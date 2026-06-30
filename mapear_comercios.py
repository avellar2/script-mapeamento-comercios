"""
Mapeador de Comércios - Google Maps
===================================
Busca comércios no Google Maps que NÃO possuem site,
gerando uma planilha de leads para prospecção.

Uso: python mapear_comercios.py [--regiao baixada|rio_premium|todas]
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import random
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from config.regioes import resolve_regiao, get_output_dir, get_locais_busca, BAIXADA
from config.avgestao import (
    resolver_grupo,
    consultar_subnichos,
    gerar_consultas_meta,
    deduplicar_leads,
    enriquecer_lead_avgestao,
    GRUPOS,
    get_grupo,
    COLUNAS_XLSX_AVGESTAO_GEO,
)
from config import territorios as T
from config.territorios import UF_NOMES
from config import dedup as DEDUP
from config import fila as FILA
from config import runs as RUNS
from config import limites as LIMITES
DELAY_MIN = 2.0
DELAY_MAX = 5.0

# ══════════════════════════════════════════════════════════════════
# Logger persistente e diagnóstico de saúde do navegador
# ══════════════════════════════════════════════════════════════════

# Timeout de navegação (ms) — aumentado de 45s para 90s para evitar
# interrupções do run em conexões lentas.
_TIMEOUT_NAVEGACAO_MS = 90000

# Timeout de ações/seletores (ms) — separado, não usa 90s para tudo.
_TIMEOUT_SELETOR_MS = 30000


def _logger_captura(run_id: str) -> logging.Logger:
    """Retorna logger com handler para arquivo dentro do diretório do run."""
    logger = logging.getLogger(f"captura.{run_id}")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    pasta = RUNS.pasta_run(run_id)
    pasta.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(pasta / "captura_stdout.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                             datefmt="%Y-%m-%dT%H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


def _avaliar_saude_pagina(browser, context, page) -> str:
    """Avalia a saúde do browser/context/page e retorna classificação.

    Retorna um dos valores:
      - "page_valida": tudo OK, página viva e browser conectado
      - "page_fechada": browser e context vivos, mas page fechada
      - "browser_morto": browser desconectado
      - "context_morto": context fechado/inutilizável
      - "sem_browser": browser/context não informados (caminho de teste)
    """
    # Browser não informado (testes unitários com mock) — pular verificação
    if browser is None and context is None:
        return "sem_browser"
    # 1. Browser
    if browser is None or not browser.is_connected():
        return "browser_morto"
    # 2. Context
    if context is None:
        return "context_morto"
    try:
        _ = context.pages  # acesso que lança se context fechado
    except Exception:
        return "context_morto"
    # 3. Page
    if page is None or page.is_closed():
        return "page_fechada"
    return "page_valida"


# ── Progress / Resume ──────────────────────────────────────────────

def load_nomes_existentes(output_dir):
    """Carrega nomes+cidade do CSV existente para evitar duplicatas."""
    existing_csv = output_dir / "todos_comercios.csv"
    existentes = set()
    if existing_csv.exists():
        with open(existing_csv, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                nome = row.get("nome", "").strip().lower()
                cidade = row.get("cidade", "").strip().lower()
                if nome and cidade:
                    existentes.add(f"{nome}|{cidade}")
    return existentes

def load_progress(output_dir):
    progress_file = output_dir / "progresso.json"
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categorias_prontas": [], "categorias_em_andamento": {}, "comercios": []}


def save_progress(progress, output_dir):
    progress_file = output_dir / "progresso.json"
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ── Export ──────────────────────────────────────────────────────────

def export_csv(businesses, filename, output_dir):
    filepath = output_dir / filename
    fieldnames = [
        "nome", "endereco", "telefone", "whatsapp", "instagram",
        "email", "categoria", "tem_site", "url_site",
        "avaliacao", "num_avaliacoes", "cidade", "bairro", "link_maps",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(businesses)
    return filepath


def export_excel(businesses, filename, output_dir):
    """Exporta para .xlsx (requer openpyxl)."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "Leads sem Site"

        headers = [
            "Nome", "Endereço", "Telefone", "WhatsApp", "Instagram",
            "Email", "Categoria", "Tem Site?", "URL do Site",
            "Avaliação", "Nº Avaliações", "Cidade", "Bairro", "Link Maps",
        ]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="2563EB")
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for row_idx, b in enumerate(businesses, 2):
            ws.cell(row=row_idx, column=1, value=b["nome"])
            ws.cell(row=row_idx, column=2, value=b["endereco"])
            ws.cell(row=row_idx, column=3, value=b["telefone"])
            ws.cell(row=row_idx, column=4, value=b.get("whatsapp", ""))
            ws.cell(row=row_idx, column=5, value=b.get("instagram", ""))
            ws.cell(row=row_idx, column=6, value=b.get("email", ""))
            ws.cell(row=row_idx, column=7, value=b["categoria"])
            ws.cell(row=row_idx, column=8, value="Sim" if b["tem_site"] else "NÃO")
            ws.cell(row=row_idx, column=9, value=b["url_site"])
            ws.cell(row=row_idx, column=10, value=b["avaliacao"])
            ws.cell(row=row_idx, column=11, value=b["num_avaliacoes"])
            ws.cell(row=row_idx, column=12, value=b.get("cidade", ""))
            ws.cell(row=row_idx, column=13, value=b.get("bairro", ""))
            ws.cell(row=row_idx, column=14, value=b.get("link_maps", ""))

            # Destaca leads sem site em amarelo
            if not b["tem_site"]:
                highlight = PatternFill("solid", fgColor="FEF08A")
                for col in range(1, 15):
                    ws.cell(row=row_idx, column=col).fill = highlight

        # Ajusta largura das colunas
        widths = [35, 45, 18, 18, 30, 30, 25, 10, 35, 10, 12, 20, 22, 45]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

        filepath = output_dir / filename
        wb.save(filepath)
        return filepath
    except ImportError:
        print("  [!] openpyxl não instalado — exportando CSV apenas")
        return None


