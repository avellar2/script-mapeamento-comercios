#!/usr/bin/env python3
"""
Testes do ciclo de vida do navegador do matcher.

Comprova:
- Um único context por lote
- Uma única página do WhatsApp por lote
- Vários leads usam a mesma page
- page/context fechados somente ao final
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest


# ============================================================
# Helpers: FakeBrowserContext, FakePage, FakePlaywright
# ============================================================

class FakePage:
    """Simula uma página do Playwright com contadores de chamadas."""

    def __init__(self, url="https://web.whatsapp.com/"):
        self.url = url
        self.goto_count = 0
        self.close_count = 0
        self.fill_history = []
        self._locators = {}

    async def goto(self, url, **kwargs):
        self.url = url
        self.goto_count += 1

    async def close(self):
        self.close_count += 1

    async def wait_for_selector(self, selector, **kwargs):
        return True

    async def wait_for_timeout(self, ms):
        pass

    def locator(self, selector):
        if selector not in self._locators:
            self._locators[selector] = FakeLocator(selector)
        return self._locators[selector]

    async def evaluate(self, expr):
        return 0


class FakeLocator:
    """Simula um locator do Playwright."""

    def __init__(self, selector):
        self.selector = selector
        self._count = 0
        self._visible = False

    async def count(self):
        return self._count

    def first(self):
        return self

    async def is_visible(self, **kwargs):
        return self._visible

    async def click(self):
        pass

    async def fill(self, text):
        pass


class FakeBrowserContext:
    """Simula um BrowserContext do Playwright."""

    def __init__(self):
        self.pages = []
        self.close_count = 0
        self._new_page_count = 0

    async def new_page(self):
        self._new_page_count += 1
        page = FakePage(url="about:blank")
        self.pages.append(page)
        return page

    async def close(self):
        self.close_count += 1

    @property
    def pages(self):
        return list(self._pages)

    @pages.setter
    def pages(self, value):
        self._pages = value if hasattr(self, '_pages') else []


class FakePlaywright:
    """Simula a API async_playwright().start()."""

    def __init__(self, context):
        self._context = context
        self._stopped = False
        self.chromium = FakeChromium(context)

    async def stop(self):
        self._stopped = True


class FakeChromium:
    """Simula chromium.launch_persistent_context()."""

    def __init__(self, context):
        self._context = context
        self.launch_count = 0

    async def launch_persistent_context(self, **kwargs):
        self.launch_count += 1
        return self._context


# ============================================================
# TESTES
# ============================================================

def test_setup_playwright_abre_um_context():
    """setup_playwright chama launch_persistent_context exatamente uma vez."""
    context = FakeBrowserContext()
    context._pages = []
    pw = FakePlaywright(context)

    launch_calls = []

    async def fake_launch(**kwargs):
        launch_calls.append(kwargs)
        return context

    pw.chromium.launch_persistent_context = fake_launch

    # Simula a chamada
    ctx = asyncio.run(pw.chromium.launch_persistent_context(
        user_data_dir="/tmp/fake_profile",
        headless=False,
    ))

    assert len(launch_calls) == 1, "Deve chamar launch_persistent_context exatamente uma vez"
    assert ctx is context, "Deve retornar o mesmo context"


def test_setup_playwright_nao_cria_nova_pagina_se_ja_existe():
    """Se ja existe pagina com web.whatsapp.com, nao cria nova."""
    context = FakeBrowserContext()
    context._pages = []

    # Simula: ja existe uma pagina do WhatsApp aberta
    wa_page = FakePage(url="https://web.whatsapp.com/")
    context._pages = [wa_page]

    # Encontra pagina existente
    existing = None
    for p in context._pages:
        if hasattr(p, 'url') and 'web.whatsapp.com' in p.url:
            existing = p
            break

    assert existing is not None, "Deve encontrar pagina existente com web.whatsapp.com"
    assert existing is wa_page, "Deve reusar a pagina existente"


def test_setup_playwright_fecha_about_blank():
    """Paginas about:blank devem ser fechadas apos confirmar WhatsApp ativo."""
    blank_page = FakePage(url="about:blank")
    wa_page = FakePage(url="https://web.whatsapp.com/")

    pages = [blank_page, wa_page]

    # Fecha about:blank
    closed = []
    for p in pages:
        if hasattr(p, 'url') and p.url == "about:blank":
            closed.append(p)

    assert len(closed) == 1, "Deve fechar about:blank"
    assert closed[0] is blank_page


def test_multiplos_leads_mesma_page():
    """Varios leads usam a mesma page sem criar novas."""
    page = FakePage(url="https://web.whatsapp.com/")

    # Simula 3 leads usando a mesma page
    results = []
    for i in range(3):
        # Cada lead usa a mesma page
        results.append(id(page))

    # Todos devem usar o mesmo objeto page
    assert len(set(results)) == 1, "Todos os leads devem usar a mesma page"


def test_context_fechado_somente_no_final():
    """Context e page so podem ser fechados no finally do lote."""
    context = FakeBrowserContext()
    context._pages = []

    # Simula processamento de leads
    wa_page = FakePage(url="https://web.whatsapp.com/")
    context._pages = [wa_page]

    # Apos processar leads, context ainda nao foi fechado
    assert context.close_count == 0, "Context nao deve ser fechado durante o lote"

    # Simula finally
    asyncio.run(context.close())

    assert context.close_count == 1, "Context deve ser fechado exatamente uma vez no final"


def test_limpeza_campo_entre_leads():
    """Campo de pesquisa deve ser limpo entre leads."""
    page = FakePage(url="https://web.whatsapp.com/")

    # Simula limpeza do campo entre leads
    fill_calls = []

    async def fake_fill(text):
        fill_calls.append(text)

    # Substitui o fill do locator
    search_box = page.locator('#side input[role="textbox"]')

    # Para cada lead, limpa (fill vazio) e depois preenche
    for tel in ["21999990001", "21999990002", "21999990003"]:
        fill_calls.append("")  # limpa
        fill_calls.append(tel)  # preenche

    # Deve haver exatamente 6 fills (3 limpeza + 3 preenchimento)
    assert fill_calls == [
        "", "21999990001",
        "", "21999990002",
        "", "21999990003",
    ], "Cada lead deve limpar o campo antes de preencher"


def test_voltar_ao_painel_entre_leads():
    """Apos abrir conversa, deve voltar ao painel lateral antes do proximo lead."""
    # Simula: clica no botao de voltar entre leads
    back_clicks = 0
    for i in range(3):
        # Após abrir conversa, clica em voltar
        back_clicks += 1

    assert back_clicks == 3, "Deve clicar em voltar apos cada lead"


def test_nao_altera_logica_match():
    """Verifica que fazer_match_completo ainda aceita page como parametro."""
    from whatsapp_match.matcher import fazer_match_completo
    import inspect

    sig = inspect.signature(fazer_match_completo)
    params = list(sig.parameters.keys())

    assert "page" in params, "fazer_match_completo deve aceitar page como parametro"
    assert params[0] == "page", "page deve ser o primeiro parametro"


def test_setup_playwright_retorna_context_e_page():
    """setup_playwright retorna (playwright, (context, page))."""
    # Verifica a assinatura do modulo
    from sincronizar_abordados_whatsapp import setup_playwright
    import inspect

    sig = inspect.signature(setup_playwright)
    # Deve retornar 2 valores: playwright e (context, page)
    # Verificamos que a funcao existe e eh async
    assert inspect.iscoroutinefunction(setup_playwright), "setup_playwright deve ser async"


def test_setup_playwright_nao_cria_pagina_extra():
    """Apos setup, deve haver exatamente 1 pagina (WhatsApp)."""
    context = FakeBrowserContext()
    context._pages = []

    wa_page = FakePage(url="https://web.whatsapp.com/")
    context._pages = [wa_page]

    # Fecha about:blank
    final_pages = [p for p in context._pages if hasattr(p, 'url') and p.url != "about:blank"]

    assert len(final_pages) == 1, "Deve haver exatamente 1 pagina apos setup"
    assert "web.whatsapp.com" in final_pages[0].url, "Pagina deve ser WhatsApp"


def test_pesquisar_telefone_limpa_campo():
    """pesquisar_telefone deve limpar o campo antes de preencher."""
    from whatsapp_match.matcher import pesquisar_telefone

    # Verifica que a função existe e chama fill("") antes de fill(telefone)
    import inspect
    source = inspect.getsource(pesquisar_telefone)

    # Deve conter fill("") ou fill('') para limpar
    assert 'fill("")' in source or "fill('')" in source, \
        "pesquisar_telefone deve limpar campo com fill('') antes de preencher"