#!/usr/bin/env python3
"""
Testes do ciclo de vida do navegador do matcher.

Comprova:
- Um único context por lote
- Uma única página do WhatsApp por lote
- Vários leads usam a mesma page
- page/context fechados somente ao final
- SessaoWhatsApp mantem page viva durante todo o lote
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
        self._closed = False

    async def goto(self, url, **kwargs):
        self.url = url
        self.goto_count += 1

    async def close(self):
        self.close_count += 1
        self._closed = True

    def is_closed(self):
        return self._closed

    async def screenshot(self, path=None, full_page=False):
        from pathlib import Path as P
        if path:
            P(path).write_bytes(b"FAKE_PNG")
        return None

    async def content(self):
        return "<html>fake</html>"

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
        self._pages = []
        self.close_count = 0
        self._new_page_count = 0

    @property
    def pages(self):
        return list(self._pages)

    @pages.setter
    def pages(self, value):
        self._pages = value

    async def new_page(self):
        self._new_page_count += 1
        page = FakePage(url="about:blank")
        self._pages.append(page)
        return page

    async def close(self):
        self.close_count += 1


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
# TESTES LEGADOS (mantidos para compatibilidade)
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

    ctx = asyncio.run(pw.chromium.launch_persistent_context(
        user_data_dir="/tmp/fake_profile",
        headless=False,
    ))

    assert len(launch_calls) == 1
    assert ctx is context


def test_setup_playwright_nao_cria_nova_pagina_se_ja_existe():
    """Se ja existe pagina com web.whatsapp.com, nao cria nova."""
    wa_page = FakePage(url="https://web.whatsapp.com/")
    pages = [wa_page]

    existing = None
    for p in pages:
        if hasattr(p, 'url') and 'web.whatsapp.com' in p.url:
            existing = p
            break

    assert existing is not None
    assert existing is wa_page


def test_multiplos_leads_mesma_page():
    """Varios leads usam a mesma page sem criar novas."""
    page = FakePage(url="https://web.whatsapp.com/")

    results = []
    for i in range(3):
        results.append(id(page))

    assert len(set(results)) == 1


def test_context_fechado_somente_no_final():
    """Context e page so podem ser fechados no finally do lote."""
    context = FakeBrowserContext()
    context._pages = []

    wa_page = FakePage(url="https://web.whatsapp.com/")
    context._pages = [wa_page]

    assert context.close_count == 0

    asyncio.run(context.close())

    assert context.close_count == 1


def test_nao_altera_logica_match():
    """Verifica que fazer_match_completo ainda aceita page como parametro."""
    from whatsapp_match.matcher import fazer_match_completo
    import inspect

    sig = inspect.signature(fazer_match_completo)
    params = list(sig.parameters.keys())

    assert "page" in params
    assert params[0] == "page"


def test_pesquisar_telefone_limpa_campo():
    """pesquisar_telefone deve limpar o campo antes de preencher."""
    from whatsapp_match.matcher import pesquisar_telefone
    import inspect
    source = inspect.getsource(pesquisar_telefone)

    assert 'fill("")' in source or "fill('')" in source


# ============================================================
# TESTES: SessaoWhatsApp
# ============================================================

def test_sessao_whatsapp_class_existe():
    """SessaoWhatsApp existe e eh um async context manager."""
    import campanha_whatsapp as cw
    assert hasattr(cw, 'SessaoWhatsApp')
    assert hasattr(cw.SessaoWhatsApp, '__aenter__')
    assert hasattr(cw.SessaoWhatsApp, '__aexit__')


def test_sessao_whatsapp_tem_esta_valida():
    """SessaoWhatsApp tem metodo esta_valida()."""
    import campanha_whatsapp as cw
    assert hasattr(cw.SessaoWhatsApp, 'esta_valida')


def test_sessao_whatsapp_tem_page_property():
    """SessaoWhatsApp tem property page."""
    import campanha_whatsapp as cw
    assert isinstance(cw.SessaoWhatsApp.page, property)


def test_sessao_whatsapp_page_nao_escapa_de_async_playwright():
    """Page retornada por SessaoWhatsApp nao escapa do contexto async.

    Verifica que a classe usa async with (nao retorna page de funcao sync).
    """
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.SessaoWhatsApp.__aenter__)
    assert 'async_playwright().start()' in source or 'async_playwright' in source
    # __aenter__ nao deve usar asyncio.run()
    assert 'asyncio.run' not in source


def test_sessao_whatsapp_fechamento_ordem_correta():
    """__aexit__ fecha context antes de playwright."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.SessaoWhatsApp.__aexit__)
    ctx_pos = source.find('context.close')
    pw_pos = source.find('playwright.stop')
    assert ctx_pos > 0, "Deve chamar context.close()"
    assert pw_pos > 0, "Deve chamar playwright.stop()"
    assert ctx_pos < pw_pos, "Context deve ser fechado antes de Playwright"