def export_csv_avgestao(businesses, filename, output_dir):
    """Exporta comércios do modo AVGESTAO para CSV (inclui place_id e subnicho)."""
    filepath = output_dir / filename
    fieldnames = [
        "nome", "endereco", "telefone", "whatsapp", "instagram",
        "email", "categoria", "subnicho", "tem_site", "url_site",
        "avaliacao", "num_avaliacoes", "cidade", "bairro", "link_maps",
        "place_id",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(businesses)
    return filepath


def export_excel_avgestao_raw(businesses, filename, output_dir):
    """Exporta comércios do modo AVGESTAO para XLSX bruto (com place_id e subnicho)."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "Comércios AVGESTÃO"

        headers = [
            "Nome", "Endereço", "Telefone", "WhatsApp", "Instagram",
            "Email", "Categoria", "Subnicho", "Tem Site?", "URL do Site",
            "Avaliação", "Nº Avaliações", "Cidade", "Bairro", "Link Maps",
            "Place ID",
        ]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="7C3AED")
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        campos = [
            "nome", "endereco", "telefone", "whatsapp", "instagram",
            "email", "categoria", "subnicho", "tem_site", "url_site",
            "avaliacao", "num_avaliacoes", "cidade", "bairro", "link_maps",
            "place_id",
        ]
        for row_idx, b in enumerate(businesses, 2):
            for col_idx, campo in enumerate(campos, 1):
                valor = b.get(campo, "")
                if campo == "tem_site":
                    valor = "Sim" if valor else "NÃO"
                ws.cell(row=row_idx, column=col_idx, value=valor)

        widths = [35, 45, 18, 18, 30, 30, 25, 26, 10, 35, 10, 12, 20, 22, 45, 30]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

        filepath = output_dir / filename
        wb.save(filepath)
        return filepath
    except ImportError:
        print("  [!] openpyxl não instalado — exportando CSV apenas")
        return None


# ── Google Maps Scraper ────────────────────────────────────────────

async def aceitar_cookies(page):
    """Clica no botão de aceitar cookies do Google, se aparecer."""
    for selector in [
        'button[aria-label*="Aceitar"]',
        'button[aria-label*="Accept"]',
        'button[aria-label*="accept all"]',
        'form:nth-of-type(2) button',
    ]:
        btn = page.locator(selector).first
        if await btn.count() > 0:
            try:
                await btn.click(timeout=2000)
                await asyncio.sleep(1)
                return True
            except Exception:
                pass
    return False


async def scroll_panel(page, max_scrolls=25):
    """Rola o painel de resultados para carregar mais comércios."""
    panel = page.locator('div[role="feed"]').first
    if await panel.count() == 0:
        return
    for _ in range(max_scrolls):
        await panel.evaluate("el => el.scrollBy(0, 800)")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        fim = page.locator(
            'span:has-text("fim da lista"), span:has-text("end of the list")'
        )
        if await fim.count() > 0:
            break


async def extrair_detalhes(page, categoria, cidade="", subnicho=""):
    """Extrai dados de um comércio na página de detalhes aberta."""
    await page.wait_for_timeout(1500)

    dados = {
        "nome": "",
        "endereco": "",
        "telefone": "",
        "whatsapp": "",
        "instagram": "",
        "email": "",
        "categoria": categoria,
        "tem_site": False,
        "url_site": "",
        "avaliacao": "",
        "num_avaliacoes": "",
        "cidade": cidade,
        "bairro": "",
        "link_maps": "",
        "place_id": "",
        "subnicho": subnicho,
    }

    # Nome - mais seletivo para evitar pegar elementos errados
    for sel in ['h1.DUwDvf', 'h1[class*="fontHeadline"]', 'h1[class*="fontTitle"]']:
        el = page.locator(sel).first
        if await el.count() > 0:
            txt = (await el.inner_text()).strip()
            if txt and len(txt) > 3:  # Nome deve ter mais de 3 caracteres
                dados["nome"] = txt
                break

    # Validação: ignora nomes inválidos
    if not dados["nome"] or len(dados["nome"]) < 5:
        return None

    # Ignora entradas com nomes genéricos/inválidos
    nomes_invalidos = ["resultados", "todos", "categorias", "ver mais", "mostrar mais",
                       "próximo", "anterior", "fechar", "voltar", "menu", "pesquisa"]
    if dados["nome"].lower() in nomes_invalidos:
        return None

    # Avaliação
    rating_el = page.locator('div[role="img"][aria-label*="estrela"], div[role="img"][aria-label*="star"]').first
    if await rating_el.count() > 0:
        label = await rating_el.get_attribute("aria-label") or ""
        m = re.search(r"([\d,.]+)", label)
        if m:
            dados["avaliacao"] = m.group(1).replace(",", ".")

    # Nº avaliações
    reviews_el = page.locator('button[aria-label*="avaliação"], button[aria-label*="review"]').first
    if await reviews_el.count() > 0:
        txt = await reviews_el.inner_text()
        dados["num_avaliacoes"] = re.sub(r"\D", "", txt)

    # Endereço
    addr_el = page.locator(
        'button[data-item-id*="address"], button[aria-label*="Endereço"], '
        'button[aria-label*="Address"]'
    ).first
    if await addr_el.count() > 0:
        dados["endereco"] = (await addr_el.inner_text()).strip()
        # Remove caracteres especiais do início
        dados["endereco"] = re.sub(r'^[\W\u200b-\u200d]+', '', dados["endereco"])

    # Telefone
    phone_el = page.locator(
        'button[data-item-id*="phone:tel"], button[aria-label*="Telefone"], '
        'button[aria-label*="Phone"]'
    ).first
    if await phone_el.count() > 0:
        dados["telefone"] = (await phone_el.inner_text()).strip()
        # Remove caracteres especiais do início
        dados["telefone"] = re.sub(r'^[\W\u200b-\u200d]+', '', dados["telefone"])

    # Website
    web_el = page.locator(
        'a[data-item-id*="authority"], a[aria-label*="Site"], '
        'a[aria-label*="Website"], a[aria-label*="site oficial"]'
    ).first
    if await web_el.count() > 0:
        dados["tem_site"] = True
        dados["url_site"] = (await web_el.get_attribute("href")) or ""

    # WhatsApp
    whatsapp_el = page.locator(
        'a[href*="wa.me"], a[href*="whatsapp"], '
        'a[data-item-id*="whatsapp"], button[aria-label*="WhatsApp"], '
        'a[aria-label*="WhatsApp"]'
    ).first
    if await whatsapp_el.count() > 0:
        href = await whatsapp_el.get_attribute("href") or ""
        if "wa.me" in href:
            # Extrai o número do link wa.me
            wa_match = re.search(r"wa\.me/(\d+)", href)
            if wa_match:
                dados["whatsapp"] = wa_match.group(1)
        elif "whatsapp" in href.lower():
            dados["whatsapp"] = href
        else:
            dados["whatsapp"] = (await whatsapp_el.inner_text()).strip()

    # Se não achou WhatsApp dedicado, verifica se o telefone é celular (9° dígito)
    if not dados["whatsapp"] and dados["telefone"]:
        tel_limpo = re.sub(r"\D", "", dados["telefone"])
        # Celulares no Brasil têm 11 dígitos (DDD + 9 + 8 dígitos)
        if len(tel_limpo) == 11 or (len(tel_limpo) == 13 and tel_limpo.startswith("55")):
            dados["whatsapp"] = dados["telefone"]

    # Instagram
    insta_el = page.locator(
        'a[href*="instagram.com"], a[aria-label*="Instagram"]'
    ).first
    if await insta_el.count() > 0:
        insta_href = await insta_el.get_attribute("href") or ""
        if "instagram.com" in insta_href:
            # Limpa URL do Instagram
            insta_href = insta_href.rstrip("/")
            dados["instagram"] = insta_href
        else:
            dados["instagram"] = (await insta_el.inner_text()).strip()

    # Se o site for Instagram, captura como Instagram também
    if dados["url_site"] and "instagram.com" in dados["url_site"].lower():
        if not dados["instagram"]:
            dados["instagram"] = dados["url_site"].rstrip("/")
        dados["tem_site"] = False  # Instagram não é site próprio

    # Link do Google Maps (captura URL atual da página de detalhe)
    try:
        current_url = page.url
        if "/maps/" in current_url or "google" in current_url:
            dados["link_maps"] = current_url
            # Place ID: extrai do URL quando disponivel (CID ou ChIJ)
            m_pid = re.search(r"(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+|ChIJ[A-Za-z0-9_-]+)", current_url)
            if m_pid:
                dados["place_id"] = m_pid.group(1)
    except Exception:
        pass

    # Bairro - extrair do endereço
    if dados["endereco"]:
        end = dados["endereco"]
        partes = end.split(" - ")
        if len(partes) >= 3:
            dados["bairro"] = partes[-2].strip().split(",")[0].strip()
        elif len(partes) == 2:
            bairro_cidade = partes[-1].strip()
            # Tenta separar bairro de cidade
            bc_parts = bairro_cidade.split(",")
            if len(bc_parts) >= 2:
                dados["bairro"] = bc_parts[0].strip()

    # Email - Tenta encontrar em vários locais
    email_selectors = [
        'a[href^="mailto:"]',
        'button[data-item-id*="email"]',
        'div[aria-label*="Email"]',
        'span:has-text("@")',
    ]

    for sel in email_selectors:
        email_el = page.locator(sel).first
        if await email_el.count() > 0:
            try:
                # Se for um link mailto:
                href = await email_el.get_attribute("href")
                if href and href.startswith("mailto:"):
                    dados["email"] = href.replace("mailto:", "").strip().split('?')[0]
                    break

                # Se for texto, tenta extrair email
                text = await email_el.inner_text()
                email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
                if email_match:
                    dados["email"] = email_match.group(0)
                    break
            except Exception:
                pass

    return dados


# ══════════════════════════════════════════════════════════════════
# Robustez de buscar_categoria (etapa 8) — helpers testaveis
# ══════════════════════════════════════════════════════════════════

class CaptchaDetectado(Exception):
    """Levantada quando o Google Maps apresenta CAPTCHA/bloqueio e
    captcha_detector=True. Nao tenta resolver nem contornar."""


class NavegadorFechado(Exception):
    """Browser ou contexto do Playwright foi fechado inesperadamente."""


# Padroes especificos de erro de navegador/context/page fechado (lowercase).
# Usados por _eh_erro_navegador_fechado para distinguir falhas fatais de
# erros recuperaveis (timeout, execution context destroyed, etc.).
PADROES_NAVEGADOR_FECHADO = (
    "target page, context or browser has been closed",
    "browser has been closed",
    "browser closed",
    "context has been closed",
    "context closed",
    "page has been closed",
    "page closed",
)


def _eh_erro_navegador_fechado(erro: str) -> bool:
    """Retorna True se a mensagem de erro corresponde a navegador/context/page fechado.

    Usa apenas padroes especificos (lowercase) para evitar falsos positivos
    com erros de navegacao como timeout ou execution context destroyed.
    """
    erro_lower = str(erro).lower()
    return any(p in erro_lower for p in PADROES_NAVEGADOR_FECHADO)


async def _garantir_pagina_ativa(browser, context, page):
    """Verifica saude do browser/context/page e retorna (page_valida, foi_recriada).

    - Se browser estiver desconectado: levanta NavegadorFechado.
    - Se context estiver indisponivel: levanta NavegadorFechado.
    - Se somente a page estiver fechada: tenta recriar uma unica vez.
    - Se a recriacao falhar: levanta NavegadorFechado.

    O chamador DEVE atualizar a referencia da page com o primeiro elemento
    da tupla retornada.
    """
    if browser is None or not browser.is_connected():
        raise NavegadorFechado("browser desconectado")

    if context is None:
        raise NavegadorFechado("contexto indisponivel")

    try:
        context.pages
    except Exception as exc:
        raise NavegadorFechado("contexto fechado") from exc

    if page is not None and not page.is_closed():
        return page, False

    # Page fechada — tenta recriar uma unica vez
    try:
        nova_page = await context.new_page()
        return nova_page, True
    except Exception as exc:
        raise NavegadorFechado(
            "page fechada e nao foi possivel recriar"
        ) from exc


# Delay principal por item usado quando delay_min/delay_max nao sao informados.
# Reproduz o comportamento atual (random.uniform(1.8, 3.5) no loop de itens).
_DELAY_ITEM_DEFAULT = (1.8, 3.5)


def validar_delays(delay_min, delay_max):
    """Valida/normaliza os delays por item.

    Retorna (delay_min, delay_max). Defaults (None, None) reproduzem o
    comportamento atual (1.8, 3.5). ValueError se delay_min > delay_max
    (com ambos informados) ou se algum for negativo.
    """
    if delay_min is None and delay_max is None:
        return _DELAY_ITEM_DEFAULT
    dmin = _DELAY_ITEM_DEFAULT[0] if delay_min is None else float(delay_min)
    dmax = _DELAY_ITEM_DEFAULT[1] if delay_max is None else float(delay_max)
    if dmin < 0 or dmax < 0:
        raise ValueError("delay_min/delay_max nao podem ser negativos")
    if dmin > dmax:
        raise ValueError(
            f"delay_min ({dmin}) nao pode ser maior que delay_max ({dmax})"
        )
    return dmin, dmax


async def detectar_captcha(page) -> bool:
    """Detecta bloqueio/CAPTCHA do Google. Nao tenta resolver.

    Verifica URL de bloqueio (sorry / accounts.google.com) e seletor de
    CAPTCHA. Tolerante a erros de leitura da pagina (retorna False).
    """
    try:
        url = page.url or ""
    except Exception:
        url = ""
    if "sorry" in url or "accounts.google.com" in url:
        return True
    try:
        if await page.locator("#captcha").count() > 0:
            return True
    except Exception:
        pass
    return False


async def salvar_screenshot(page, screenshot_dir, nome: str):
    """Salva screenshot em screenshot_dir se configurado. Robusto a falhas."""
    if not screenshot_dir:
        return None
    try:
        d = Path(screenshot_dir)
        d.mkdir(parents=True, exist_ok=True)
        caminho = d / f"{nome}.png"
        await page.screenshot(path=str(caminho))
        return caminho
    except Exception:
        return None


def _alcance_tentativas(max_tentativas) -> int:
    """Quantas tentativas de clique fazer por item (>=1). Default 3.

    None/0/negativo -> 3 (preserva comportamento atual).
    """
    if max_tentativas is None:
        return 3
    try:
        n = int(max_tentativas)
    except (TypeError, ValueError):
        return 3
    return n if n >= 1 else 3


def _deve_interromper_por_captcha(captcha_detector: bool, captcha_detectado: bool) -> bool:
    """CAPTCHA so interrompe se o detector estiver habilitado E houver deteccao.

    captcha_detector=False nunca interrompe (mesmo com bloqueio presente).
    """
    return bool(captcha_detector) and bool(captcha_detectado)


async def buscar_categoria(page, categoria, cidade, start_index=0, progress=None, nomes_existentes=None, max_results=20, output_dir=None, subnicho="", query_term=None, delay_min=None, delay_max=None, max_tentativas=3, screenshot_dir=None, captcha_detector=False, _run_id=None, _browser=None, _context=None):
    """Busca uma categoria no Google Maps e retorna lista de comércios.

    Novos kwargs (defaults preservam o comportamento atual):
        delay_min/delay_max — delay por item (default 1.8-3.5, como antes).
        max_tentativas       — tentativas de clique por item (default 3).
        screenshot_dir       — se informado, salva screenshot em falhas.
        captcha_detector     — se True, levanta CaptchaDetectado ao detectar
                               bloqueio (default False = nao interrompe).
        _run_id              — para logging persistente (injetado pelo orquestrador).
        _browser             — para verificação de saúde (injetado pelo orquestrador).
        _context             — para verificação de saúde (injetado pelo orquestrador).
    O contrato de retorno e extrair_detalhes nao mudam.
    """
    # Validar delays por item (default reproduz 1.8-3.5; ValueError se min > max).
    dmin_item, dmax_item = validar_delays(delay_min, delay_max)
    n_tent = _alcance_tentativas(max_tentativas)

    log = _logger_captura(_run_id) if _run_id else None

    termo_busca = query_term or categoria
    query = f"{termo_busca} em {cidade}" if " em " not in termo_busca else termo_busca
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/"

    # ── Navegação com retry e verificação de saúde ──
    navegou_ok = False
    tentativa_nav = 0
    max_tent_nav = 2  # 1 tentativa inicial + 1 recuperação

    while tentativa_nav < max_tent_nav and not navegou_ok:
        tentativa_nav += 1
        t_inicio = datetime.now().isoformat()

        if log:
            log.info("NAVEGAÇÃO tentativa %d/%d | cidade=%s subnicho=%s url=%s",
                     tentativa_nav, max_tent_nav, cidade, subnicho, url[:100])

        try:
            await page.goto(url, wait_until="domcontentloaded",
                            timeout=_TIMEOUT_NAVEGACAO_MS)
            navegou_ok = True
            t_fim = datetime.now().isoformat()
            if log:
                duracao_ms = int((datetime.fromisoformat(t_fim) -
                                  datetime.fromisoformat(t_inicio)).total_seconds() * 1000)
                log.info("NAVEGAÇÃO OK | tentativa=%d | duração=%dms | url_atual=%s",
                         tentativa_nav, duracao_ms, page.url[:80])

        except PlaywrightTimeoutError as e:
            duracao_ms = int((datetime.now() - datetime.fromisoformat(t_inicio)).total_seconds() * 1000)
            if log:
                log.warning("TIMEOUT navegação tentativa %d | duração=%dms | erro=%s | "
                            "page.is_closed=%s | browser.is_connected=%s",
                            tentativa_nav, duracao_ms, str(e)[:200],
                            page.is_closed() if page else "N/A",
                            browser.is_connected() if (browser := _browser) else "N/A")

            # Classificar o estado real do navegador
            saude = _avaliar_saude_pagina(_browser, _context, page)

            if saude == "browser_morto":
                if log:
                    log.error("Navegador morto após timeout — levantando NavegadorFechado")
                raise NavegadorFechado(f"browser desconectado após timeout: {e}")

            if saude == "context_morto":
                if log:
                    log.error("Context morto após timeout — levantando NavegadorFechado")
                raise NavegadorFechado(f"contexto fechado após timeout: {e}")

            if saude == "page_fechada":
                # Tentar recriar a página uma vez
                if tentativa_nav < max_tent_nav:
                    if log:
                        log.info("Page fechada após timeout — recriando página")
                    try:
                        page = await _context.new_page()
                        await page.goto("https://www.google.com/maps",
                                        wait_until="commit", timeout=30000)
                        if log:
                            log.info("Page recriada e Maps carregado — retentando navegação")
                        continue  # retentar a navegação com a nova página
                    except Exception as recriar_err:
                        if log:
                            log.error("Falha ao recriar page: %s", str(recriar_err)[:200])
                        raise NavegadorFechado(
                            f"page fechada após timeout e falha ao recriar: {recriar_err}"
                        )
                else:
                    raise NavegadorFechado(
                        f"page fechada após timeout na segunda tentativa: {e}"
                    )

            # saude == "page_valida" — timeout mas navegador vivo
            if tentativa_nav < max_tent_nav:
                if log:
                    log.info("Timeout mas navegador vivo — tentando recuperação controlada")
                # Recuperação controlada: reload com timeout adequado
                # (somente se page e browser estiverem saudáveis)
                try:
                    await page.reload(wait_until="commit", timeout=30000)
                    await asyncio.sleep(2)
                    if log:
                        log.info("Reload OK — retentando navegação")
                    continue  # retentar a navegação após reload
                except PlaywrightTimeoutError:
                    if log:
                        log.error("Reload também deu timeout — retornando lista vazia")
                    # Segunda tentativa falhou — retornar vazio, não interromper o run
                    return []
                except Exception as reload_err:
                    # Verificar se o reload matou o browser/context
                    saude2 = _avaliar_saude_pagina(_browser, _context, page)
                    if saude2 in ("browser_morto", "context_morto"):
                        raise NavegadorFechado(
                            f"navegador morto após reload: {reload_err}"
                        )
                    if log:
                        log.error("Reload falhou (não-timeout): %s — retornando lista vazia",
                                  str(reload_err)[:200])
                    return []
            else:
                # Segunda tentativa de navegação falhou
                if log:
                    log.error("Segunda tentativa de navegação falhou — retornando lista vazia")
                return []

        except Exception as e:
            erro_lower = str(e).lower()
            eh_navegador_fechado = any(p in erro_lower for p in PADROES_NAVEGADOR_FECHADO)

            if eh_navegador_fechado:
                saude = _avaliar_saude_pagina(_browser, _context, page)
                if log:
                    log.error("Exceção de navegador fechado | tipo=%s | saude=%s | erro=%s",
                              type(e).__name__, saude, str(e)[:200])
                    log.error("Traceback: %s", traceback.format_exc())
                raise NavegadorFechado(f"navegador fechado durante navegação (saude={saude}): {e}")

            # Exceção não-timeout e não-navegador-fechado
            if log:
                log.warning("Exceção não-fatal na navegação tentativa %d: %s | %s",
                            tentativa_nav, type(e).__name__, str(e)[:200])

            # Verificar saúde antes de retentar
            saude = _avaliar_saude_pagina(_browser, _context, page)
            if saude in ("browser_morto", "context_morto"):
                raise NavegadorFechado(f"navegador morto após exceção (saude={saude}): {e}")

            if saude == "page_fechada" and tentativa_nav < max_tent_nav:
                if log:
                    log.info("Page fechada após exceção — recriando")
                try:
                    page = await _context.new_page()
                    await page.goto("https://www.google.com/maps",
                                    wait_until="commit", timeout=30000)
                    continue
                except Exception as recriar_err:
                    raise NavegadorFechado(
                        f"falha ao recriar page após exceção: {recriar_err}"
                    )

            # Erro recuperável — marcar como erro de navegação e continuar
            if tentativa_nav >= max_tent_nav:
                if log:
                    log.error("Navegação falhou após %d tentativas — retornando lista vazia",
                              max_tent_nav)
                return []

    if not navegou_ok:
        if log:
            log.error("Navegação falhou sem exceção — retornando lista vazia")
        return []

    await asyncio.sleep(random.uniform(2, 3))
    await aceitar_cookies(page)
    await asyncio.sleep(2)

    # Deteccao de CAPTCHA/bloqueio — so interrompe se captcha_detector=True.
    # Nao tenta resolver nem contornar.
    captcha_detectado = await detectar_captcha(page)
    if _deve_interromper_por_captcha(captcha_detector, captcha_detectado):
        await salvar_screenshot(page, screenshot_dir, "captcha")
        raise CaptchaDetectado(
            "CAPTCHA/bloqueio detectado no Google Maps — interrompendo execucao"
        )

    # Rola para carregar mais
    await scroll_panel(page)
    await asyncio.sleep(1)

    # ── Verificação de saúde antes de ler resultados ──
    saude_leitura = _avaliar_saude_pagina(_browser, _context, page)
    if log:
        log.info("SAÚDE antes de items.count() | saude=%s | url=%s",
                 saude_leitura, page.url[:80] if not page.is_closed() else "page_closed")

    if saude_leitura in ("browser_morto", "context_morto"):
        if log:
            log.error("Navegador morto antes de items.count() — levantando NavegadorFechado")
        raise NavegadorFechado(f"navegador morto antes de ler resultados (saude={saude_leitura})")

    if saude_leitura == "page_fechada":
        if log:
            log.error("Page fechada antes de items.count() — retornando lista vazia")
        return []

    # Captura todos os resultados
    try:
        items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')
        total = await items.count()
    except Exception as e:
        erro_lower = str(e).lower()
        eh_nav = any(p in erro_lower for p in PADROES_NAVEGADOR_FECHADO)
        browser_morto = (_browser is not None and not _browser.is_connected())
        if eh_nav or browser_morto:
            if log:
                log.error("Navegador fechado durante items.count(): %s", str(e)[:200])
            raise NavegadorFechado(f"navegador fechado ao ler resultados: {e}")
        # Erro não-fatal — retornar zero resultados
        if log:
            log.warning("Erro não-fatal em items.count(): %s — retornando 0 resultados", str(e)[:200])
        total = 0
        items = None

    print(f"  > {total} resultados encontrados")
    if total == 0:
        if log:
            log.info("0 resultados encontrados — retornando lista vazia")
        return []

    comercios = []
    vistos = set()  # Controle de duplicatas nesta sessão

    # Carregar nomes já existentes no CSV para pular
    if nomes_existentes:
        for chave in nomes_existentes:
            if cidade.lower() in chave:
                vistos.add(chave)
    limite = min(total, max_results * 3)  # Tentar até 3x mais que o limite

    # Se está continuando de onde parou, carrega já vistos do progresso
    if start_index > 0:
        print(f"  > Continuando do indice {start_index}...")
        # Carrega duplicatas já vistas do progresso salvo
        for c in progress.get("comercios", []):
            if c.get("categoria") == categoria and c.get("cidade") == cidade:
                chave = f"{c['nome'].lower()}|{cidade}"
                vistos.add(chave)
        print(f"  > {len(vistos)} comércios já processados")

    # Loop até encontrar MAX_RESULTS únicos ou atingir limite
    i = start_index
    novos_encontrados = 0  # Conta só os novos (não os que já existiam no CSV)
    ja_existentes = len(vistos)

    while i < limite and novos_encontrados < max_results:
        # Recarrega os itens a cada iteração (o DOM pode mudar)
        items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')
        total_itens = await items.count()

        if total_itens <= i:
            print(f"    [{novos_encontrados}/{max_results}] Itens reduzidos, recarregando pagina...")
            await scroll_panel(page)
            await asyncio.sleep(1)
            items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')
            total_itens = await items.count()
            if total_itens <= i:
                # Verifica se chegou ao fim da lista
                fim_lista = page.locator('span:has-text("fim da lista"), span:has-text("end of the list")')
                if await fim_lista.count() > 0:
                    print(f"    [{novos_encontrados}/{max_results}] Fim da lista - Sem mais resultados")
                    break
                else:
                    print(f"    [{novos_encontrados}/{max_results}] Nao ha mais itens disponiveis")
                    break

        # Verifica se chegou ao fim da lista antes de processar
        fim_lista = page.locator('span:has-text("fim da lista"), span:has-text("end of the list")')
        if await fim_lista.count() > 0 and i >= total_itens - 1:
            print(f"    [{novos_encontrados}/{max_results}] Fim da lista atingido")
            break

        item = items.nth(i)

        # Verifica se o elemento está visível antes de tentar clicar
        try:
            if not await item.is_visible():
                print(f"    [{novos_encontrados+1}/{max_results}] Elemento não visível, pulando...")
                i += 1
                continue
        except:
            # Se não conseguir verificar visibilidade, tenta clicar mesmo assim
            pass

        # Tenta clicar com retry e maior timeout
        clicou = False
        for tentativa in range(n_tent):
            try:
                await item.click(timeout=10000)
                clicou = True
                break
            except Exception as e:
                erro_str = str(e).lower()
                # Se o erro for "not visible", pula este elemento
                if 'not visible' in erro_str or 'element is not visible' in erro_str:
                    print(f"    [{novos_encontrados+1}/{max_results}] Elemento invisível, pulando...")
                    break
                elif tentativa < n_tent - 1:
                    print(f"    [{novos_encontrados+1}/{max_results}] Retry clique {tentativa + 1}/{n_tent}...")
                    await asyncio.sleep(1)
                    # Tenta scroll com menor timeout
                    try:
                        await item.scroll_into_view_if_needed(timeout=1000)
                    except:
                        pass
                    await asyncio.sleep(0.5)
                else:
                    print(f"    [{novos_encontrados+1}/{max_results}] Erro ao clicar: {str(e)[:60]}")
                    await salvar_screenshot(page, screenshot_dir, f"erro_clique_{i}")
                    break

        if not clicou:
            i += 1
            continue

        await asyncio.sleep(random.uniform(dmin_item, dmax_item))

        dados = await extrair_detalhes(page, categoria, cidade, subnicho=subnicho)
        if dados:
            # Verifica duplicata por nome + cidade
            chave = f"{dados['nome'].lower()}|{cidade.lower()}"
            if chave in vistos:
                print(f"    [{novos_encontrados}/{max_results}] DUPLICATA - {dados['nome'][:40]}")
            else:
                vistos.add(chave)
                comercios.append(dados)
                novos_encontrados += 1
                tag = "COM site" if dados["tem_site"] else "SEM site"
                email_info = f" | Email: {dados['email']}" if dados['email'] else ""
                print(f"    [{novos_encontrados}/{max_results}] {tag} - {dados['nome'][:40]}{email_info}")

                # Salva progresso incrementalmente
                if progress:
                    chave_progresso = f"{cidade}::{categoria}"
                    progress["categorias_em_andamento"][chave_progresso] = {"indice": i + 1, "total": limite}
                    progress["comercios"].extend(comercios)
                    comercios.clear()  # Limpa a lista local já que salvou no progress
                    save_progress(progress, output_dir)

        # Volta para resultados - TENTATIVA 1: botão voltar
        voltou = False
        for _ in range(2):
            try:
                back = page.locator('button[aria-label*="Voltar"], button[aria-label*="Back"]').first
                if await back.count() > 0:
                    await back.click(timeout=3000)
                    await asyncio.sleep(0.5)
                    voltou = True
                    break
            except Exception:
                pass

            # TENTATIVA 2: go_back
            try:
                await page.go_back(timeout=3000)
                await asyncio.sleep(0.5)
                voltou = True
                break
            except Exception:
                pass

        if not voltou:
            # TENTATIVA 3: recarrega a URL de busca
            print(f"    [{novos_encontrados}/{max_results}] Navegacao travada, recarregando...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            await scroll_panel(page, max_scrolls=5)
            await asyncio.sleep(1)

        await asyncio.sleep(random.uniform(0.8, 1.5))
        i += 1

    # Mensagem final sobre a categoria
    if novos_encontrados >= max_results:
        print(f"  > Categoria completa: {novos_encontrados} novos resultados encontrados")
    else:
        print(f"  > Fim dos resultados: {novos_encontrados}/{max_results} novos ({ja_existentes} já existiam)")

    return comercios


# ── Main ────────────────────────────────────────────────────────────

async def main():
    # Argumentos
    parser = argparse.ArgumentParser(description="Mapeador de Comercios - Google Maps")
    parser.add_argument(
        "--regiao",
        default=None,
        help="Regiao: no modo landing (baixada/rio_premium/todas); "
             "no modo AVGESTAO com --escopo regiao, nome da regiao IBGE (ex: sudeste, nordeste)",
    )
    parser.add_argument(
        "--produto",
        choices=["landing", "avgestao"],
        default="landing",
        help="Produto: landing (padrao, comportamento antigo) ou avgestao",
    )
    parser.add_argument(
        "--grupo",
        default=None,
        help="Grupo do AVGESTAO: assistencias, refrigeracao, automotivo, sob_medida, servicos_externos",
    )
    parser.add_argument(
        "--cidade",
        default=None,
        help="Cidade para busca AVGESTAO (ex: 'Nova Iguacu, RJ')",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Maximo de resultados por subnicho (alias de --max-por-consulta; "
             "default 20 se nem --max nem --max-por-consulta forem informados).",
    )
    # ── CLI geografica (etapa 9) — sem remover os antigos ──────────────
    parser.add_argument("--escopo",
        choices=["cidade", "cidades", "uf", "ufs", "regiao", "brasil", "arquivo"],
        default=None, help="Escopo geografico do modo AVGESTAO escalado")
    parser.add_argument("--cidades", nargs="+", default=None,
        help="Lista de cidades 'Nome, UF' para --escopo cidades")
    parser.add_argument("--uf", nargs="+", default=None,
        help="Lista de UFs para --escopo uf/ufs (ex: RJ SP)")
    parser.add_argument("--ufs", nargs="+", default=None, dest="ufs",
        help="Alias de --uf")
    parser.add_argument("--cidades-arquivo", default=None,
        help="Caminho de arquivo com cidades (uma por linha, 'Nome, UF')")
    parser.add_argument("--limite-cidades", type=int, default=None,
        help="Limita o numero de cidades resolvidas")
    parser.add_argument("--max-por-cidade", type=int, default=None,
        help="Limite de leads unicos por cidade (runtime, nao trunca a fila)")
    parser.add_argument("--max-por-subnicho", type=int, default=None,
        help="Limite de leads unicos por subnicho (runtime)")
    parser.add_argument("--max-total", type=int, default=None,
        help="Limite total de leads unicos no run")
    parser.add_argument("--max-por-consulta", type=int, default=None,
        help="Maximo de resultados por consulta (alias de --max)")
    parser.add_argument("--resume", action="store_true",
        help="Retoma um run existente (exige --run-id)")
    parser.add_argument("--run-id", default=None,
        help="Id do run (gerado se omitido; exigido com --resume)")
    parser.add_argument("--dry-run", action="store_true",
        help="Resolve cidades, gera fila/checkpoint e mostra distribuicao sem abrir browser")
    parser.add_argument("--somente-gerar-fila", action="store_true",
        help="Como --dry-run: gera fila e encerra sem abrir browser")
    parser.add_argument("--ordem-cidades",
        choices=["fornecida", "capitais", "maiores", "alfabetica", "aleatoria"],
        default="fornecida", help="Ordem das cidades na fila")
    parser.add_argument("--delay-min", type=float, default=None,
        help="Delay minimo (s) entre consultas (default 2.0)")
    parser.add_argument("--delay-max", type=float, default=None,
        help="Delay maximo (s) entre consultas (default 5.0)")
    parser.add_argument("--max-tentativas", type=int, default=3,
        help="Tentativas de clique por item (default 3)")
    parser.add_argument("--headless", action="store_true",
        help="Executa Chromium em modo headless")
    parser.add_argument("--permitir-base-incompleta", action="store_true",
        help="Permite escopos amplos mesmo com base de municipios incompleta")
    parser.add_argument("--confirmar-grande-execucao", action="store_true",
        help="Confirmacao explicita para --escopo brasil sem --max-total/--limite-cidades")
    parser.add_argument("--legacy", action="store_true",
        help="Fluxo AVGESTAO antigo (contingencia; nao documentado)")
    args = parser.parse_args()

    # Força UTF-8 no Windows
    if sys.platform == "win32":
        import locale
        import codecs
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[!] Playwright não encontrado. Instalando...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.async_api import async_playwright

    if args.produto == "avgestao":
        if args.legacy:
            return await main_avgestao(args, async_playwright)
        return await main_avgestao_escalado(args, async_playwright)

    regioes = resolve_regiao(args.regiao)

    for regiao in regioes:
        locais = get_locais_busca(regiao)
        categorias = regiao.categorias
        max_results = regiao.max_results_per_category
        output_dir = get_output_dir(regiao.key, "playwright")

        print("=" * 60)
        print(f"  MAPEADOR DE COMÉRCIOS — {regiao.label.upper()}")
        print("  Buscando comércios SEM site para prospecção")
        print(f"  {len(locais)} locais serão mapeados | {len(categorias)} categorias")
        print("=" * 60)

        progress = load_progress(output_dir)
        feitas = set(progress.get("categorias_prontas", []))
        em_andamento = progress.get("categorias_em_andamento", {})
        todos = progress.get("comercios", [])

        # Carregar nomes já existentes no CSV para evitar duplicatas
        nomes_existentes = load_nomes_existentes(output_dir)
        if nomes_existentes:
            print(f"\n  {len(nomes_existentes)} comércios já existem no CSV (serão pulados)")

        # Formato antigo de progresso (cidade única) - migra para novo formato
        if not feitas and not em_andamento and not todos:
            print("\n[!] Progresso antigo detectado. Resetando para nova estrutura multi-cidade.")
            print("    Todas as cidades e categorias serão reprocessadas.\n")

        # Adiciona categorias em andamento às restantes (para continuar)
        restantes = [c for c in categorias if c not in feitas]
        print(f"\nCategorias restantes: {len(restantes)}/{len(categorias)}")
        print(f"Locais a processar: {len(locais)}")
        print(f"Comércios já mapeados: {len(todos)}")
        if em_andamento:
            print(f"Em andamento: {list(em_andamento.keys())}\n")

        if not restantes and not em_andamento:
            print("Todas as categorias já foram buscadas!")
            print(f"Delete {output_dir / 'progresso.json'} para recomeçar.\n")
            continue

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="pt-BR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()

            # Abre o Google Maps e aceita cookies iniciais
            try:
                await page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"[!] Timeout ao carregar Maps. Tentando novamente... ({e})")
                await page.goto("https://www.google.com/maps", wait_until="commit", timeout=30000)
            await asyncio.sleep(3)
            await aceitar_cookies(page)
            await asyncio.sleep(1)

            # Itera sobre cada local e cada categoria
            total_tarefas = len(locais) * len(categorias)
            tarefa_atual = 0

            for local_idx, local in enumerate(locais):
                print(f"\n{'='*60}")
                print(f"  [{regiao.label}] LOCAL {local_idx+1}/{len(locais)}: {local}")
                print(f"{'='*60}")

                for cat_idx, cat in enumerate(categorias):
                    tarefa_atual += 1

                    # Pula categorias já concluídas
                    chave_progresso = f"{local}::{cat}"
                    if chave_progresso in feitas:
                        continue

                    print(f"\n[{tarefa_atual}/{total_tarefas}] [{regiao.key}] {local} - {cat}")

                    # Verifica se já estava em andamento
                    start_idx = 0
                    if chave_progresso in em_andamento:
                        start_idx = em_andamento[chave_progresso].get("indice", 0)
                        print(f"  > Continuando do índice {start_idx}")

                    try:
                        resultados = await buscar_categoria(
                            page, cat, local,
                            start_index=start_idx,
                            progress=progress,
                            nomes_existentes=nomes_existentes,
                            max_results=max_results,
                            output_dir=output_dir,
                        )

                        # Marca categoria como completa
                        if chave_progresso in em_andamento:
                            del em_andamento[chave_progresso]
                        feitas.add(chave_progresso)
                        progress["categorias_prontas"] = list(feitas)
                        progress["categorias_em_andamento"] = em_andamento
                        save_progress(progress, output_dir)

                        # Conta sem site (do progresso atualizado)
                        sem = sum(1 for c in progress["comercios"] if c["categoria"] == cat and c.get("cidade") == local and not c["tem_site"])
                        todos_categoria = [c for c in progress["comercios"] if c["categoria"] == cat and c.get("cidade") == local]
                        print(f"  > {len(todos_categoria)} encontrados | {sem} sem site")

                    except Exception as e:
                        print(f"  X Erro geral: {e}")
                        # Tenta navegar de volta ao Maps
                        try:
                            await page.goto("https://www.google.com/maps", wait_until="commit", timeout=15000)
                        except Exception:
                            pass
                        continue

                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    print(f"  Aguardando {delay:.1f}s...")
                    await asyncio.sleep(delay)

            await browser.close()

        # ── Exporta resultados ──────────────────────────────────────────
        # Recarrega o progresso para ter dados atualizados
        progress = load_progress(output_dir)
        todos = progress.get("comercios", [])

        if not todos:
            print("\nNenhum comércio novo encontrado.")
            continue

        # Mesclar com comércios já existentes no CSV
        existing_csv = output_dir / "todos_comercios.csv"
        existentes_csv = []
        if existing_csv.exists():
            with open(existing_csv, encoding="utf-8-sig") as f:
                existentes_csv = list(csv.DictReader(f))

        # Criar set de chaves dos novos para evitar duplicatas na mesclagem
        novos_nomes = set()
        for c in todos:
            novos_nomes.add(f"{c['nome'].lower().strip()}|{c.get('cidade', '').lower().strip()}")

        # Filtrar existentes que não estão nos novos
        mantidos = [c for c in existentes_csv
                    if f"{c['nome'].lower().strip()}|{c.get('cidade', '').lower().strip()}" not in novos_nomes]

        todos_final = mantidos + todos
        print(f"\n  Mesclando: {len(mantidos)} existentes + {len(todos)} novos = {len(todos_final)} total")

        # Todos os comércios
        export_csv(todos_final, "todos_comercios.csv", output_dir)
        print(f"\n  CSV completo: {output_dir / 'todos_comercios.csv'}")

        # Leads sem site
        sem_site = [c for c in todos_final if not c["tem_site"]]
        if sem_site:
            export_csv(sem_site, "leads_sem_site.csv", output_dir)
            print(f"  CSV leads:    {output_dir / 'leads_sem_site.csv'}")

            xlsx = export_excel(sem_site, "leads_sem_site.xlsx", output_dir)
            if xlsx:
                print(f"  Excel leads:  {xlsx}")

        # Resumo
        com_site = len(todos_final) - len(sem_site)
        taxa = (len(sem_site) / len(todos_final) * 100) if todos_final else 0
        print(f"\n{'='*50}")
        print(f"  RESUMO FINAL - {regiao.label.upper()}")
        print(f"  Total mapeados:     {len(todos_final)}")
        print(f"  COM site:           {com_site}")
        print(f"  SEM site (leads):   {len(sem_site)}")
        print(f"  Taxa de prospecção: {taxa:.1f}%")
        print(f"{'='*50}")

        # Estatísticas por local
        print(f"\n  ESTATÍSTICAS POR LOCAL:")
        print(f"  {'-'*50}")
        for local in locais:
            da_local = [c for c in todos_final if c.get("cidade") == local]
            sem_site_local = [c for c in da_local if not c["tem_site"]]
            if da_local:
                print(f"  {local.split(',')[0]:20s}: {len(da_local):4d} total | {len(sem_site_local):4d} sem site")
        print(f"{'='*50}")


async def main_avgestao(args, async_playwright):
    """Fluxo de mapeamento no modo AVGESTAO.

    Usa consultas especificas por subnicho e cidade, captura place_id,
    deduplica por place_id -> url maps -> telefone -> nome+endereco.
    Preserva pausas entre consultas e retomada apos interrupcao.
    """
    from config.regioes import BAIXADA
    from datetime import date

    grupos = resolver_grupo(args.grupo)
    cidade_arg = args.cidade
    max_results = args.max if args.max is not None else 20

    cidades = [cidade_arg] if cidade_arg else list(BAIXADA.cidades)
    hoje = date.today().isoformat()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        try:
            await page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[!] Timeout ao carregar Maps. Tentando novamente... ({e})")
            await page.goto("https://www.google.com/maps", wait_until="commit", timeout=30000)
        await asyncio.sleep(3)
        await aceitar_cookies(page)
        await asyncio.sleep(1)

        for grupo in grupos:
            output_dir = Path("output") / "avgestao" / grupo.key
            output_dir.mkdir(parents=True, exist_ok=True)

            print("\n" + "=" * 60)
            print(f"  MAPEADOR AVGESTAO — {grupo.label.upper()}")
            print(f"  {len(grupo.subnichos)} subnichos | {len(cidades)} cidades")
            print("=" * 60)

            progress = load_progress(output_dir)
            todos = progress.get("comercios", [])
            vistos_chaves = set()
            for c in todos:
                vistos_chaves.add(f"{c.get('nome','').lower()}|{c.get('cidade','').lower()}|{c.get('subnicho','').lower()}")

            for cidade in cidades:
                print(f"\n  CIDADE: {cidade}")
                consultas = gerar_consultas_meta(grupo.key, cidade)

                for sub_idx, consulta in enumerate(consultas, 1):
                    query = consulta["query"]
                    subnicho_label = consulta["subnicho_label"]
                    subnicho_key = consulta["subnicho"]
                    msg_cat = consulta["msg_cat"]
                    print(f"\n  [{sub_idx}/{len(consultas)}] {subnicho_label} em {cidade}")

                    try:
                        resultados = await buscar_categoria(
                            page, subnicho_label, cidade,
                            start_index=0,
                            progress=progress,
                            nomes_existentes=None,
                            max_results=max_results,
                            output_dir=output_dir,
                            subnicho=subnicho_label,
                            query_term=query,
                        )

                        for r in resultados:
                            r["grupo"] = grupo.key
                            r["subnicho"] = subnicho_key
                            r["msg_cat"] = msg_cat
                            r["source_query"] = query
                            chave = f"{r.get('nome','').lower()}|{r.get('cidade','').lower()}|{r.get('subnicho','').lower()}"
                            if chave not in vistos_chaves:
                                vistos_chaves.add(chave)
                                todos.append(r)

                        progress["comercios"] = todos
                        save_progress(progress, output_dir)

                    except Exception as e:
                        print(f"  X Erro em {subnicho_label}: {e}")
                        try:
                            await page.goto("https://www.google.com/maps", wait_until="commit", timeout=15000)
                        except Exception:
                            pass

                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    print(f"  Aguardando {delay:.1f}s...")
                    await asyncio.sleep(delay)

        await browser.close()

    # Deduplica e exporta por grupo (apos fechar o browser)
    for grupo in grupos:
        output_dir = Path("output") / "avgestao" / grupo.key
        progress = load_progress(output_dir)
        todos = progress.get("comercios", [])
        if not todos:
            print(f"\n  Nenhum comércio encontrado para {grupo.label}.")
            continue

        unicos = deduplicar_leads(todos)
        print(f"\n  {grupo.label}: {len(todos)} bruto -> {len(unicos)} únicos (dedup place_id/maps/tel/nome+end)")

        csv_path = export_csv_avgestao(unicos, f"comercios_{grupo.key}_{hoje}.csv", output_dir)
        print(f"  CSV:  {csv_path}")
        xlsx_path = export_excel_avgestao_raw(unicos, f"comercios_{grupo.key}_{hoje}.xlsx", output_dir)
        if xlsx_path:
            print(f"  Excel: {xlsx_path}")

        # Estatísticas por subnicho
        print(f"\n  ESTATÍSTICAS POR SUBNICHO — {grupo.label.upper()}")
        print(f"  {'-'*50}")
        subs = {}
        for c in unicos:
            s = c.get("subnicho") or "(sem subnicho)"
            subs[s] = subs.get(s, 0) + 1
        for s, q in sorted(subs.items(), key=lambda x: -x[1]):
            print(f"  {s:40s}: {q}")
        print(f"{'='*50}")


# ══════════════════════════════════════════════════════════════════
# MODO AVGESTAO ESCALADO (etapa 9) — fila + checkpoint + dedup global
# ══════════════════════════════════════════════════════════════════

def _validar_args_escaldo(args):
    """Validacoes de CLI do modo escalado. Aborta (SystemExit) em conflito."""
    # --max e --max-por-consulta: alias; se ambos informados e diferentes, erro
    if args.max_por_consulta is not None and args.max is not None \
            and args.max != args.max_por_consulta:
        print("❌ Conflito: --max e --max-por-consulta informados com valores diferentes "
              f"({args.max} != {args.max_por_consulta}). Use apenas um.")
        sys.exit(1)
    # max_por_consulta efetivo (default historico 20 se nenhum informado)
    if args.max_por_consulta is not None:
        mpc = args.max_por_consulta
    elif args.max is not None:
        mpc = args.max
    else:
        mpc = 20
    # Proteção Brasil: exige --max-total OU --limite-cidades OU --confirmar-grande-execucao
    if args.escopo == "brasil":
        if not (args.max_total or (args.limite_cidades and args.limite_cidades > 0)
                or args.confirmar_grande_execucao):
            print("❌ Execução com --escopo brasil exige --max-total, --limite-cidades "
                  "ou --confirmar-grande-execucao (para evitar captacao nacional nao intencional).")
            sys.exit(1)
    # Resume exige run-id
    if args.resume and not args.run_id:
        print("❌ --resume exige --run-id <id>.")
        sys.exit(1)
    # delay inter-task valido
    dmin = args.delay_min if args.delay_min is not None else DELAY_MIN
    dmax = args.delay_max if args.delay_max is not None else DELAY_MAX
    if dmin < 0 or dmax < 0:
        print("❌ --delay-min/--delay-max nao podem ser negativos.")
        sys.exit(1)
    if dmin > dmax:
        print(f"❌ --delay-min ({dmin}) maior que --delay-max ({dmax}).")
        sys.exit(1)
    return mpc, dmin, dmax


def _escopo_do_args(args) -> str:
    """Descobre o escopo efetivo. Default historico: Baixada (cidades)."""
    if args.escopo:
        return args.escopo
    # sem escopo e sem cidade -> Baixada (comportamento historico)
    if args.cidade:
        return "cidade"
    if args.cidades:
        return "cidades"
    return "cidades"  # default Baixada


def _resolver_municipios_do_args(args, run_id):
    """Resolve os municipios conforme o escopo. Default Baixada historico."""
    escopo = _escopo_do_args(args)
    if not args.escopo and not args.cidade and not args.cidades:
        # default historico: Baixada
        return T.resolver_cidades(
            escopo="cidades", cidades=list(BAIXADA.cidades),
            limite_cidades=args.limite_cidades, ordem=args.ordem_cidades,
            run_id=run_id, permitir_base_incompleta=args.permitir_base_incompleta,
        )
    return T.resolver_cidades(
        escopo=escopo,
        cidade=args.cidade,
        cidades=args.cidades,
        uf=args.uf,
        ufs=args.ufs or args.uf,
        regiao=args.regiao if escopo == "regiao" else None,
        cidades_arquivo=args.cidades_arquivo,
        limite_cidades=args.limite_cidades,
        ordem=args.ordem_cidades,
        run_id=run_id,
        permitir_base_incompleta=args.permitir_base_incompleta,
    )


def _escopo_descritor(args, municipios):
    """Label curto do escopo para nomes de arquivo e config."""
    if args.escopo == "brasil":
        return "brasil"
    if args.escopo == "regiao":
        return (args.regiao or "regiao")
    if args.escopo in ("uf", "ufs"):
        return "_".join(args.ufs or args.uf or [])
    if args.escopo in ("cidades", "arquivo"):
        return f"{len(municipios)}cidades"
    if args.escopo == "cidade":
        return (args.cidade or "cidade").replace(", ", "_").replace(" ", "_")
    return "baixada"


def _serializar_municipios(municipios) -> list:
    """Serializa Municipio para dict JSON-serializavel (preserva nome/uf/normalizado)."""
    out = []
    for m in municipios or []:
        if isinstance(m, dict):
            out.append(m)
        else:
            out.append({
                "nome": getattr(m, "nome", ""),
                "uf": getattr(m, "uf", ""),
                "nome_normalizado": getattr(m, "nome_normalizado", "") or
                    getattr(m, "nome", ""),
                "regiao": getattr(m, "regiao", ""),
            })
    return out


def _config_do_run(args, municipios, run_id, max_por_consulta, escopo_descritor):
    """Monta o dict de configuracao estrutural do run."""
    return {
        "produto": "avgestao",
        "run_id": run_id,
        "grupos": [g.key for g in resolver_grupo(args.grupo)],
        "escopo": _escopo_do_args(args),
        "escopo_descritor": escopo_descritor,
        "municipios": _serializar_municipios(municipios),
        "subnichos": [s.subnicho_key for g in resolver_grupo(args.grupo) for s in g.subnichos],
        "consultas": [],
        "ordem_cidades": args.ordem_cidades,
        "limite_cidades": args.limite_cidades,
        "max_por_consulta": max_por_consulta,
        "max_por_cidade": args.max_por_cidade,
        "max_por_subnicho": args.max_por_subnicho,
        "max_total": args.max_total,
        "delay_min": args.delay_min if args.delay_min is not None else DELAY_MIN,
        "delay_max": args.delay_max if args.delay_max is not None else DELAY_MAX,
        "max_tentativas": args.max_tentativas,
        "headless": args.headless,
        "permitir_base_incompleta": args.permitir_base_incompleta,
    }


def _enriquecer_lead_geo(lead, item, escopo, run_id):
    """Adiciona campos geograficos + captured_at UTC ao lead aceito."""
    lead["grupo"] = item.grupo
    lead["subnicho"] = item.subnicho
    lead["msg_cat"] = item.msg_cat
    lead["uf"] = item.uf
    lead["estado"] = UF_NOMES.get(item.uf, "")
    lead["regiao"] = item.regiao
    lead["source_query"] = item.query
    lead["source_scope"] = escopo
    lead["run_id"] = run_id
    lead["captured_at"] = datetime.now(timezone.utc).isoformat()
    # maps_url: a base de dedup lê link_maps|url_maps|maps_url; o CSV GEO usa maps_url
    lead["maps_url"] = lead.get("link_maps", "") or lead.get("maps_url", "")
    return lead


def _carregar_chaves_supabase():
    """Pre-carrega chaves do Supabase para o dedup global.

    Retorna dict {place_ids, maps_urls, telefones} ou None se o Supabase nao
    estiver configurado. Erros de conexao/autenticacao SAO propagados (nao
    sao escondidos como 'coluna ausente').
    """
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None  # Supabase nao configurado -> skip (sem dedup contra base)
    from supabase import create_client  # type: ignore
    from import_leads_to_supabase import listar_chaves_existentes
    sb = create_client(url, key)  # auth/conexao -> propaga
    ch = listar_chaves_existentes(sb)
    return {
        "place_ids": ch["place_ids"],
        "maps_urls": ch["maps_urls"],
        "telefones": ch["telefones"],
    }


def _reconstituir_dedup_parciais(run_id):
    """Cria IndexadorDedup e pre-carrega com leads_parciais.csv do run."""
    idx = DEDUP.IndexadorDedup()
    parciais = RUNS.ler_leads_parciais(run_id)
    for lead in parciais:
        # re-alimenta o indexador: add retorna False para duplicatas internas,
        # mas queremos registrar as chaves. add ja registra quando aceita.
        idx.add(lead)
    return idx


def _exportar_xlsx_geo(leads, caminho):
    """Exporta XLSX geografico agregado usando COLUNAS_XLSX_AVGESTAO_GEO.

    Aplica enriquecer_lead_avgestao para preencher score/motivos/mensagem.
    Nao altera COLUNAS_XLSX_AVGESTAO (as 20 originais).
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("  [!] openpyxl nao instalado — pulando XLSX geo")
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads GEO"
    headers = [c[0] for c in COLUNAS_XLSX_AVGESTAO_GEO]
    campos = [c[1] for c in COLUNAS_XLSX_AVGESTAO_GEO]
    widths = [c[2] for c in COLUNAS_XLSX_AVGESTAO_GEO]
    hfont = Font(bold=True, color="FFFFFF")
    hfill = PatternFill("solid", fgColor="7C3AED")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = hfont
        cell.fill = hfill
        cell.alignment = Alignment(horizontal="center")
    for r, lead in enumerate(leads, 2):
        row = dict(lead)
        try:
            row.update(enriquecer_lead_avgestao(lead))
        except Exception:
            pass
        for c, campo in enumerate(campos, 1):
            v = row.get(campo, lead.get(campo, ""))
            if campo == "tem_site":
                v = "Sim" if v else "NÃO"
            ws.cell(row=r, column=c, value=v)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.auto_filter.ref = ws.dimensions
    caminho.parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho)
    return caminho


