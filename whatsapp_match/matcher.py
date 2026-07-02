#!/usr/bin/env python3
"""
whatsapp_match/matcher.py — Lógica de match de leads no WhatsApp Web.

Fluxo:
1. Pesquisar telefone no campo de busca
2. Abrir a conversa encontrada
3. Confirmar que o número corresponde
4. Detectar bolha de mensagem de saída
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
    encontrar_seletor,
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


async def _detectar_tela_login(page) -> bool:
    """Detecta se o WhatsApp Web esta na tela de login (QR code)."""
    try:
        from config.whatsapp_selectors import QR_CODE_SELECTORS, TIMEOUT_CURTO
        for selector in QR_CODE_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=TIMEOUT_CURTO)
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
        (encontrou, seletor_usado)
    """
    # Encontra o campo de busca
    search_selector = await encontrar_seletor(page, SEARCH_BOX_SELECTORS, TIMEOUT_CURTO)
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
        await page.wait_for_timeout(500)
        await search_box.fill(telefone)
        logger.info("Campo de busca encontrado: %s", search_selector)
        await page.wait_for_timeout(2000)  # Aguarda resultados
        return True, search_selector
    except Exception as e:
        logger.warning("Erro ao pesquisar telefone %s: %s", telefone, e)
        return False, None


async def abrir_conversa(page) -> bool:
    """
    Abre a primeira conversa da lista de resultados.

    Returns:
        True se conseguiu abrir
    """
    try:
        # Aguarda o item de chat aparecer
        item_selector = await encontrar_seletor(page, CHAT_ITEM_SELECTORS, 3000)
        if not item_selector:
            logger.debug("Nenhum chat item encontrado para a busca")
            return False

        chat_item = page.locator(item_selector).first
        if not await chat_item.is_visible():
            return False

        await chat_item.click()
        await page.wait_for_timeout(1500)

        # Aguarda carregamento da conversa
        loading_selector = await encontrar_seletor(page, LOADING_INDICATORS, TIMEOUT_CURTO)
        if loading_selector:
            try:
                await page.wait_for_selector(loading_selector, state="hidden", timeout=5000)
            except Exception:
                pass

        return True
    except Exception as e:
        logger.warning("Erro ao abrir conversa: %s", e)
        return False


async def confirmar_numero(page, telefone_canonico: str) -> tuple[bool, Optional[str]]:
    """
    Confirma que a conversa aberta pertence ao número correto.

    Tenta obter o telefone do header ou do painel de informações.

    Args:
        page: Página do Playwright
        telefone_canonico: Telefone canônico (ex: 5521999999999)

    Returns:
        (confirmado, telefone_encontrado)
    """
    # Tenta obter telefone do header
    try:
        header_selector = await encontrar_seletor(page, CONVERSATION_HEADER_SELECTORS, TIMEOUT_CURTO)
        if header_selector:
            header = page.locator(header_selector)
            await header.click()
            await page.wait_for_timeout(500)

            # Procura telefone no painel de informações
            phone_selector = await encontrar_seletor(page, PHONE_IN_PROFILE_SELECTORS, TIMEOUT_CURTO)
            if phone_selector:
                phone_el = page.locator(phone_selector).first
                phone_text = await phone_el.get_attribute("title") or await phone_el.text_content()
                if phone_text:
                    phone_text = phone_text.strip()
                    # Normaliza o telefone encontrado
                    encontrado = normalizar_telefone_br(phone_text)
                    if encontrado and encontrado == telefone_canonico:
                        return True, encontrado

            # Volta para a conversa
            back_selector = await encontrar_seletor(page, BACK_BUTTON_SELECTORS, TIMEOUT_CURTO)
            if back_selector:
                await page.locator(back_selector).first.click()
                await page.wait_for_timeout(500)
    except Exception as e:
        logger.warning("Erro ao confirmar número: %s", e)

    return False, None


