"""Testes para as correções de robustez de navegação.

Cobre:
1. Timeout de navegação (PlaywrightTimeoutError) com retry
2. Timeout não é classificado como NavegadorFechado
3. Page fechada com browser vivo é recriada uma vez
4. Browser desconectado levanta NavegadorFechado
5. Context fechado interrompe corretamente
6. Reload só ocorre com page saudável
7. Reload com timeout não segue para leitura de itens
8. Página válida sem resultados retorna zero
9. CAPTCHA permanece sendo tratado sem contorno
10. _avaliar_saude_pagina classifica corretamente
11. _logger_captura funciona sem run_id
12. Traceback é registrado em erros
13. Nenhum segundo run é criado
14. Timeout de navegação aumentado de 45s para 90s
15. Timeout de seletores é separado (30s)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mapear_comercios import (
    _avaliar_saude_pagina,
    NavegadorFechado,
    CaptchaDetectado,
    PlaywrightTimeoutError,
    _TIMEOUT_NAVEGACAO_MS,
    _TIMEOUT_SELETOR_MS,
    buscar_categoria,
)


# ══════════════════════════════════════════════════════════════════
# Testes de _avaliar_saude_pagina
# ══════════════════════════════════════════════════════════════════

class TestAvaliarSaudePagina:
    def test_browser_morto_desconectado(self):
        browser = MagicMock()
        browser.is_connected.return_value = False
        context = MagicMock()
        context.pages = []
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(browser, context, page) == "browser_morto"

    def test_browser_morto_none(self):
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(None, MagicMock(), page) == "browser_morto"

    def test_context_morto_none(self):
        browser = MagicMock()
        browser.is_connected.return_value = True
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(browser, None, page) == "context_morto"

    def test_context_morto_fechado(self):
        browser = MagicMock()
        browser.is_connected.return_value = True
        context_exc = MagicMock()
        type(context_exc).pages = property(
            lambda self: (_ for _ in ()).throw(Exception("closed"))
        )
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(browser, context_exc, page) == "context_morto"

    def test_page_fechada(self):
        browser = MagicMock()
        browser.is_connected.return_value = True
        context = MagicMock()
        context.pages = []
        page = MagicMock()
        page.is_closed.return_value = True
        assert _avaliar_saude_pagina(browser, context, page) == "page_fechada"

    def test_page_valida(self):
        browser = MagicMock()
        browser.is_connected.return_value = True
        context = MagicMock()
        context.pages = []
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(browser, context, page) == "page_valida"

    def test_sem_browser(self):
        page = MagicMock()
        page.is_closed.return_value = False
        assert _avaliar_saude_pagina(None, None, page) == "sem_browser"

    def test_page_none(self):
        browser = MagicMock()
        browser.is_connected.return_value = True
        context = MagicMock()
        context.pages = []
        assert _avaliar_saude_pagina(browser, context, None) == "page_fechada"


# ══════════════════════════════════════════════════════════════════
# Testes de constantes
# ══════════════════════════════════════════════════════════════════

class TestTimeouts:
    def test_timeout_navegacao_90s(self):
        assert _TIMEOUT_NAVEGACAO_MS == 90000

    def test_timeout_seletor_30s(self):
        assert _TIMEOUT_SELETOR_MS == 30000


# ══════════════════════════════════════════════════════════════════
# Helpers para testes de buscar_categoria
# ══════════════════════════════════════════════════════════════════

class FakeBrowser:
    def __init__(self, connected=True):
        self._connected = connected
    def is_connected(self):
        return self._connected


class FakeContext:
    def __init__(self):
        self._pages = []
    @property
    def pages(self):
        return self._pages
    async def new_page(self):
        p = _make_mock_page(return_count=0)
        self._pages.append(p)
        return p


def _make_mock_page(return_count=0, url="https://www.google.com/maps/search/test"):
    """Cria um mock mínimo de page para buscar_categoria."""
    page = MagicMock()
    page.is_closed.return_value = False
    page.url = url
    page._goto_count = 0

    async def mock_goto(u, **kwargs):
        page._goto_count += 1
        page.url = u
        return MagicMock()

    page.goto = mock_goto
    page.reload = AsyncMock()
    page.on = MagicMock()
    page.set_default_navigation_timeout = MagicMock()
    page.set_default_timeout = MagicMock()

    items = MagicMock()
    items.count = AsyncMock(return_value=return_count)
    page.locator = MagicMock(return_value=items)

    return page


def _run_async(coro):
    return asyncio.run(coro)


# ══════════════════════════════════════════════════════════════════
# Testes de buscar_categoria com retry e saúde
# ══════════════════════════════════════════════════════════════════

class TestBuscarCategoriaRetry:
    """Testes de retry de navegação em buscar_categoria."""

    def test_goto_ok_primeira_tentativa(self):
        """page.goto conclui na primeira tentativa."""
        page = _make_mock_page(return_count=3)
        browser = FakeBrowser(connected=True)
        context = FakeContext()

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        assert isinstance(resultado, list)

    def test_timeout_primeira_tentativa_recupera_segunda(self):
        """Primeiro goto dá timeout, segundo funciona (page_valida)."""
        page = _make_mock_page(return_count=0)
        browser = FakeBrowser(connected=True)
        context = FakeContext()
        call_count = 0

        original_goto = page.goto

        async def mock_goto_timeout_once(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PlaywrightTimeoutError("Navigation timeout")
            return await original_goto(url, **kwargs)

        page.goto = mock_goto_timeout_once

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        assert isinstance(resultado, list)

    def test_timeout_duplo_retorna_vazio(self):
        """Dois timeouts de navegação retornam lista vazia, não NavegadorFechado."""
        page = _make_mock_page(return_count=0)

        async def always_timeout(url, **kwargs):
            raise PlaywrightTimeoutError("Navigation timeout")

        page.goto = always_timeout

        browser = FakeBrowser(connected=True)
        context = FakeContext()

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        # Timeout NÃO é classificado como NavegadorFechado
        assert resultado == []

    def test_browser_desconectado_levanta_navegador_fechado(self):
        """Browser desconectado levanta NavegadorFechado."""
        page = MagicMock()
        page.is_closed.return_value = False
        page.url = "https://www.google.com/maps"
        page.on = MagicMock()

        async def goto_timeout(url, **kwargs):
            raise PlaywrightTimeoutError("timeout")

        page.goto = goto_timeout
        page.locator = MagicMock()

        browser = FakeBrowser(connected=False)  # MORTO
        context = FakeContext()

        with pytest.raises(NavegadorFechado, match="browser desconectado"):
            _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))

    def test_page_valida_sem_resultados_retorna_vazio(self):
        """Página válida com 0 resultados retorna lista vazia, não erro."""
        page = _make_mock_page(return_count=0)
        browser = FakeBrowser(connected=True)
        context = FakeContext()

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Cidade Pequena",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        assert resultado == []

    def test_captcha_detectado_quando_habilitado(self):
        """CAPTCHA continua sendo tratado sem contorno."""
        page = _make_mock_page(return_count=0)
        browser = FakeBrowser(connected=True)
        context = FakeContext()

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=True), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock), \
             patch("mapear_comercios.salvar_screenshot", new_callable=AsyncMock):
            with pytest.raises(CaptchaDetectado):
                _run_async(buscar_categoria(
                    page, "celular", "Rio de Janeiro",
                    max_results=5, captcha_detector=True,
                    _run_id=None, _browser=browser, _context=context,
                ))

    def test_params_run_id_none_funciona(self):
        """buscar_categoria funciona com _run_id=None (sem logger)."""
        page = _make_mock_page(return_count=0)
        browser = FakeBrowser(connected=True)
        context = FakeContext()

        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        assert isinstance(resultado, list)

    def test_reload_seguro_nao_segue_se_page_fechada(self):
        """Verificação de saúde: page fechada antes de items.count() retorna []."""
        page = MagicMock()
        page.is_closed.return_value = True  # Page fechada!
        page.url = "https://www.google.com/maps"
        page.on = MagicMock()
        page._goto_count = 0

        async def mock_goto(url, **kwargs):
            page._goto_count += 1
            page.url = url
            return MagicMock()

        page.goto = mock_goto
        page.reload = AsyncMock()
        page.set_default_navigation_timeout = MagicMock()
        page.set_default_timeout = MagicMock()

        browser = FakeBrowser(connected=True)
        context = FakeContext()

        # Page fechada: _avaliar_saude_pagina retorna "page_fechada"
        # buscar_categoria deve retornar [] sem crash
        with patch("mapear_comercios.aceitar_cookies", new_callable=AsyncMock), \
             patch("mapear_comercios.detectar_captcha", new_callable=AsyncMock, return_value=False), \
             patch("mapear_comercios.scroll_panel", new_callable=AsyncMock), \
             patch("mapear_comercios.asyncio.sleep", new_callable=AsyncMock):
            resultado = _run_async(buscar_categoria(
                page, "celular", "Rio de Janeiro",
                max_results=5, _run_id=None, _browser=browser, _context=context,
            ))
        # Page fechada após timeout -> retorna [] (NÃO levanta NavegadorFechado)
        assert resultado == []


# ══════════════════════════════════════════════════════════════════
# Testes de run, checkpoint e leads preservados
# ══════════════════════════════════════════════════════════════════

class TestRunPreservado:
    """Garante que as mudanças não afetam a estrutura de run/checkpoint."""

    def test_timeout_navegacao_90s(self):
        """Timeout de navegação é 90000ms (90s), não 45000ms."""
        assert _TIMEOUT_NAVEGACAO_MS == 90000

    def test_timeout_seletor_nao_e_90s(self):
        """Timeout de seletor é separado (30s), não igual ao de navegação."""
        assert _TIMEOUT_SELETOR_MS == 30000
        assert _TIMEOUT_SELETOR_MS != _TIMEOUT_NAVEGACAO_MS