def _exportar_parciais_xlsx(leads, caminho):
    """Exporta leads_parciais.xlsx (colunas COLUNAS_CSV_GEO, raw)."""
    try:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter
    except ImportError:
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads parciais"
    cols = RUNS.COLUNAS_CSV_GEO
    for c, h in enumerate(cols, 1):
        ws.cell(row=1, column=c, value=h)
    for r, lead in enumerate(leads, 2):
        for c, campo in enumerate(cols, 1):
            ws.cell(row=r, column=c, value=lead.get(campo, ""))
    for i, _ in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = 22
    caminho.parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho)
    return caminho


def _imprimir_distribuicao(fila, municipios, max_por_consulta):
    """Mostra distribuicao por UF, regiao, cidade, grupo e subnicho (dry-run)."""
    dist = FILA.distribuicao_estimada(fila, max_por_consulta)
    print(f"\n  Cidades: {dist['cidades']} | UFs: {dist['ufs']}")
    print(f"  Tarefas: {dist['total_tarefas']}")
    print(f"  Estimativa maxima de resultados: {dist['estimativa_maxima_leads']}")
    print(f"\n  Por UF:")
    for uf, q in sorted(dist["por_uf"].items()):
        print(f"    {uf:4s}: {q}")
    print(f"\n  Por regiao:")
    for reg, q in sorted(dist["por_regiao"].items()):
        print(f"    {reg:18s}: {q}")
    print(f"\n  Por grupo:")
    for g, q in sorted(dist["por_grupo"].items()):
        print(f"    {g:18s}: {q}")
    print(f"\n  Por subnicho:")
    for s, q in sorted(dist["por_subnicho"].items()):
        print(f"    {s:40s}: {q}")
    print(f"\n  Por cidade:")
    for cid, q in sorted(dist["por_cidade"].items()):
        print(f"    {cid:40s}: {q}")