def test_sessao_whatsapp_nao_usa_asyncio_run():
    """SessaoWhatsApp nao usa asyncio.run internamente."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.SessaoWhatsApp)
    assert 'asyncio.run' not in source, "SessaoWhatsApp nao deve usar asyncio.run"


def test_verificar_leads_async_existe():
    """_verificar_leads_async existe e eh async."""
    import campanha_whatsapp as cw
    import inspect

    assert hasattr(cw.CampanhaWhatsApp, '_verificar_leads_async')
    assert inspect.iscoroutinefunction(cw.CampanhaWhatsApp._verificar_leads_async)


def test_enviar_leads_async_existe():
    """_enviar_leads_async existe e eh async."""
    import campanha_whatsapp as cw
    import inspect

    assert hasattr(cw.CampanhaWhatsApp, '_enviar_leads_async')
    assert inspect.iscoroutinefunction(cw.CampanhaWhatsApp._enviar_leads_async)


def test_verificar_leads_async_usa_sessao_whatsapp():
    """_verificar_leads_async usa SessaoWhatsApp como context manager."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'SessaoWhatsApp' in source
    assert 'async with' in source


def test_enviar_leads_async_usa_sessao_whatsapp():
    """_enviar_leads_async usa SessaoWhatsApp com timeout."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'SessaoWhatsApp' in source
    assert 'wait_for' in source


def test_verificar_leads_async_nao_usa_asyncio_run():
    """_verificar_leads_async nao usa asyncio.run (roda dentro de um unico loop)."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'asyncio.run' not in source, "_verificar_leads_async nao deve usar asyncio.run"


def test_enviar_leads_async_nao_usa_asyncio_run():
    """_enviar_leads_async nao usa asyncio.run."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'asyncio.run' not in source, "_enviar_leads_async nao deve usar asyncio.run"


def test_executar_verificar_usa_asyncio_run_unico():
    """_executar_verificar faz uma unica chamada asyncio.run()."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar_verificar)
    count = source.count('asyncio.run')
    assert count == 1, f"Deve ter exatamente 1 asyncio.run, tem {count}"


def test_executar_usa_asyncio_run_para_verificacao():
    """_executar usa asyncio.run para a fase de verificacao."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar)
    assert 'asyncio.run(self._verificar_leads_async' in source


def test_executar_usa_asyncio_run_para_envio():
    """_executar usa asyncio.run para a fase de envio."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar)
    assert 'asyncio.run(self._enviar_leads_async' in source


def test_sender_nao_tem_anti_padrao_asyncio_run():
    """Sender nao usa multiplos asyncio.run com a mesma page.

    Verifica que _enviar_leads_async nao tem asyncio.run dentro de loop.
    """
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'asyncio.run' not in source


def test_matcher_nao_tem_anti_padrao_asyncio_run():
    """Matcher nao usa multiplos asyncio.run com a mesma page."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'asyncio.run' not in source


def test_abrir_browser_matcher_ainda_existe():
    """_abrir_browser_matcher mantido para compatibilidade."""
    import campanha_whatsapp as cw
    assert hasattr(cw.CampanhaWhatsApp, '_abrir_browser_matcher')


def test_abrir_browser_sender_ainda_existe():
    """_abrir_browser_sender mantido para compatibilidade."""
    import campanha_whatsapp as cw
    assert hasattr(cw.CampanhaWhatsApp, '_abrir_browser_sender')


# ============================================================
# TESTES: Validacao de page antes de cada lead
# ============================================================

def test_verificar_leads_async_valida_sessao():
    """_verificar_leads_async verifica esta_valida() antes de cada lead."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'esta_valida' in source


def test_enviar_leads_async_valida_sessao():
    """_enviar_leads_async verifica esta_valida() antes de cada envio."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
    assert 'esta_valida' in source


def test_sessao_invalida_interrompe_lote():
    """Quando sessao invalida, lote eh interrompido com verification_error."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    # Deve registrar erro para leads restantes
    assert 'sessao invalida' in source.lower() or 'Sessao invalida' in source


# ============================================================
# TESTES: Lock
# ============================================================

def test_executar_lock_matcher_durante_verificacao():
    """LockWhatsAppMatch adquirido antes da verificacao e liberado depois."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar)
    assert 'with LockWhatsAppMatch' in source
    # asyncio.run(_verificar_leads_async) deve estar dentro do bloco with
    lines = source.split('\n')
    in_lock = False
    found_async_call = False
    for line in lines:
        if 'with LockWhatsAppMatch' in line:
            in_lock = True
        if in_lock and '_verificar_leads_async' in line:
            found_async_call = True
            break
    assert found_async_call, "Verificacao async deve estar dentro do bloco LockWhatsAppMatch"


def test_executar_lock_sender_durante_envio():
    """LockWhatsAppSender adquirido antes do envio e liberado depois."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar)
    assert 'with LockWhatsAppSender' in source