async def detectar_grupo(page) -> bool:
    """
    Verifica se a conversa atual é um grupo/canal/comunidade.

    Returns:
        True se for grupo/canal/comunidade
    """
    try:
        group_selector = await encontrar_seletor(page, GROUP_INDICATORS, TIMEOUT_CURTO)
        return group_selector is not None
    except Exception:
        return False


async def detectar_mensagem_saida(page) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Detecta se existe pelo menos uma mensagem de saída na conversa.

    Returns:
        (encontrou, timestamp_mais_recente, texto_da_mensagem)
    """
    try:
        # Procura bolhas de mensagem de saída
        out_selector = await encontrar_seletor(page, MESSAGE_OUT_SELECTORS, TIMEOUT_CURTO)
        if not out_selector:
            return False, None, None

        out_messages = page.locator(out_selector)
        count = await out_messages.count()

        if count == 0:
            return False, None, None

        # Pega a última mensagem de saída
        last_msg = out_messages.nth(count - 1)
        texto = await extrair_texto_mensagem(last_msg)

        # Tenta obter timestamp (data-timestamp no elemento)
        timestamp = None
        try:
            ts = await last_msg.get_attribute("data-timestamp")
            if ts:
                dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                timestamp = dt.isoformat()
        except Exception:
            pass

        return True, timestamp, texto
    except Exception as e:
        logger.warning("Erro ao detectar mensagem de saída: %s", e)
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

    Args:
        page: Página do Playwright
        lead_id: UUID do lead
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        diagnostic_dir: Diretório para salvar diagnósticos em caso de erro

    Returns:
        MatchResult com o resultado
    """
    result = MatchResult(
        lead_id=lead_id,
        phone_normalized=phone_normalized,
        campaign_key=campaign_key,
        status=MatchStatus.ERROR,
    )

    try:
        # Gera variantes do telefone para busca
        variantes = variantes_busca_telefone(phone_normalized)

        search_found_count = 0
        for variante in variantes:
            # Pesquisa o telefone
            encontrado, search_sel = await pesquisar_telefone(page, variante)
            if encontrado == "login_required":
                result.status = MatchStatus.LOGIN_REQUIRED
                return result
            if not encontrado:
                continue

            result.selector_used = search_sel

            # Verifica se é grupo/canal/comunidade
            if await detectar_grupo(page):
                result.status = MatchStatus.GROUP
                return result

            # Abre a conversa
            if not await abrir_conversa(page):
                search_found_count += 1
                if search_found_count >= 1:
                    logger.info("Nenhum chat encontrado apos %d tentativas, parando", search_found_count)
                    break
                continue
            result.chat_found = True

            # Confirma o número
            confirmado, tel_encontrado = await confirmar_numero(page, phone_normalized)
            if not confirmado:
                result.status = MatchStatus.AMBIGUOUS_CONTACT
                result.details["phone_found"] = tel_encontrado
                return result

            # Detecta mensagem de saída
            out_found, timestamp, texto = await detectar_mensagem_saida(page)
            result.outbound_found = out_found
            result.message_timestamp = timestamp

            if not out_found:
                result.status = MatchStatus.NO_OUTBOUND
                return result

            # Extrai fingerprint e verifica campanha
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

            return result

        # Check if login was required (QR detected in first attempt)
        login_check = await _detectar_tela_login(page)
        if login_check:
            result.status = MatchStatus.LOGIN_REQUIRED
            if diagnostic_dir:
                await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}_login")
            return result

        # Nenhuma variante encontrou conversa (fallbacks esgotados / DOM quebrado)
        result.status = MatchStatus.SEARCH_FIELD_NOT_FOUND
        if diagnostic_dir:
            await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}_nochat")
        return result

    except Exception as e:
        logger.error("Erro no match do lead %s: %s", lead_id, e)
        result.status = MatchStatus.ERROR
        result.error_message = str(e)[:200]

        if diagnostic_dir:
            await capturar_diagnostico(page, diagnostic_dir, f"match_{lead_id[:8]}")

        return result