def _agora_iso():
    return datetime.now(timezone.utc).isoformat()


def _config_para_resume(args, config_salvo, run_id, max_por_consulta):
    """Constroi a config de comparacao do resume mesclando salvo + args.

    Campos estruturais NAO informados (None/default) herdam do config_salvo,
    permitindo retomar sem re-passar --cidade/--grupo/--escopo. Campos
    explicitamente informados sobrescrevem (e divergem se diferentes do salvo).
    """
    cfg = dict(config_salvo)
    cfg["run_id"] = run_id
    cfg["produto"] = "avgestao"
    cfg["versao_fila"] = config_salvo.get("versao_fila", RUNS.VERSAO_FILA)
    # max_por_consulta: se usuario informou --max/--max-por-consulta, usa; senao salvo
    if args.max_por_consulta is not None or args.max is not None:
        cfg["max_por_consulta"] = max_por_consulta
    else:
        cfg["max_por_consulta"] = config_salvo.get("max_por_consulta", max_por_consulta)
    # limites: so sobrescreve se informado explicitamente
    if args.max_por_cidade is not None:
        cfg["max_por_cidade"] = args.max_por_cidade
    if args.max_por_subnicho is not None:
        cfg["max_por_subnicho"] = args.max_por_subnicho
    if args.max_total is not None:
        cfg["max_total"] = args.max_total
    if args.ordem_cidades and args.ordem_cidades != "fornecida":
        cfg["ordem_cidades"] = args.ordem_cidades
    # grupos/subnichos: se --grupo informado, recalcula; senao mantem do salvo
    if args.grupo:
        grupos = resolver_grupo(args.grupo)
        cfg["grupos"] = [g.key for g in grupos]
        cfg["subnichos"] = [s.subnicho_key for g in grupos for s in g.subnichos]
    if args.escopo:
        cfg["escopo"] = args.escopo
    return cfg


