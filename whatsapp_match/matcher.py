#!/usr/bin/env python3
"""
whatsapp_match/matcher.py — Lógica de match de leads no WhatsApp Web.

Fluxo otimizado (~30s por lead):
1. Pesquisar telefone no campo de busca
2. Abrir a conversa encontrada (espera composta, 6-10s)
3. Confirmar que o número corresponde (timeout curto, early exit, 3-6s)
4. Detectar bolha de mensagem de saída (DOM real, 1-3s)
5. Extrair texto para fingerprint
6. Verificar se corresponde à campanha

Anti-falso-positivo:
- Não considera mensagens recebidas
- Não considera conversa vazia
- Não considera grupo/canal/comunidade/status
- Não considera contato diferente com número parecido
- Contato ambíguo → não marca, registra para revisão
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from config.whatsapp_selectors import (
    SEARCH_BOX_SELECTORS,
    CHAT_ITEM_SELECTORS,
    CONVERSATION_HEADER_SELECTORS,
    INFO_PANEL_SELECTORS,
    PHONE_IN_PROFILE_SELECTORS,
    MESSAGE_OUT_SELECTORS,
    MESSAGE_TEXT_SELECTORS,
    BACK_BUTTON_SELECTORS,
    LOADING_INDICATORS,
    GROUP_INDICATORS,
    TIMEOUT_PADRAO,
    TIMEOUT_CURTO,
    TIMEOUT_RAPIDO,
    encontrar_seletor,
    encontrar_seletor_rapido,
    capturar_diagnostico,
)
from utils.phone_utils import normalizar_telefone_br, variantes_busca_telefone
from utils.campaign_fingerprint import fingerprint_mensagem, corresponde_campanha

logger = logging.getLogger(__name__)


class MatchStatus(Enum):
    """Status do match de um lead no WhatsApp."""
    MATCHED = "matched"               # Mensagem de saída encontrada e corresponde à campanha
    AMBIGUOUS = "ambiguous"           # Mensagem de saída encontrada mas não corresponde à campanha
    NO_OUTBOUND = "no_outbound"       # Conversa existe mas sem mensagem de saída
    NO_CHAT = "no_chat"               # Nenhuma conversa encontrada para o telefone
    GROUP = "group"                   # É um grupo, não marcar
    CHANNEL = "channel"               # É um canal, não marcar
    COMMUNITY = "community"           # É uma comunidade, não marcar
    STATUS = "status"                 # É status, não marcar
    AMBIGUOUS_CONTACT = "ambiguous_contact"  # Contato salvo por nome, número não confirmável
    ERROR = "error"                   # Erro durante a pesquisa
    SEARCH_FIELD_NOT_FOUND = "search_field_not_found"  # Campo de busca nao encontrado
    LOGIN_REQUIRED = "login_required"  # WhatsApp Web nao autenticado (QR code)


@dataclass
class MatchResult:
    """Resultado do match de um lead."""
    lead_id: str
    phone_normalized: str
    campaign_key: str
    status: MatchStatus
    message_timestamp: Optional[str] = None
    message_fingerprint: Optional[str] = None
    campaign_match: Optional[bool] = None
    chat_found: bool = False
    outbound_found: bool = False
    selector_used: Optional[str] = None
    error_message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    # Instrumentação de tempos
    timings: dict[str, float] = field(default_factory=dict)


async def _detectar_tela_login(page) -> bool:
    """Detecta se o WhatsApp Web esta na tela de login (QR code)."""
    try:
        from config.whatsapp_selectors import QR_CODE_SELECTORS
        for selector in QR_CODE_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=TIMEOUT_RAPIDO)
                if el:
                    return True
            except Exception:
                continue
        body = await page.inner_text("body", timeout=3000)
        body_lower = body.lower()[:500]
        for kw in ["escaneie", "conectar", "use o whatsapp", "scan the qr", "qr code"]:
            if kw in body_lower:
                return True
    except Exception:
        pass
    return False


async def pesquisar_telefone(page, telefone: str) -> tuple[bool, Optional[str]]:
    """
    Pesquisa um telefone no campo de busca do WhatsApp Web.

    Args:
        page: Página do Playwright
        telefone: Telefone canônico ou variante

    Returns:
        (encontrou, seletor_usado) — encontrou pode ser True, False, ou "login_required"
    """
    t0 = time.time()

    # Encontra o campo de busca (usando count() primeiro, rápido)
    search_selector = await encontrar_seletor_rapido(page, SEARCH_BOX_SELECTORS, TIMEOUT_CURTO)
    if not search_selector:
        if await _detectar_tela_login(page):
            logger.warning("WhatsApp Web nao autenticado (QR code visivel)")
            return "login_required", None
        logger.warning("Campo de busca não encontrado")
        return False, None

    try:
        search_box = page.locator(search_selector)
        await search_box.click()
        await search_box.fill("")
        await page.wait_for_timeout(200)  # reduzido de 300ms
        await search_box.fill(telefone)
        logger.info("Campo de busca encontrado: %s (%.2fs)", search_selector, time.time() - t0)
        await page.wait_for_timeout(800)  # reduzido de 1000ms
        return True, search_selector
    except Exception as e:
        logger.warning("Erro ao pesquisar telefone %s: %s", telefone, e)
        return False, None


async def abrir_conversa(page) -> bool:
    """
    Abre a primeira conversa da lista de resultados.

    Usa espera composta: aguarda até que o header da conversa OU
    painel de mensagens esteja visível, com orçamento total de ~8s.

    Returns:
        True se conseguiu abrir
    """
    t0 = time.time()
    try:
        # Aguarda o item de chat aparecer (timeout curto)
        item_selector = await encontrar_seletor_rapido(page, CHAT_ITEM_SELECTORS, 2000)
        if not item_selector:
            logger.debug("Nenhum chat item encontrado para a busca")
            return False

        chat_item = page.locator(item_selector).first
        if not await chat_item.is_visible():
            return False

        await chat_item.click()

        # Espera composta: header OU painel de mensagens OU erro
        # Orçamento total: 8s
        import asyncio
        header_ready = False
        messages_ready = False

        try:
            # Race: o que aparecer primeiro
            async def wait_header():
                nonlocal header_ready
                try:
                    sel = await encontrar_seletor(page, CONVERSATION_HEADER_SELECTORS, 3000)
                    if sel:
                        header_ready = True
                except Exception:
                    pass

            async def wait_messages():
                nonlocal messages_ready
                try:
                    # Painel de mensagens visível
                    await page.wait_for_selector(
                        'div[data-testid="conversation-panel-messages"]',
                        timeout=5000
                    )
                    messages_ready = True
                except Exception:
                    pass

            async def wait_loading_gone():
                try:
                    loading_sel = await encontrar_seletor_rapido(page, LOADING_INDICATORS, 500)
                    if loading_sel:
                        await page.wait_for_selector(loading_sel, state="hidden", timeout=5000)
                except Exception:
                    pass

            # Dispara as 3 esperas em paralelo
            await asyncio.wait_for(
                asyncio.gather(wait_header(), wait_messages(), wait_loading_gone()),
                timeout=8.0
            )
        except asyncio.TimeoutError:
            pass  # Timeout global — continua com o que tiver

        elapsed = time.time() - t0
        logger.debug("Abertura da conversa: %.2fs (header=%s, messages=%s)",
                     elapsed, header_ready, messages_ready)

        # Se pelo menos um indicador apareceu, considera sucesso
        return header_ready or messages_ready

    except Exception as e:
        logger.warning("Erro ao abrir conversa: %s (%.2fs)", e, time.time() - t0)
        return False


async def confirmar_numero(page, telefone_canonico: str) -> tuple[bool, Optional[str]]:
    """
    Confirma que a conversa aberta pertence ao número correto.

    Estratégia otimizada:
    1. Consulta todos os seletores de header com timeout curto
    2. Abre painel de info só se necessário
    3. Para imediatamente quando confirmar
    4. Orçamento total: 3-6s

    Args:
        page: Página do Playwright
        telefone_canonico: Telefone canônico (ex: 5521999999999)

    Returns:
        (confirmado, telefone_encontrado)
    """
    t0 = time.time()

    # Tenta obter telefone do header (rápido, sem abrir painel)
    try:
        header_selector = await encontrar_seletor_rapido(page, CONVERSATION_HEADER_SELECTORS, 1000)
        if header_selector:
            header = page.locator(header_selector)
            await header.click()
            await page.wait_for_timeout(200)

            # Procura telefone no painel de informações
            phone_selector = await encontrar_seletor_rapido(page, PHONE_IN_PROFILE_SELECTORS, 2000)
            if phone_selector:
                phone_el = page.locator(phone_selector).first
                phone_text = await phone_el.get_attribute("title") or await phone_el.text_content()
                if phone_text:
                    phone_text = phone_text.strip()
                    encontrado = normalizar_telefone_br(phone_text)
                    if encontrado and encontrado == telefone_canonico:
                        elapsed = time.time() - t0
                        logger.debug("Número confirmado: %s (%.2fs)", telefone_canonico, elapsed)
                        return True, encontrado

            # Volta para a conversa
            back_selector = await encontrar_seletor_rapido(page, BACK_BUTTON_SELECTORS, 1000)
            if back_selector:
                await page.locator(back_selector).first.click()
                await page.wait_for_timeout(200)
    except Exception as e:
        logger.warning("Erro ao confirmar número: %s (%.2fs)", e, time.time() - t0)

    return False, None


async def detectar_grupo(page) -> Optional[str]:
    """
    Verifica se a conversa atual é um grupo/canal/comunidade.

    Otimizado: usa count() imediato em todos os seletores, sem esperar 5s cada.

    Returns:
        Tipo detectado ("group", "channel", "community") ou None
    """
    t0 = time.time()
    try:
        # Testa todos os indicadores com count() — instantâneo
        for selector in GROUP_INDICATORS:
            try:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    elapsed = time.time() - t0
                    logger.debug("Grupo/canal detectado: %s (%.2fs)", selector, elapsed)
                    # Classifica o tipo
                    if "community" in selector.lower():
                        return "community"
                    elif "channel" in selector.lower():
                        return "channel"
                    else:
                        return "group"
            except Exception:
                continue
    except Exception:
        pass

    elapsed = time.time() - t0
    logger.debug("Nenhum indicador de grupo encontrado (%.2fs)", elapsed)
    return None


async def detectar_mensagem_saida(page) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Detecta se existe pelo menos uma mensagem de saída na conversa.

    WhatsApp Web atual (2026): usa pseudo-elemento CSS ::before que insere
    "tail-out" (enviada) ou "tail-in" (recebida) no textContent do msg-container.
    Filtramos por textContent que começa com "tail-out".

    Returns:
        (encontrou, timestamp_mais_recente, texto_da_mensagem)
    """
    t0 = time.time()
    try:
        # Pega todos os msg-containers e filtra por tail-out
        locator = page.locator('div[data-testid="msg-container"]')
        count = await locator.count()
        if count == 0:
            return False, None, None

        # Itera de tras pra frente (mais recentes primeiro)
        for i in range(count - 1, -1, -1):
            try:
                msg = locator.nth(i)
                texto = await msg.text_content()
                if texto and texto.startswith("tail-out"):
                    # Remove o prefixo "tail-out" do texto
                    texto_limpo = texto[8:]  # remove "tail-out"
                    timestamp = None
                    try:
                        ts = await msg.get_attribute("data-timestamp")
                        if ts:
                            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                            timestamp = dt.isoformat()
                    except Exception:
                        pass
                    elapsed = time.time() - t0
                    logger.debug("Outbound detectado via tail-out: msg %d/%d (%.2fs)",
                                i, count, elapsed)
                    return True, timestamp, texto_limpo
            except Exception:
                continue

        # Fallback JS
        try:
            has_outbound = await page.evaluate("""() => {
                const msgs = document.querySelectorAll('div[data-testid="msg-container"]');
                for (const msg of msgs) {
                    if (msg.textContent && msg.textContent.startsWith('tail-out')) {
                        return 1;
                    }
                }
                return 0;
            }""")
            if has_outbound and has_outbound > 0:
                logger.debug("Outbound detectado via JS fallback")
                return True, None, None
        except Exception:
            pass

    except Exception as e:
        logger.warning("Erro ao detectar mensagem de saída: %s (%.2fs)", e, time.time() - t0)

    return False, None, None


