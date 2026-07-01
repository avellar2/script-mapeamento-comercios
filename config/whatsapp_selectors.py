"""
config/whatsapp_selectors.py — Seletores centralizados do WhatsApp Web.

O DOM do WhatsApp Web muda com frequência. Este módulo centraliza todos os
seletores com fallbacks, timeouts controlados e helpers de diagnóstico
(screenshot + snapshot HTML em caso de falha).

NÃO espalhar seletores diretamente pelo código dos scripts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# SELEÇÃO DE CHAT / PESQUISA
# ============================================================

# Campo de pesquisa do WhatsApp Web
SEARCH_BOX_SELECTORS = [
    'div[contenteditable="true"][data-tab="3"]',
    'div[contenteditable="true"][title*="pesquisar" i]',
    'div[contenteditable="true"][title*="search" i]',
    'div[contenteditable="true"][spellcheck="true"]',
]

# Resultado da pesquisa (chat list item)
CHAT_LIST_SELECTORS = [
    'div[data-testid="chat-list"]',
    'div[aria-label*="lista de conversas" i]',
    'div[aria-label*="chat list" i]',
    'div[role="region"] >> xpath=./div[contains(@class,"copyable-area")]',
]

# Item individual na lista de chats
CHAT_ITEM_SELECTORS = [
    'div[data-testid="chat-list-item"]',
    'div[role="row"][tabindex="-1"]',
    'div[aria-selected="false"]',
]

# ============================================================
# CABEÇALHO DA CONVERSA
# ============================================================

# Nome do contato no header
CONTACT_NAME_SELECTORS = [
    'span[data-testid="conversation-info-header-chat-title"]',
    'header div[data-testid="conversation-header"] span[title]',
    'div[data-testid="conversation-header"] span[dir="auto"]',
]

# Header da conversa (para clicar e abrir info)
CONVERSATION_HEADER_SELECTORS = [
    'div[data-testid="conversation-header"]',
    'header[data-testid="conversation-header"]',
    'header div[role="button"]',
]

# ============================================================
# PAINEL DE INFORMAÇÕES DO CONTATO
# ============================================================

INFO_PANEL_SELECTORS = [
    'div[data-testid="info-panel"]',
    'div[aria-label*="informações do contato" i]',
    'div[aria-label*="contact info" i]',
]

# Telefone no painel de informações
PHONE_IN_PROFILE_SELECTORS = [
    'div[data-testid="info-panel"] span[title*="+"]',
    'div[data-testid="panel-header-title"] span[title*="+"]',
    'span[title*="+55"]',
    'span[title*="+"]',
]

# ============================================================
# MENSAGENS
# ============================================================

# Mensagens enviadas (bolha de saída)
MESSAGE_OUT_SELECTORS = [
    'div[data-testid="conversation-panel-messages"] div[data-testid*="out"]',
    'div.message-out',
    'div[class*="message-out"]',
    'div[data-testid*="out"]',
]

# Mensagens recebidas (bolha de entrada)
MESSAGE_IN_SELECTORS = [
    'div[data-testid="conversation-panel-messages"] div[data-testid*="in"]',
    'div.message-in',
    'div[class*="message-in"]',
    'div[data-testid*="in"]',
]

# Texto dentro de uma bolha de mensagem
MESSAGE_TEXT_SELECTORS = [
    'span.selectable-text.copyable-text',
    'span[dir="auto"]',
    'div.copyable-text',
]

# ============================================================
# BOTÃO DE VOLTAR
# ============================================================

BACK_BUTTON_SELECTORS = [
    'button[aria-label*="voltar" i]',
    'button[aria-label*="back" i]',
    'div[data-testid="btn-back"]',
    'div[role="button"][aria-label*="voltar" i]',
]

# ============================================================
# CARREGAMENTO / LOADING
# ============================================================

LOADING_INDICATORS = [
    'div[data-testid="conversation-loading"]',
    'div[role="progressbar"]',
    'div[aria-label*="carregando" i]',
    'div[aria-label*="loading" i]',
]

# ============================================================
# DETECÇÃO DE GRUPO / CANAL / COMUNIDADE
# ============================================================

GROUP_INDICATORS = [
    'div[data-testid="group-icon"]',
    'div[data-testid="community-icon"]',
    'div[data-testid="channel-icon"]',
    'span[data-testid="icon-group"]',
    'span[data-testid="icon-community"]',
    'span[data-testid="icon-channel"]',
]

# ============================================================
# QR CODE (tela de login)
# ============================================================

QR_CODE_SELECTORS = [
    'canvas[aria-label*="escaneie" i]',
    'canvas[aria-label*="scan" i]',
    'div[data-testid="qrcode"]',
    'div[data-ref]',
]

# ============================================================
# HELPERS
# ============================================================

TIMEOUT_PADRAO = 30000  # 30s
TIMEOUT_CURTO = 5000    # 5s
TIMEOUT_QR = 240000     # 4 min


async def encontrar_seletor(page, selectors: list[str], timeout: int = TIMEOUT_CURTO) -> Optional[str]:
    """
    Tenta cada seletor da lista até encontrar um que corresponda a um elemento.

    Args:
        page: Página do Playwright
        selectors: Lista de seletores CSS/XPath
        timeout: Timeout por tentativa em ms

    Returns:
        O primeiro seletor que encontrou um elemento, ou None
    """
    for selector in selectors:
        try:
            el = await page.wait_for_selector(selector, timeout=timeout)
            if el:
                return selector
        except Exception:
            continue
    return None


async def capturar_diagnostico(page, caminho: Path, prefixo: str = "erro") -> None:
    """
    Captura screenshot + snapshot HTML para diagnóstico de falha.

    Args:
        page: Página do Playwright
        caminho: Diretório para salvar os arquivos
        prefixo: Prefixo do nome do arquivo
    """
    caminho = Path(caminho)
    caminho.mkdir(parents=True, exist_ok=True)

    try:
        # Screenshot
        screenshot_path = caminho / f"{prefixo}_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info("Screenshot salvo: %s", screenshot_path)
    except Exception as e:
        logger.warning("Erro ao capturar screenshot: %s", e)

    try:
        # Snapshot HTML (limitado a 500KB para não sobrecarregar)
        html = await page.content()
        if len(html) > 500_000:
            html = html[:500_000] + "\n<!-- TRUNCADO -->\n"
        html_path = caminho / f"{prefixo}_snapshot.html"
        html_path.write_text(html, encoding="utf-8")
        logger.info("Snapshot HTML salvo: %s", html_path)
    except Exception as e:
        logger.warning("Erro ao capturar snapshot: %s", e)