async def _executar_com_browser(run_id, fila, motor, indexador,
                                 args, escopo, max_por_consulta,
                                 screenshot_dir, dmin_inter, dmax_inter,
                                 cp, municipios, escopo_descritor):
    """Abre Chromium, processa fila e fecha navegador.

    Extraido para permitir lock opcional (testes usam LOCK_DISABLED=1).
    """
    from playwright.async_api import async_playwright

    log = _logger_captura(run_id)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=bool(args.headless),
            args=["--disable-blink-features=AutomationControlled"],
        )
        log.info("BROWSER LAUNCHED | browser.is_connected=%s | PID=%s",
                 browser.is_connected(), os.getpid())

        # ── Instrumentação de eventos Playwright ──
        def on_browser_disconnected():
            log.warning("EVENTO: browser.on('disconnected') — browser desconectou")

        def on_page_close():
            log.info("EVENTO: page.on('close') — page fechada")

        def on_page_crash():
            log.error("EVENTO: page.on('crash') — page crashou")

        browser.on("disconnected", on_browser_disconnected)

        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()
        page.on("close", on_page_close)
        page.on("crash", on_page_crash)

        # ── Timeout de navegação e seletores ──
        page.set_default_navigation_timeout(_TIMEOUT_NAVEGACAO_MS)
        page.set_default_timeout(_TIMEOUT_SELETOR_MS)

        log.info("PAGE CRIADA | timeouts: nav=%dms sel=%dms",
                 _TIMEOUT_NAVEGACAO_MS, _TIMEOUT_SELETOR_MS)

        try:
            try:
                log.info("GOTO Maps inicial (timeout=%dms)", _TIMEOUT_NAVEGACAO_MS)
                await page.goto("https://www.google.com/maps",
                                wait_until="domcontentloaded",
                                timeout=_TIMEOUT_NAVEGACAO_MS)
                log.info("Maps carregado com sucesso")
            except PlaywrightTimeoutError as e:
                log.warning("Timeout ao carregar Maps inicial: %s — tentando commit", str(e)[:200])
                saude = _avaliar_saude_pagina(browser, ctx, page)
                if saude in ("browser_morto", "context_morto"):
                    log.error("Navegador morto após timeout no Maps inicial (saude=%s)", saude)
                    raise NavegadorFechado(f"navegador morto ao carregar Maps (saude={saude}): {e}")
                try:
                    await page.goto("https://www.google.com/maps",
                                    wait_until="commit", timeout=30000)
                    log.info("Maps carregado com commit (segunda tentativa)")
                except Exception as e2:
                    saude2 = _avaliar_saude_pagina(browser, ctx, page)
                    log.error("Falha total ao carregar Maps | saude=%s | erro=%s",
                              saude2, str(e2)[:200])
                    if saude2 in ("browser_morto", "context_morto"):
                        raise NavegadorFechado(f"navegador morto ao carregar Maps: {e2}")
                    # Maps não carregou, mas navegador vivo — continuar mesmo assim
                    log.warning("Maps não carregou, mas navegador vivo — continuando")
            except Exception as e:
                erro_lower = str(e).lower()
                if any(p in erro_lower for p in PADROES_NAVEGADOR_FECHADO):
                    saude = _avaliar_saude_pagina(browser, ctx, page)
                    log.error("Navegador fechado ao carregar Maps | saude=%s | erro=%s",
                              saude, str(e)[:200])
                    raise NavegadorFechado(f"navegador fechado ao carregar Maps (saude={saude}): {e}")
                log.warning("Erro não-fatal ao carregar Maps: %s", str(e)[:200])

            await asyncio.sleep(3)
            await aceitar_cookies(page)

            try:
                await _processar_fila(run_id, fila, motor, indexador,
                                      browser, ctx, page, args,
                                      escopo, max_por_consulta, screenshot_dir,
                                      dmin_inter, dmax_inter, cp)
            except (KeyboardInterrupt, asyncio.CancelledError):
                atual = _tarefa_atual(fila)
                RUNS.salvar_estado_interrupcao(run_id, fila, cp, atual,
                                               "interrompido pelo usuario/cancelamento")
                log.info("INTERRUPÇÃO: run interrompido pelo usuário")
                print("\n⏹  Execucao interrompida — estado salvo.")
            except CaptchaDetectado as e:
                atual = _tarefa_atual(fila)
                RUNS.salvar_estado_interrupcao(run_id, fila, cp, atual,
                                               f"captcha detectado: {e}")
                log.warning("CAPTCHA detectado — run interrompido")
                print("\n🛑  CAPTCHA detectado — execucao interrompida e estado salvo.")
            except NavegadorFechado as e:
                atual = _tarefa_atual(fila)
                RUNS.salvar_estado_interrupcao(run_id, fila, cp, atual,
                                               f"navegador fechado: {e}")
                log.error("NAVEGADOR FECHADO — run interrompido: %s", str(e)[:300])
                print(f"\n🛑 Navegador/contexto fechado — run interrompido")
        finally:
            log.info("FINALLY: iniciando fechamento | browser.is_connected=%s | page.is_closed=%s",
                     browser.is_connected() if browser else "None",
                     page.is_closed() if page else "None")
            if page is not None and not page.is_closed():
                try:
                    await page.close()
                    log.info("FINALLY: page.close() OK")
                except Exception as e:
                    log.warning("FINALLY: page.close() falhou: %s", str(e)[:200])
            if ctx is not None:
                try:
                    await ctx.close()
                    log.info("FINALLY: ctx.close() OK")
                except Exception as e:
                    log.warning("FINALLY: ctx.close() falhou: %s", str(e)[:200])
            if browser is not None and browser.is_connected():
                try:
                    await browser.close()
                    log.info("FINALLY: browser.close() OK")
                except Exception as e:
                    log.warning("FINALLY: browser.close() falhou: %s", str(e)[:200])
            log.info("FINALLY: fechamento concluído")


