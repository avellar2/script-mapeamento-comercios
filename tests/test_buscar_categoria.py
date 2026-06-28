"""
Testes de robustez de buscar_categoria (etapa 8).

Testa os helpers testaveis (validar_delays, _alcance_tentativas,
detectar_captcha, salvar_screenshot, _deve_interromper_por_captcha) e a
integracao de deteccao de CAPTCHA habilitada/desabilitada com a funcao
(usando fake page + neutralizacao de sleeps). Nao abre Google Maps.

Roda de duas formas:
    py -3.12 tests/test_buscar_categoria.py
    pytest tests/test_buscar_categoria.py
"""

import asyncio
import inspect
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mapear_comercios as M
from mapear_comercios import (
    buscar_categoria,
    CaptchaDetectado,
    validar_delays,
    detectar_captcha,
    salvar_screenshot,
    _alcance_tentativas,
    _deve_interromper_por_captcha,
)


# ── defaults antigos ─────────────────────────────────────────────────

def test_defaults_antigos_buscar_categoria():
    sig = inspect.signature(buscar_categoria)
    p = sig.parameters
    assert p["delay_min"].default is None
    assert p["delay_max"].default is None
    assert p["max_tentativas"].default == 3
    assert p["screenshot_dir"].default is None
    assert p["captcha_detector"].default is False
    # defaults reproduzem comportamento atual
    assert validar_delays(None, None) == (1.8, 3.5)
    assert _alcance_tentativas(None) == 3


# ── validar_delays ───────────────────────────────────────────────────

def test_validar_delays_default():
    assert validar_delays(None, None) == (1.8, 3.5)


def test_validar_delays_custom():
    assert validar_delays(2, 5) == (2.0, 5.0)


def test_validar_delays_somente_min_usa_max_padrao():
    dmin, dmax = validar_delays(3, None)
    assert dmin == 3.0 and dmax == 3.5


def test_validar_delays_min_maior_max_erro():
    try:
        validar_delays(5, 2)
        assert False, "devia dar ValueError"
    except ValueError:
        pass


def test_validar_delays_negativo_erro():
    try:
        validar_delays(-1, 5)
        assert False, "devia dar ValueError"
    except ValueError:
        pass


# ── _alcance_tentativas (quantidade de tentativas) ──────────────────

def test_alcance_tentativas_default():
    assert _alcance_tentativas(None) == 3


def test_alcance_tentativas_respeita_max():
    assert _alcance_tentativas(5) == 5
    assert _alcance_tentativas(1) == 1
    assert _alcance_tentativas(10) == 10


def test_alcance_tentativas_invalido_cai_default():
    assert _alcance_tentativas(0) == 3
    assert _alcance_tentativas(-1) == 3


# ── detectar_captcha ─────────────────────────────────────────────────

class _Loc:
    def __init__(self, count_val=0):
        self._count = count_val

    async def count(self):
        return self._count


class _FakePageUrl:
    def __init__(self, url, captcha_count=0):
        self._url = url
        self._captcha_count = captcha_count

    @property
    def url(self):
        return self._url

    def locator(self, sel):
        if sel == "#captcha":
            return _Loc(self._captcha_count)
        return _Loc(0)


def test_detectar_captcha_url_sorry():
    p = _FakePageUrl("https://www.google.com/sorry/index?continue=...")
    assert asyncio.run(detectar_captcha(p)) is True


def test_detectar_captcha_url_accounts():
    p = _FakePageUrl("https://accounts.google.com/something")
    assert asyncio.run(detectar_captcha(p)) is True


def test_detectar_captcha_normal_false():
    p = _FakePageUrl("https://www.google.com/maps/search/celular+em+RJ/")
    assert asyncio.run(detectar_captcha(p)) is False


def test_detectar_captcha_seletor_true():
    p = _FakePageUrl("https://www.google.com/maps/search/x/", captcha_count=1)
    assert asyncio.run(detectar_captcha(p)) is True


class _PageUrlErro:
    @property
    def url(self):
        raise RuntimeError("pagina sumiu")

    def locator(self, sel):
        return _Loc(0)


def test_detectar_captcha_erro_leitura_retorna_false():
    # tolerante: erro ao ler url/locator nao vira True
    assert asyncio.run(detectar_captcha(_PageUrlErro())) is False


# ── _deve_interromper_por_captcha ───────────────────────────────────

def test_deve_interromper_habilitado_detectado():
    assert _deve_interromper_por_captcha(True, True) is True


def test_deve_interromper_desabilitado_nao_interrompe():
    # captcha detectado mas detector desligado -> nao interrompe
    assert _deve_interromper_por_captcha(False, True) is False