async def extrair_texto_mensagem(element) -> Optional[str]:
    """
    Extrai o texto de uma bolha de mensagem.

    Args:
        element: Elemento Playwright da bolha

    Returns:
        Texto da mensagem ou None
    """
    try:
        # Tenta seletores de texto
        for selector in MESSAGE_TEXT_SELECTORS:
            try:
                text_el = element.locator(selector).first
                if await text_el.is_visible():
                    return await text_el.text_content()
            except Exception:
                continue

        # Fallback: texto direto do elemento
        return await element.text_content()
    except Exception:
        return None


async def fazer_match_completo(
    page,
    lead_id: str,
    phone_normalized: str,
    campaign_key: str,
    diagnostic_dir: Optional[str] = None,
) -> MatchResult:
    """
    Executa o fluxo completo de match para um lead.

    Otimizações:
    - Timeouts reduzidos (1s em vez de 5s)
    - count() imediato em vez de wait_for_selector
    - Espera composta na abertura da conversa
    - Early exit em todas as etapas
    - Orçamento global ~35s

    Args:
        page: Página do Playwright
        lead_id: UUID do lead
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        diagnostic_dir: Diretório para salvar diagnósticos em caso de erro

    Returns:
        MatchResult com o resultado
    """
    t_total_start = time.time()
    timings = {}

    result = MatchResult(
        lead_id=lead_id,
        phone_normalized=phone_normalized,
        campaign_key=campaign_key,
        status=MatchStatus.ERROR,
    )

    try:
        # Gera variantes do telefone para busca
        variantes = variantes_busca_telefone(phone_normalized)

        search_field_was_found = False
        variants_tried = 0

        for variante in variantes:
            variant_start = time.time()

            # ETAPA 1: Pesquisar telefone
            t1 = time.time()
            encontrado, search_sel = await pesquisar_telefone(page, variante)
            timings["search"] = time.time() - t1

            if encontrado == "login_required":
                result.status = MatchStatus.LOGIN_REQUIRED
                result.timings = timings
                return result
            if not encontrado:
                variants_tried += 1
                continue

            # Campo de busca encontrado
            search_field_was_found = True
            result.selector_used = search_sel
            variant_elapsed = time.time() - variant_start
            logger.debug("Variante %d: %.2fs, found=True", variants_tried, variant_elapsed)
            variants_tried += 1

            # ETAPA 2: Detectar grupo/canal (rápido, count() imediato)
            t1 = time.time()
            grupo_tipo = await detectar_grupo(page)
            timings["group_detect"] = time.time() - t1
            if grupo_tipo:
                if grupo_tipo == "community":
                    result.status = MatchStatus.COMMUNITY
                elif grupo_tipo == "channel":
                    result.status = MatchStatus.CHANNEL
                else:
                    result.status = MatchStatus.GROUP
                result.timings = timings
                return result

            # ETAPA 3: Abrir conversa (espera composta)
            t1 = time.time()
            if not await abrir_conversa(page):
                timings["open_chat"] = time.time() - t1
                continue  # Nenhum chat encontrado — tenta próxima variante
            timings["open_chat"] = time.time() - t1
            result.chat_found = True

            # ETAPA 4: Confirmar número (timeout curto, early exit)
            t1 = time.time()
            confirmado, tel_encontrado = await confirmar_numero(page, phone_normalized)
            timings["confirm_phone"] = time.time() - t1
            if not confirmado:
                result.status = MatchStatus.AMBIGUOUS_CONTACT
                result.details["phone_found"] = tel_encontrado
                result.timings = timings
                return result

            # ETAPA 5: Detectar mensagem de saída (count() imediato)
            t1 = time.time()
            out_found, timestamp, texto = await detectar_mensagem_saida(page)
            timings["outbound_detect"] = time.time() - t1
            result.outbound_found = out_found
            result.message_timestamp = timestamp

            if not out_found:
                result.status = MatchStatus.NO_OUTBOUND
                result.timings = timings
                return result

            # ETAPA 6: Fingerprint e campanha
            t1 = time.time()
            if texto:
                fp = fingerprint_mensagem(texto)
                result.message_fingerprint = fp
                match = corresponde_campanha(texto, campaign_key)
                result.campaign_match = match

                if match:
                    result.status = MatchStatus.MATCHED
                else:
                    result.status = MatchStatus.AMBIGUOUS
            else:
                result.status = MatchStatus.AMBIGUOUS
            timings["fingerprint"] = time.time() - t1

            timings["total"] = time.time() - t_total_start
            result.timings = timings
            return result

        # Após esgotar todas as variantes
        # Verifica se era tela de login
        login_check = await _detectar_tela_login(page)
        if login_check:
            result.status = MatchStatus.LOGIN_REQUIRED
            if diagnostic_dir:
                await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}_login")
            result.timings = timings
            return result

        # Classificação correta após esgotar variantes
        if search_field_was_found:
            result.status = MatchStatus.NO_CHAT
            logger.info("Busca executada, %d variantes testadas, nenhuma conversa encontrada", variants_tried)
        else:
            result.status = MatchStatus.SEARCH_FIELD_NOT_FOUND
            logger.warning("Campo de busca nao encontrado em %d variantes", variants_tried)
            if diagnostic_dir:
                await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}_nosearch")

        timings["total"] = time.time() - t_total_start
        result.timings = timings
        return result

    except Exception as e:
        logger.error("Erro no match do lead %s: %s", lead_id, e)
        result.status = MatchStatus.ERROR
        result.error_message = str(e)[:200]

        if diagnostic_dir:
            await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}")

        timings["total"] = time.time() - t_total_start
        result.timings = timings
        return result