async def main_avgestao_escalado(args, async_playwright):
    """Fluxo AVGESTAO escalado: fila + checkpoint + dedup global + limites.

    Sem escopo/cidade -> Baixada historica. --cidade -> escopo cidade.
    --dry-run/--somente-gerar-fila nao abrem browser. --resume valida config_hash.
    """
    max_por_consulta, dmin_inter, dmax_inter = _validar_args_escaldo(args)
    escopo = _escopo_do_args(args)

    # ── RESUME: carrega run existente ────────────────────────────────
    if args.resume:
        run_id = args.run_id
        # checa existencia sem criar (pasta_run cria o diretorio)
        run_dir = RUNS.OUTPUT_BASE / run_id
        if not run_dir.exists() or not (run_dir / "config.json").exists():
            print(f"❌ Run inexistente: {run_id}")
            sys.exit(1)
        config_salvo = RUNS.carregar_config(run_id)
        config_atual = _config_para_resume(args, config_salvo, run_id, max_por_consulta)
        motivos = RUNS.verificar_compatibilidade_resume(config_salvo, config_atual)
        if motivos:
            print("❌ Resume incompativel — configuracao estrutural divergente:")
            for m in motivos:
                print(f"    - {m}")
            print("    Alterar limites/escopo/grupos exige um novo run.")
            sys.exit(1)
        # max_por_consulta efetivo do run (herda do salvo se nao informado)
        max_por_consulta = config_atual["max_por_consulta"]
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        municipios = config_salvo.get("municipios", [])
        escopo_descritor = config_salvo.get("escopo_descritor", "run")
        escopo = config_salvo.get("escopo", escopo)
        print(f"↻ Retomando run {run_id}: {len(fila)} tarefas na fila")
    else:
        # ── NOVO RUN: resolver municipios e criar run ─────────────────
        run_id = args.run_id or RUNS.gerar_run_id()
        municipios = _resolver_municipios_do_args(args, run_id)
        if not municipios:
            print("❌ Nenhuma cidade resolvida para o escopo informado.")
            sys.exit(1)
        escopo_descritor = _escopo_descritor(args, municipios)
        config = _config_do_run(args, municipios, run_id, max_por_consulta, escopo_descritor)
        RUNS.salvar_config(run_id, config)
        grupos = resolver_grupo(args.grupo)
        fila = FILA.gerar_fila(grupos, municipios, max_por_consulta=max_por_consulta,
                               run_id=run_id)
        RUNS.salvar_fila_run(run_id, fila)
        cp = RUNS.novo_checkpoint(run_id, len(fila))
        cp["config_hash"] = config.get("config_hash")
        RUNS.salvar_checkpoint(run_id, cp)
        print(f"✓ Run criado: {run_id}")
        print(f"  Escopo: {escopo} ({escopo_descritor}) | Cidades: {len(municipios)}")

    # ── DRY-RUN / SOMENTE-GERAR-FILA: nao abre browser ────────────────
    if args.dry_run or args.somente_gerar_fila:
        _imprimir_distribuicao(fila, municipios, max_por_consulta)
        print(f"\n  Pasta do run: {RUNS.pasta_run(run_id)}")
        print("  (dry-run — navegador nao aberto, Google Maps nao consultado)")
        return run_id

    # ── EXECUCAO REAL ────────────────────────────────────────────────
    grupos = resolver_grupo(args.grupo)
    # dedup global: reconstitui dos parciais + Supabase
    indexador = _reconstituir_dedup_parciais(run_id)
    try:
        chaves_sb = _carregar_chaves_supabase()
        if chaves_sb is not None:
            indexador.mesclar_chaves_existentes(chaves_sb)
            print(f"  Dedup: chaves Supabase pre-carregadas "
                  f"({len(chaves_sb['place_ids'])} place_ids, "
                  f"{len(chaves_sb['maps_urls'])} maps_urls)")
        else:
            print("  Dedup: Supabase nao configurado — dedup apenas intra-run/parciais")
    except Exception as e:
        # erro real de conexao/auth: NAO esconder
        print(f"❌ Erro ao carregar chaves do Supabase: {e}")
        raise

    limites = LIMITES.Limites(
        max_por_cidade=args.max_por_cidade,
        max_por_subnicho=args.max_por_subnicho,
        max_total=args.max_total,
    )
    motor = LIMITES.MotorLimites(limites=limites, contadores=LIMITES.ContadoresLimites())
    # no resume, reconta contadores a partir dos parciais aceitos
    if args.resume:
        for lead in RUNS.ler_leads_parciais(run_id):
            motor.contadores.registrar_aceito(lead.get("cidade", ""), lead.get("subnicho", ""))

    cp = RUNS.carregar_checkpoint(run_id) or RUNS.novo_checkpoint(run_id, len(fila))
    screenshot_dir = RUNS.caminhos_run(run_id)["screenshots"]

    # ── Lock global + lock por run ────────────────────────────────────
    # Pula lock em dry-run (nao abre browser) e quando LOCK_DISABLED=1
    if not (args.dry_run or args.somente_gerar_fila) \
            and os.environ.get("LOCK_DISABLED") != "1":
        from config.lock import LockGlobal, LockRun
        comando = f"mapear {run_id} {'resume' if args.resume else 'novo'}"
        with LockGlobal(run_id, comando=comando) as lock_global:
            if not lock_global.acquired:
                print("  Lock global nao adquirido — outra captacao ja esta ativa.")
                return run_id
            with LockRun(run_id, comando=comando) as lock_run:
                if not lock_run.acquired:
                    print(f"  Lock do run {run_id} nao adquirido — run ja sendo processado.")
                    return run_id
                await _executar_com_browser(run_id, fila, motor, indexador,
                                            args, escopo, max_por_consulta,
                                            screenshot_dir, dmin_inter, dmax_inter,
                                            cp, municipios, escopo_descritor)
    else:
        await _executar_com_browser(run_id, fila, motor, indexador,
                                    args, escopo, max_por_consulta,
                                    screenshot_dir, dmin_inter, dmax_inter,
                                    cp, municipios, escopo_descritor)

    # ── Exportacao final ─────────────────────────────────────────────
    _exportar_final(run_id, fila, municipios, escopo_descritor, args)
    return run_id