def test_deve_interromper_habilitado_nao_detectado():
    assert _deve_interromper_por_captcha(True, False) is False


# ── salvar_screenshot ────────────────────────────────────────────────

class _PageShot:
    def __init__(self, raise_=False):
        self.shots = []
        self._raise = raise_

    async def screenshot(self, path=None):
        if self._raise:
            raise RuntimeError("fail")
        self.shots.append(path)
        return path


def test_salvar_screenshot_sem_dir_retorna_none():
    page = _PageShot()
    out = asyncio.run(salvar_screenshot(page, None, "x"))
    assert out is None
    assert page.shots == []


def test_salvar_screenshot_com_dir_cria_arquivo():
    page = _PageShot()
    with tempfile.TemporaryDirectory() as tmp:
        out = asyncio.run(salvar_screenshot(page, tmp, "falha"))
        assert out is not None
        assert out.name == "falha.png"
        assert page.shots == [str(out)]


def test_salvar_screenshot_erro_retorna_none():
    page = _PageShot(raise_=True)
    with tempfile.TemporaryDirectory() as tmp:
        out = asyncio.run(salvar_screenshot(page, tmp, "x"))
        assert out is None  # engolido silenciosamente


# ── integracao: CAPTCHA habilitado interrompe ────────────────────────

class _ItemLoc:
    def __init__(self, page, sel):
        self.page = page
        self.sel = sel

    @property
    def first(self):
        return self

    async def count(self):
        return 0

    async def click(self, timeout=10000):
        pass

    async def scroll_into_view_if_needed(self, timeout=1000):
        pass

    def nth(self, i):
        return self


class _FakePageMaps:
    """Fake minimo para buscar_categoria chegar ate a deteccao de captcha."""

    def __init__(self, url):
        self._url = url
        self.shots = []

    @property
    def url(self):
        return self._url

    async def goto(self, *a, **k):
        return None

    async def reload(self, *a, **k):
        return None

    async def screenshot(self, path=None):
        self.shots.append(path)
        return path

    def locator(self, sel):
        return _ItemLoc(self, sel)


async def _noop_coro(*a, **k):
    return None


def _neutralizar_sleeps():
    """Patches para testes: sleeps viram noop, random.uniform -> 0."""
    return (
        asyncio.sleep,
        random.uniform,
        M.aceitar_cookies,
        M.scroll_panel,
    )


def _aplicar_neutros():
    asyncio.sleep = _noop_coro  # type: ignore
    random.uniform = lambda *a, **k: 0.0  # type: ignore
    M.aceitar_cookies = _noop_coro  # type: ignore
    M.scroll_panel = _noop_coro  # type: ignore


def _restaurar(orig):
    asyncio.sleep, random.uniform, M.aceitar_cookies, M.scroll_panel = orig


def test_captcha_habilitado_interrompe_e_salva_screenshot():
    orig = _neutralizar_sleeps()
    _aplicar_neutros()
    page = _FakePageMaps("https://www.google.com/sorry/index?continue=maps")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            try:
                asyncio.run(buscar_categoria(
                    page, "celular", "RJ", max_results=1,
                    captcha_detector=True, screenshot_dir=tmp,
                ))
                assert False, "devia levantar CaptchaDetectado"
            except CaptchaDetectado:
                pass
            # screenshot do captcha foi salva
            assert any("captcha" in str(s) for s in page.shots), page.shots
        finally:
            _restaurar(orig)


def test_captcha_desabilitado_nao_interrompe():
    orig = _neutralizar_sleeps()
    _aplicar_neutros()
    page = _FakePageMaps("https://www.google.com/sorry/index?continue=maps")
    try:
        # captcha_detector=False: mesmo com URL de bloqueio, NAO levanta
        resultado = asyncio.run(buscar_categoria(
            page, "celular", "RJ", max_results=1, captcha_detector=False,
        ))
        assert resultado == []  # 0 resultados, mas nao interrompeu
    finally:
        _restaurar(orig)


def test_sem_captcha_detector_nao_interrompe_mesmo_url_normal():
    orig = _neutralizar_sleeps()
    _aplicar_neutros()
    page = _FakePageMaps("https://www.google.com/maps/search/celular+em+RJ/")
    try:
        resultado = asyncio.run(buscar_categoria(
            page, "celular", "RJ", max_results=1, captcha_detector=True,
        ))
        assert resultado == []  # url normal, sem captcha -> continua
    finally:
        _restaurar(orig)


# ── runner ──────────────────────────────────────────────────────────

def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passou = 0
    falhou = 0
    for fn in fns:
        try:
            fn()
            passou += 1
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            falhou += 1
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            falhou += 1
            print(f"  ERROR  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())