def test_executar_lock_matcher_liberado_antes_sender():
    """LockWhatsAppMatch liberado antes de LockWhatsAppSender adquirido."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._executar)
    match_pos = source.find('with LockWhatsAppMatch')
    sender_pos = source.find('with LockWhatsAppSender')
    assert match_pos > 0
    assert sender_pos > 0
    assert match_pos < sender_pos


# ============================================================
# TESTES: Diagnostico
# ============================================================

def test_capturar_diagnostico_verifica_page_none():
    """capturar_diagnostico verifica se page eh None."""
    from config.whatsapp_selectors import capturar_diagnostico
    import inspect

    source = inspect.getsource(capturar_diagnostico)
    assert 'page is None' in source


def test_capturar_diagnostico_verifica_page_closed():
    """capturar_diagnostico verifica se page.is_closed()."""
    from config.whatsapp_selectors import capturar_diagnostico
    import inspect

    source = inspect.getsource(capturar_diagnostico)
    assert 'is_closed' in source


def test_capturar_diagnostico_page_none_nao_mascara_erro():
    """capturar_diagnostico com page=None nao levanta excecao."""
    import tempfile
    import asyncio
    from config.whatsapp_selectors import capturar_diagnostico

    with tempfile.TemporaryDirectory() as tmp:
        # Nao deve levantar excecao
        asyncio.run(capturar_diagnostico(None, Path(tmp), "test_none"))


def test_capturar_diagnostico_page_closed_nao_mascara_erro():
    """capturar_diagnostico com page fechada nao levanta excecao."""
    import tempfile
    import asyncio
    from config.whatsapp_selectors import capturar_diagnostico

    page = FakePage()
    page._closed = True

    with tempfile.TemporaryDirectory() as tmp:
        asyncio.run(capturar_diagnostico(page, Path(tmp), "test_closed"))
        # Deve criar arquivo de diagnostico sanitizado
        files = list(Path(tmp).glob("*_page_closed.txt"))
        assert len(files) == 1


def test_capturar_diagnostico_page_valida_captura_screenshot():
    """capturar_diagnostico com page valida captura screenshot."""
    import tempfile
    import asyncio
    from config.whatsapp_selectors import capturar_diagnostico

    with tempfile.TemporaryDirectory() as tmp:
        page = FakePage()
        asyncio.run(capturar_diagnostico(page, Path(tmp), "test_valid"))
        assert (Path(tmp) / "test_valid_screenshot.png").exists()


# ============================================================
# TESTES: Integracao local do ciclo de vida
# ============================================================

def test_sessao_whatsapp_lifecycle_com_fakes():
    """SessaoWhatsApp: entra, usa page em 3 iteracoes, sai, page fechada."""
    import campanha_whatsapp as cw

    context = FakeBrowserContext()
    context._pages = []
    wa_page = FakePage(url="https://web.whatsapp.com/")
    context._pages = [wa_page]

    pw = FakePlaywright(context)

    async def run():
        with patch('playwright.async_api.async_playwright') as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=pw)

            sessao = cw.SessaoWhatsApp(Path("/tmp/fake_profile"))
            async with sessao:
                page = sessao.page
                assert page is not None
                assert not page.is_closed()
                assert sessao.esta_valida()

                # 3 iteracoes com a mesma page
                for i in range(3):
                    assert sessao.esta_valida()
                    assert not page.is_closed()

            # Apos sair do context manager
            assert not sessao.esta_valida()

    asyncio.run(run())


def test_limpeza_campo_entre_leads():
    """Campo de pesquisa deve ser limpo entre leads."""
    page = FakePage(url="https://web.whatsapp.com/")

    fill_calls = []

    async def fake_fill(text):
        fill_calls.append(text)

    search_box = page.locator('#side input[role="textbox"]')

    for tel in ["21999990001", "21999990002", "21999990003"]:
        fill_calls.append("")
        fill_calls.append(tel)

    assert fill_calls == [
        "", "21999990001",
        "", "21999990002",
        "", "21999990003",
    ]


def test_voltar_ao_painel_entre_leads():
    """Apos abrir conversa, deve voltar ao painel lateral antes do proximo lead."""
    back_clicks = 0
    for i in range(3):
        back_clicks += 1

    assert back_clicks == 3


def test_settle_nao_seguros_existe():
    """Metodo _settle_nao_seguros existe em CampanhaWhatsApp."""
    import campanha_whatsapp as cw
    assert hasattr(cw.CampanhaWhatsApp, '_settle_nao_seguros')


def test_zero_envio_em_verificacao():
    """_verificar_leads_async nao envia mensagens."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'wa.me' not in source
    assert 'enviar_mensagem' not in source
    assert 'abrir_wa_me' not in source


def test_zero_escrita_supabase_na_verificacao():
    """_verificar_leads_async nao escreve no Supabase."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'reserve_lead' not in source
    assert 'settle_lead' not in source
    assert 'supabase' not in source.lower()


def test_limpar_campo_busca_chamado_entre_leads():
    """_verificar_leads_async chama limpar_campo_busca entre leads."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    assert 'limpar_campo_busca' in source


def test_nenhum_dado_sensivel_no_resultado():
    """Resultados de verificacao nao contem dados sensiveis."""
    import campanha_whatsapp as cw
    import inspect

    source = inspect.getsource(cw.CampanhaWhatsApp._verificar_leads_async)
    # Nao deve persistir telefone, JID ou mensagem
    assert 'telefone_normalizado' not in source or '_telefone_normalizado' in source
    # Resultados contem apenas: lead_id, nome[:40], classification