def _tarefa_atual(fila):
    """Id da tarefa em_andamento (para marcar interrompida)."""
    for item in fila:
        if item.status == FILA.STATUS_EM_ANDAMENTO:
            return item.id_tarefa
    return None


def _persistir_estado(run_id, fila, cp, item=None):
    """Atualiza checkpoint com contagens de status e salva fila+checkpoint atomicamente."""
    status_cont = FILA.contagem_por_status(fila)
    cp["concluidas"] = status_cont.get(FILA.STATUS_CONCLUIDA, 0)
    cp["pendentes"] = status_cont.get(FILA.STATUS_PENDENTE, 0)
    cp["em_andamento"] = status_cont.get(FILA.STATUS_EM_ANDAMENTO, 0)
    cp["erro"] = status_cont.get(FILA.STATUS_ERRO, 0)
    cp["interrompidas"] = status_cont.get(FILA.STATUS_INTERROMPIDA, 0)
    cp["ignoradas_limite"] = status_cont.get(FILA.STATUS_IGNORADA_LIMITE, 0)
    cp["atualizado_em"] = _agora_iso()
    cp["ultima_tarefa"] = item.id_tarefa if item else None
    RUNS.salvar_fila_run(run_id, fila)
    RUNS.salvar_checkpoint(run_id, cp)


async def _processar_fila(run_id, fila, motor, indexador, browser, context, page,
                          args, escopo, max_por_consulta, screenshot_dir,
                          dmin_inter, dmax_inter, cp):
    """Loop principal de execucao da fila. Pausa entre consultas aqui (nao em buscar_categoria).

    browser/context/page: objetos do Playwright. page pode ser atualizada
    internamente se for recriada apos fechamento (o chamador recebe a
    referencia atualizada via retorno).
    """
    for idx, item in enumerate(fila):
        if item.status not in FILA.STATUS_EXECUTAVEIS:
            continue  # concluida/interrompida/ignorada_limite nao repetem
        # erro ja esgotou tentativas -> nao retentativa no mesmo run
        if item.status == FILA.STATUS_ERRO \
                and (item.tentativas or 0) >= (args.max_tentativas or 3):
            continue

        # Verificacao de saude do navegador (a partir da segunda tarefa)
        if idx > 0:
            try:
                page, recriada = await _garantir_pagina_ativa(
                    browser, context, page
                )
                if recriada:
                    print("  ⚠ page recriada apos fechamento — repetindo tarefa")
            except NavegadorFechado:
                # Falha fatal — interrompe o run
                RUNS.salvar_estado_interrupcao(
                    run_id, fila, cp, item.id_tarefa,
                    "navegador ou contexto fechado inesperadamente"
                )
                print(f"\n  🛑 Navegador/contexto fechado — run interrompido")
                return

        pode, status = motor.pode_despachar(item)
        if not pode:
            item.status = status  # ignorada_limite
            if motor.total_atingido:
                motor.marcar_ignoradas_a_partir_de(fila, idx)
                _persistir_estado(run_id, fila, cp, item)
                print(f"  ⏸  max_total atingido — restantes marcadas ignorada_limite")
                return
            _persistir_estado(run_id, fila, cp, item)
            continue

        item.status = FILA.STATUS_EM_ANDAMENTO
        item.iniciado_em = _agora_iso()
        item.tentativas = (item.tentativas or 0) + 1
        _persistir_estado(run_id, fila, cp, item)
        print(f"\n  [{idx+1}/{len(fila)}] {item.subnicho_label} em {item.cidade}, {item.uf}")

        leads_aceitos = []
        try:
            resultados = await buscar_categoria(
                page, item.subnicho_label, item.cidade,
                start_index=0, progress=None, nomes_existentes=None,
                max_results=max_por_consulta, output_dir=None,
                subnicho=item.subnicho, query_term=item.query,
                max_tentativas=args.max_tentativas,
                screenshot_dir=str(screenshot_dir),
                captcha_detector=True,
                _run_id=run_id, _browser=browser, _context=context,
            )
            for lead in resultados:
                if motor.total_atingido:
                    break  # max_total atingido — nao aceita mais leads desta task
                _enriquecer_lead_geo(lead, item, escopo, run_id)
                if indexador.add(lead):
                    motor.registrar_aceito(item)
                    leads_aceitos.append(lead)
                    # verifica max_total apos cada aceito (limite por leads unicos)
                    if LIMITES.limite_total_atingido(motor.contadores, motor.limites):
                        motor.total_atingido = True
            if leads_aceitos:
                RUNS.anexar_linha_csv(run_id, leads_aceitos)
            item.captados = len(leads_aceitos)
            item.status = FILA.STATUS_CONCLUIDA
            item.concluido_em = _agora_iso()
            print(f"    ✓ {len(leads_aceitos)} leads unicos aceitos")
            _persistir_estado(run_id, fila, cp, item)
        except CaptchaDetectado as e:
            item.status = FILA.STATUS_INTERROMPIDA
            item.erro = f"captcha: {e}"
            _persistir_estado(run_id, fila, cp, item)
            raise
        except NavegadorFechado as e:
            # Falha fatal do navegador — interrompe o run
            RUNS.salvar_estado_interrupcao(
                run_id, fila, cp, item.id_tarefa,
                f"navegador ou contexto fechado inesperadamente: {e}"
            )
            print(f"\n  🛑 Navegador/contexto fechado — run interrompido")
            return
        except Exception as e:
            erro_str = str(e)
            # Verifica se o erro corresponde a navegador/context/page fechado
            if _eh_erro_navegador_fechado(erro_str):
                RUNS.salvar_estado_interrupcao(
                    run_id, fila, cp, item.id_tarefa,
                    f"navegador ou contexto fechado inesperadamente: {e}"
                )
                print(f"\n  🛑 Navegador/contexto fechado — run interrompido")
                return
            # Erro recuperavel — marca erro e continua
            item.status = FILA.STATUS_ERRO
            item.erro = erro_str[:200]
            RUNS.registrar_erro(run_id, {"id_tarefa": item.id_tarefa,
                                         "cidade": item.cidade,
                                         "subnicho": item.subnicho}, e)
            print(f"    X erro: {e}")
            _persistir_estado(run_id, fila, cp, item)
            # apos esgotar tentativas, segue para a proxima tarefa
            continue

        # Pausa entre consultas (responsabilidade do orquestrador, nao de buscar_categoria)
        await asyncio.sleep(random.uniform(dmin_inter, dmax_inter))


def _exportar_final(run_id, fila, municipios, escopo_descritor, args):
    """Gera arquivos finais: parciais xlsx, xlsx geo, resumo, checkpoint, log."""
    caminhos = RUNS.caminhos_run(run_id)
    leads = RUNS.ler_leads_parciais(run_id)
    # dedup final de seguranca (idempotente — parciais ja sao unicos)
    unicos = DEDUP.deduplicar_leads_global(leads)

    # leads_parciais.xlsx (raw, COLUNAS_CSV_GEO)
    _exportar_parciais_xlsx(unicos, caminhos["leads_xlsx"])

    # XLSX geografico agregado (COLUNAS_XLSX_AVGESTAO_GEO + auto_filter)
    grupos_keys = "_".join(g.key for g in resolver_grupo(args.grupo))
    xlsx_geo_nome = f"leads_{grupos_keys}_{escopo_descritor}_{run_id}.xlsx"
    xlsx_geo = _exportar_xlsx_geo(unicos, RUNS.pasta_run(run_id) / xlsx_geo_nome)
    if xlsx_geo:
        print(f"  XLSX geo: {xlsx_geo}")

    # checkpoint final
    cp = RUNS.carregar_checkpoint(run_id) or RUNS.novo_checkpoint(run_id, len(fila))
    status_cont = FILA.contagem_por_status(fila)
    # preserva status_run "interrompido" se houve interrupcao (captcha/ctrl+c)
    if cp.get("status_run") != "interrompido" \
            and status_cont.get(FILA.STATUS_INTERROMPIDA, 0) == 0:
        cp["status_run"] = "concluido"
    cp["atualizado_em"] = _agora_iso()
    cp["concluidas"] = status_cont.get(FILA.STATUS_CONCLUIDA, 0)
    cp["ignoradas_limite"] = status_cont.get(FILA.STATUS_IGNORADA_LIMITE, 0)
    cp["erro"] = status_cont.get(FILA.STATUS_ERRO, 0)
    cp["interrompidas"] = status_cont.get(FILA.STATUS_INTERROMPIDA, 0)
    cp["captados_total"] = len(unicos)
    RUNS.salvar_checkpoint(run_id, cp)

    # resumo.json
    dist = FILA.distribuicao_estimada(fila, args.max_por_consulta or args.max or 20)
    resumo = {
        "run_id": run_id,
        "concluido_em": _agora_iso(),
        "status_run": cp["status_run"],
        "total_tarefas": len(fila),
        "concluidas": cp["concluidas"],
        "ignoradas_limite": cp["ignoradas_limite"],
        "erro": cp["erro"],
        "interrompidas": cp["interrompidas"],
        "captados_total": len(unicos),
        "brutos": len(leads),
        "unicos": len(unicos),
        "duplicatas_removidas": max(0, len(leads) - len(unicos)),
        "por_grupo": dist["por_grupo"],
        "por_subnicho": dist["por_subnicho"],
        "por_uf": dist["por_uf"],
        "por_regiao": dist["por_regiao"],
        "arquivos": {
            "config": str(caminhos["config"]),
            "fila": str(caminhos["fila"]),
            "checkpoint": str(caminhos["checkpoint"]),
            "leads_csv": str(caminhos["leads_csv"]),
            "leads_xlsx": str(caminhos["leads_xlsx"]),
            "xlsx_geo": str(xlsx_geo) if xlsx_geo else "",
            "erros": str(caminhos["erros"]),
            "log": str(caminhos["log"]),
        },
    }
    RUNS.salvar_resumo(run_id, resumo)

    # execucao.log (minimal)
    try:
        with open(caminhos["log"], "w", encoding="utf-8") as f:
            f.write(f"Run {run_id}\n")
            f.write(f"Concluido em: {resumo['concluido_em']}\n")
            f.write(f"Tarefas: {len(fila)} | concluidas: {cp['concluidas']} | "
                    f"ignoradas_limite: {cp['ignoradas_limite']} | erro: {cp['erro']}\n")
            f.write(f"Leads unicos: {len(unicos)} (brutos: {len(leads)})\n")
    except Exception:
        pass

    print(f"\n  RESUMO FINAL — run {run_id}")
    print(f"    Tarefas: {len(fila)} | concluidas: {cp['concluidas']} | "
          f"ignoradas_limite: {cp['ignoradas_limite']} | erro: {cp['erro']}")
    print(f"    Leads unicos: {len(unicos)} (brutos: {len(leads)})")
    print(f"    Pasta: {RUNS.pasta_run(run_id)}")


if __name__ == "__main__":
    asyncio.run(main())
