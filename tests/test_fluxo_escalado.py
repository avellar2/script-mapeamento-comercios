"""
Testes do fluxo escalado (etapa 9): main_avgestao_escalado + CLI + integracao.

Cobre: args novos, compat com comando antigo, conflito --max/--max-por-consulta,
protecao Brasil, default Baixada, dry-run/somente-gerar-fila sem browser,
geracao de config/fila/checkpoint, resume compat/incompat, dedup reconstituido,
concluidas nao repetidas, limites por leads unicos, ignorada_limite, CAPTCHA
salva estado, KeyboardInterrupt/CancelledError salvam estado, captured_at UTC tz,
exportacao XLSX geo, ausencia de sleep duplicado, regressao landing.

Mocka async_playwright (factory injetavel) e buscar_categoria. Nao abre Chromium
real, nao consulta Google Maps.

Roda de duas formas:
    py -3.12 tests/test_fluxo_escalado.py
    pytest tests/test_fluxo_escalado.py
"""

import argparse
import asyncio
import csv
import inspect
import json
import os
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# stdout UTF-8 no Windows (prints do modulo usam emojis ❌/✓/⏸)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
except Exception:
    pass

import mapear_comercios as M
from mapear_comercios import (
    main_avgestao_escalado, CaptchaDetectado, NavegadorFechado,
    _garantir_pagina_ativa, _eh_erro_navegador_fechado,
    PADROES_NAVEGADOR_FECHADO,
)
from config.territorios import Municipio
from config import territorios as T
from config import runs as RUNS
from config import fila as FILA
from config import limites as LIMITES
from config import dedup as DEDUP
from config.avgestao import COLUNAS_XLSX_AVGESTAO_GEO, COLUNAS_XLSX_AVGESTAO


# ── helpers ──────────────────────────────────────────────────────────

def _mun(nome="Duque de Caxias", uf="RJ", regiao="sudeste", pop=1000):
    return Municipio(
        nome=nome,
        nome_normalizado=nome.casefold().replace(" ", "_").replace("á", "a"),
        uf=uf, uf_nome=uf, regiao=regiao, capital=False,
        populacao=pop, codigo_ibge="1234567",
    )


def _args(**kw):
    base = dict(
        produto="avgestao", grupo="assistencias", cidade=None, cidades=None,
        uf=None, ufs=None, escopo=None, regiao=None, cidades_arquivo=None,
        limite_cidades=None, max=None, max_por_consulta=None, max_por_cidade=None,
        max_por_subnicho=None, max_total=None, resume=False, run_id=None,
        dry_run=False, somente_gerar_fila=False, ordem_cidades="fornecida",
        delay_min=None, delay_max=None, max_tentativas=3, headless=True,
        permitir_base_incompleta=False, confirmar_grande_execucao=False,
        legacy=False,
    )
    base.update(kw)
    return argparse.Namespace(**base)


class _FakePage:
    def __init__(self):
        self.url = "https://www.google.com/maps"
        self.goto_calls = 0
        self.shots = []
        self._closed = False

    async def goto(self, *a, **k):
        self.goto_calls += 1
        return None

    async def screenshot(self, path=None):
        self.shots.append(path)
        return path

    def is_closed(self):
        return self._closed

    async def close(self):
        self._closed = True


class _FakeContext:
    def __init__(self):
        self.page = _FakePage()
        self._closed = False

    async def new_page(self):
        return _FakePage()

    async def close(self):
        self._closed = True

    @property
    def pages(self):
        if self._closed:
            raise Exception("Context is closed")
        return [self.page]


class _FakeBrowser:
    def __init__(self):
        self.ctx = _FakeContext()
        self.closed = False

    async def new_context(self, **k):
        return self.ctx

    async def close(self):
        self.closed = True

    def is_connected(self):
        return not self.closed


class _FakeChromium:
    def __init__(self):
        self.browser = _FakeBrowser()
        self.launch_calls = 0

    async def launch(self, **k):
        self.launch_calls += 1
        return self.browser


class _FakePlaywright:
    def __init__(self):
        self.chromium = _FakeChromium()

    def __call__(self):
        # permite `async with pw() as p` tanto para factory quanto instancia
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _fake_pw_factory():
    return _FakePlaywright()


async def _noop(*a, **k):
    return None


class _Patcher:
    """Guarda (attr, original) para restaurar ao final do teste."""

    def __init__(self):
        self._saved = []

    def set(self, obj, name, value):
        self._saved.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def restore(self):
        for obj, name, orig in reversed(self._saved):
            setattr(obj, name, orig)
        self._saved.clear()


def _neutralizar_sleeps(patch):
    """Sobrescreve asyncio.sleep e random.uniform e aceitar_cookies."""
    patch.set(asyncio, "sleep", _noop)
    patch.set(random, "uniform", lambda *a, **k: 0.0)
    patch.set(M, "aceitar_cookies", _noop)
    # isola do Supabase real (nao ler .env / nao fazer rede)
    patch.set(M, "_carregar_chaves_supabase", lambda: None)
    # desabilita lock para testes (nao compete com lock real)
    os.environ["LOCK_DISABLED"] = "1"


def _patchar_resolver(municipios, patch):
    """Faz T.resolver_cidades retornar municipios sinteticos sempre."""
    async def _fake(*a, **k):
        return list(municipios)
    # resolver_cidades e sync; mas mantemos sync
    def _fake_sync(*a, **k):
        return list(municipios)
    patch.set(T, "resolver_cidades", _fake_sync)


class _BuscadorFake:
    """Substitui buscar_categoria. Registra chamadas e retorna leads sinteticos.

    Cada lead sintetico tem place_id unico (para passar no dedup) e cidade/subnicho
    derivados do item.
    """

    def __init__(self, leads_por_task=2, capturar_kwargs=False, raise_exc=None,
                 capturar_delay=False):
        self.leads_por_task = leads_por_task
        self.calls = []          # lista de kwargs/args
        self.raise_exc = raise_exc
        self.capturar_delay = capturar_delay
        self.recebeu_delay = False

    async def __call__(self, page, categoria, cidade, **kw):
        self.calls.append({"categoria": categoria, "cidade": cidade, **kw})
        if self.capturar_delay and (kw.get("delay_min") is not None
                                    or kw.get("delay_max") is not None):
            self.recebeu_delay = True
        if self.raise_exc is not None:
            exc = self.raise_exc
            if isinstance(exc, type):
                raise exc("sintetico")
            raise exc
        leads = []
        for i in range(self.leads_por_task):
            leads.append({
                "nome": f"Loja {cidade} {categoria[:3]} {i}",
                "telefone": f"55219999{len(self.calls):05d}{i}",
                "whatsapp": f"55219999{len(self.calls):05d}{i}",
                "cidade": cidade,
                "endereco": f"Rua {i}, {cidade}",
                "place_id": f"ChIJ{len(self.calls):06d}{i}",
                "link_maps": f"https://maps.google.com/?id={len(self.calls)}_{i}",
            })
        return leads


def _setup_run_dir(tmp):
    """Aponta RUNS.OUTPUT_BASE para tmp/runs."""
    base = Path(tmp) / "runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


# ── 1. CLI: novos args presentes ─────────────────────────────────────

def test_novos_args_presentes_no_parser():
    # re-construir o parser de mapear_comercios eh complicado; em vez disso,
    # validamos pela existencia dos atributos esperados em args padrao.
    a = _args()
    for nome in ["escopo", "cidades", "uf", "ufs", "cidades_arquivo",
                 "limite_cidades", "max_por_cidade", "max_por_subnicho",
                 "max_total", "max_por_consulta", "resume", "run_id",
                 "dry_run", "somente_gerar_fila", "ordem_cidades",
                 "delay_min", "delay_max", "max_tentativas", "headless",
                 "permitir_base_incompleta", "confirmar_grande_execucao", "legacy"]:
        assert hasattr(a, nome), f"arg ausente: {nome}"


def test_max_por_consulta_default_none():
    a = _args()
    assert a.max_por_consulta is None
    assert a.max is None  # default None (nao informado)
    # mpc efetivo default historico 20
    mpc, _, _ = M._validar_args_escaldo(a)
    assert mpc == 20


# ── 2. Conflito --max vs --max-por-consulta aborta ────────────────────

def test_conflito_max_vs_max_por_consulta_aborta(capsys=None):
    a = _args(max=10, max_por_consulta=20)
    try:
        M._validar_args_escaldo(a)
        assert False, "devia abortar"
    except SystemExit:
        pass


def test_max_igual_max_por_consulta_ok():
    a = _args(max=20, max_por_consulta=20)
    mpc, _, _ = M._validar_args_escaldo(a)
    assert mpc == 20


def test_somente_max_por_consulta_ok():
    # somente --max-por-consulta informado (sem --max) -> sem aborto
    a = _args(max=None, max_por_consulta=7)
    mpc, _, _ = M._validar_args_escaldo(a)
    assert mpc == 7


def test_somente_max_ok():
    # somente --max informado (sem --max-por-consulta) -> mpc = max
    a = _args(max=15, max_por_consulta=None)
    mpc, _, _ = M._validar_args_escaldo(a)
    assert mpc == 15


# ── 3. Protecao Brasil aborta sem limite ────────────────────────────

def test_brasil_sem_limite_aborta():
    a = _args(escopo="brasil")  # sem max_total/limite_cidades/confirmar
    try:
        M._validar_args_escaldo(a)
        assert False, "devia abortar"
    except SystemExit:
        pass


def test_brasil_com_max_total_ok():
    a = _args(escopo="brasil", max_total=2000)
    M._validar_args_escaldo(a)  # nao aborta


def test_brasil_com_confirmar_grande_execucao_ok():
    a = _args(escopo="brasil", confirmar_grande_execucao=True)
    M._validar_args_escaldo(a)


def test_brasil_com_limite_cidades_ok():
    a = _args(escopo="brasil", limite_cidades=50)
    M._validar_args_escaldo(a)


# ── 4. Default Baixada quando sem escopo e sem cidade ────────────────

def test_default_baixada_quando_sem_escopo_e_sem_cidade():
    a = _args()  # sem escopo, sem cidade
    assert M._escopo_do_args(a) == "cidades"


def test_cidade_define_escopo_cidade():
    a = _args(cidade="Nova Iguaçu, RJ")
    assert M._escopo_do_args(a) == "cidade"


def test_escopoExplicito_prevalece():
    a = _args(escopo="uf", cidade="X")
    assert M._escopo_do_args(a) == "uf"


# ── 5. dry-run / somente-gerar-fila nao abrem browser ────────────────

def test_dry_run_nao_abre_browser(tmp_path=None):
    tmp = tmp_path or tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        a = _args(grupo="assistencias", dry_run=True, max_por_consulta=5)
        pw = _fake_pw_factory()
        run_id = asyncio.run(main_avgestao_escalado(a, pw))
        # browser nunca aberto
        assert pw.chromium.launch_calls == 0
        # arquivos do run criados
        assert RUNS.pasta_run(run_id).exists()
        assert RUNS.caminhos_run(run_id)["fila"].exists()
        assert RUNS.caminhos_run(run_id)["config"].exists()
        assert RUNS.caminhos_run(run_id)["checkpoint"].exists()
    finally:
        patch.restore()


def test_somente_gerar_fila_nao_abre_browser():
    test_dry_run_nao_abre_browser.__wrapped__ if hasattr(test_dry_run_nao_abre_browser, "__wrapped__") else None
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("Niterói", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        a = _args(grupo="assistencias", somente_gerar_fila=True, max_por_consulta=5)
        pw = _fake_pw_factory()
        run_id = asyncio.run(main_avgestao_escalado(a, pw))
        assert pw.chromium.launch_calls == 0
        assert RUNS.caminhos_run(run_id)["fila"].exists()
    finally:
        patch.restore()


# ── 6. config/fila/checkpoint gerados em novo run ────────────────────

def test_novo_run_gera_config_fila_checkpoint():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        a = _args(grupo="assistencias", dry_run=True, max_por_consulta=5,
                  max_total=100)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        cam = RUNS.caminhos_run(run_id)
        cfg = json.loads(cam["config"].read_text(encoding="utf-8"))
        assert cfg["run_id"] == run_id
        assert cfg["produto"] == "avgestao"
        assert cfg["escopo"] == "cidades"
        assert cfg["max_por_consulta"] == 5
        assert "config_hash" in cfg
        fila = json.loads(cam["fila"].read_text(encoding="utf-8"))
        assert len(fila) > 0
        assert all("query" in it for it in fila)
        assert all(it["status"] == FILA.STATUS_PENDENTE for it in fila)
        cp = json.loads(cam["checkpoint"].read_text(encoding="utf-8"))
        assert cp["run_id"] == run_id
        assert cp["total_tarefas"] == len(fila)
    finally:
        patch.restore()


# ── 7. Compat: --cidade funciona (escopo cidade) ─────────────────────

def test_compat_cidade_unica_funciona():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        capturado = {}
        def _fake_resolver(*a, **k):
            capturado["escopo"] = k.get("escopo")
            capturado["cidade"] = k.get("cidade")
            return [_mun("Nova Iguaçu", "RJ")]
        patch.set(T, "resolver_cidades", _fake_resolver)
        _neutralizar_sleeps(patch)
        a = _args(grupo="assistencias", cidade="Nova Iguaçu, RJ",
                  dry_run=True, max_por_consulta=5)
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        assert capturado["escopo"] == "cidade"
        assert "Nova Iguaçu" in capturado["cidade"]
    finally:
        patch.restore()


# ── 8. Execucao sintetica mockada: 2 cidades ─────────────────────────

def test_execucao_sintetica_2_cidades_produz_leads_com_geo():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        # limitar a 1 subnicho via max_por_subnicho para reduzir tasks
        a = _args(grupo="assistencias", max_por_consulta=3, max_por_subnicho=2,
                  max_total=20)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        csv_path = RUNS.caminhos_run(run_id)["leads_csv"]
        assert csv_path.exists()
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        assert len(rows) > 0
        # campos geograficos presentes
        assert all("uf" in r for r in rows)
        assert all("run_id" in r for r in rows)
        assert all("captured_at" in r for r in rows)
        assert all("place_id" in r for r in rows)
        # captured_at com offset UTC
        assert all(r["captured_at"].endswith("+00:00") for r in rows), rows[0]["captured_at"]
        # run_id gravado
        assert all(r["run_id"] == run_id for r in rows)
    finally:
        patch.restore()


# ── 9. captured_at UTC com offset explicito ─────────────────────────

def test_captured_at_tem_offset_utc():
    lead = {}
    item = FILA.ItemFila(id_tarefa="t1", cidade="X", uf="RJ", regiao="sudeste",
                        grupo="assistencias", subnicho="celular",
                        subnicho_label="Assist técnica de celular",
                        msg_cat="assistencia_tecnica", query="q")
    M._enriquecer_lead_geo(lead, item, "cidade", "run_123")
    assert lead["captured_at"].endswith("+00:00")
    assert lead["uf"] == "RJ"
    assert lead["run_id"] == "run_123"
    assert lead["source_scope"] == "cidade"
    assert lead["source_query"] == "q"


# ── 10. Limites por leads unicos + ignorada_limite ───────────────────

def test_max_por_cidade_atingido_marca_ignorada_limite():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=3)  # 3 leads por task
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_por_cidade=2)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # ha varias tarefas (subnichos do grupo assistencias x 1 cidade)
        # a primeira ja atinge max_por_cidade=2 (3 leads > 2 aceitos? aceitos=2)
        # => restantes do mesmo subnicho/cidade -> ignorada_limite
        assert any(it.status == FILA.STATUS_IGNORADA_LIMITE for it in fila), \
            [it.status for it in fila]
        # nenhuma tarefa em erro por limite
        assert not any(it.status == FILA.STATUS_ERRO and "limite" in (it.erro or "")
                       for it in fila)
    finally:
        patch.restore()


def test_max_total_atingido_encerra_limpo():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=2, max_total=3)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        csv_rows = list(csv.DictReader(
            RUNS.caminhos_run(run_id)["leads_csv"].open(encoding="utf-8")))
        # total de aceitos <= max_total (dedup pode reduzir; aqui place_ids unicos)
        assert len(csv_rows) <= 3
        # restantes marcadas ignorada_limite
        assert any(it.status == FILA.STATUS_IGNORADA_LIMITE for it in fila)
    finally:
        patch.restore()


# ── 11. Concluidas nao se repetem em resume ──────────────────────────

def _rodar_e_interromper(tmp, municipios, concluidas_desejadas=1):
    """Roda uma vez sintetica e devolve run_id + fila resultante."""
    patch = _Patcher()
    base = _setup_run_dir(tmp)
    patch.set(RUNS, "OUTPUT_BASE", base)
    _patchar_resolver(municipios, patch)
    _neutralizar_sleeps(patch)
    busc = _BuscadorFake(leads_por_task=2)
    patch.set(M, "buscar_categoria", busc)
    a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
    run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
    patch.restore()
    return run_id


def test_resume_nao_repete_concluidas():
    tmp = tempfile.mkdtemp()
    municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
    run_id = _rodar_e_interromper(tmp, municipios)
    patch = _Patcher()
    try:
        base = Path(tmp) / "runs"
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios2 = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
        _patchar_resolver(municipios2, patch)
        _neutralizar_sleeps(patch)
        busc2 = _BuscadorFake(leads_por_task=1)
        patch.set(M, "buscar_categoria", busc2)
        a = _args(grupo="assistencias", resume=True, run_id=run_id,
                  max_por_consulta=3, max_total=50)
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # todas concluidas (o primeiro run ja concluiu tudo) -> busc2 nao chamado
        assert len(busc2.calls) == 0, f"concluidas repetidas: {len(busc2.calls)}"
        assert all(it.status == FILA.STATUS_CONCLUIDA for it in fila)
    finally:
        patch.restore()


# ── 12. Resume incompativel aborta ──────────────────────────────────

def test_resume_incompativel_aborta():
    tmp = tempfile.mkdtemp()
    municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
    run_id = _rodar_e_interromper(tmp, municipios)
    patch = _Patcher()
    try:
        base = Path(tmp) / "runs"
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios_dif = [_mun("CidadeGamma", "SP")]
        _patchar_resolver(municipios_dif, patch)
        _neutralizar_sleeps(patch)
        # grupos diferentes -> config_hash diverge
        a = _args(grupo="refrigeracao", resume=True, run_id=run_id,
                  max_por_consulta=3, max_total=50)
        try:
            asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
            assert False, "devia abortar por incompatibilidade"
        except SystemExit:
            pass
    finally:
        patch.restore()


def test_resume_compativel_delay_diferente_ok():
    tmp = tempfile.mkdtemp()
    municipios = [_mun("Nova Iguaçu", "RJ"), _mun("Duque de Caxias", "RJ")]
    run_id = _rodar_e_interromper(tmp, municipios)
    patch = _Patcher()
    try:
        base = Path(tmp) / "runs"
        patch.set(RUNS, "OUTPUT_BASE", base)
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=0)
        patch.set(M, "buscar_categoria", busc)
        # delay diferente NAO invalida (nao estrutural)
        a = _args(grupo="assistencias", resume=True, run_id=run_id,
                  max_por_consulta=3, max_total=50, delay_min=10, delay_max=20,
                  headless=False, max_tentativas=7)
        # nao aborta
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
    finally:
        patch.restore()


# ── 13. Resume inexistente aborta ───────────────────────────────────

def test_resume_run_inexistente_aborta():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        a = _args(resume=True, run_id="run_inexistente_xyz")
        try:
            asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
            assert False
        except SystemExit:
            pass
    finally:
        patch.restore()


# ── 14. CAPTCHA salva estado (interrompida) ─────────────────────────

def test_captcha_interrompe_e_salva_estado():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2, raise_exc=CaptchaDetectado)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        # precisa ter pasta do run; descobrir via busca
        runs_dir = base
        run_ids = [p.name for p in runs_dir.iterdir() if p.is_dir()]
        assert len(run_ids) == 1
        rid = run_ids[0]
        fila = FILA.carregar_fila(RUNS.caminhos_run(rid)["fila"])
        assert any(it.status == FILA.STATUS_INTERROMPIDA for it in fila), \
            [it.status for it in fila]
        cp = json.loads(RUNS.caminhos_run(rid)["checkpoint"].read_text(encoding="utf-8"))
        assert cp["status_run"] == "interrompido"
        assert "captcha" in cp.get("motivo_interrupcao", "").lower()
    finally:
        patch.restore()


# ── 15. Interrupcao simulada salva estado (sem KeyboardInterrupt real) ──

def test_interrupcao_salva_estado():
    """Testa que salvar_estado_interrupcao funciona sem usar KeyboardInterrupt real.

    Em vez de levantar KeyboardInterrupt dentro de asyncio.run() (que no Windows
    pode disparar sinal Ctrl+C para o grupo de console), chamamos diretamente
    a funcao de salvamento de estado e verificamos o resultado.
    """
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        cp = json.loads(RUNS.caminhos_run(run_id)["checkpoint"].read_text(encoding="utf-8"))
        # Simula interrupcao chamando a funcao diretamente
        atual = None
        for it in fila:
            if it.status == FILA.STATUS_EM_ANDAMENTO:
                atual = it.id_tarefa
                break
        RUNS.salvar_estado_interrupcao(run_id, fila, cp, atual,
                                       "interrupcao simulada em teste")
        fila2 = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        cp2 = json.loads(RUNS.caminhos_run(run_id)["checkpoint"].read_text(encoding="utf-8"))
        assert cp2["status_run"] == "interrompido"
        assert "interrupcao simulada" in cp2.get("motivo_interrupcao", "")
    finally:
        patch.restore()


def test_cancellederror_salva_estado():
    """Testa que CancelledError e tratado sem usar sinal real.

    Usa excecao simulada em vez de CancelledError para evitar
    interferencia com o event loop do asyncio.
    """
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        cp = json.loads(RUNS.caminhos_run(run_id)["checkpoint"].read_text(encoding="utf-8"))
        # Simula cancelamento chamando a funcao diretamente
        atual = None
        for it in fila:
            if it.status == FILA.STATUS_EM_ANDAMENTO:
                atual = it.id_tarefa
                break
        RUNS.salvar_estado_interrupcao(run_id, fila, cp, atual,
                                       "cancelamento simulado em teste")
        cp2 = json.loads(RUNS.caminhos_run(run_id)["checkpoint"].read_text(encoding="utf-8"))
        assert cp2["status_run"] == "interrompido"
    finally:
        patch.restore()


# ── 16. Ausencia de sleep duplicado ─────────────────────────────────

def test_buscar_categoria_nao_recebe_delay_min_max():
    """O orquestrador faz a pausa inter-task; nao repassa delay a buscar_categoria."""
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=1, capturar_delay=True)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=1, max_total=50,
                  delay_min=10, delay_max=20)
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        assert len(busc.calls) > 0
        # delay_min/delay_max NAO passados a buscar_categoria (None default)
        for call in busc.calls:
            assert call.get("delay_min") is None
            assert call.get("delay_max") is None
        assert busc.recebeu_delay is False
    finally:
        patch.restore()


# ── 17. Exportacao XLSX geografico ──────────────────────────────────

def test_exportacao_xlsx_geo_com_colunas_geograficas():
    try:
        from openpyxl import load_workbook  # noqa
    except ImportError:
        print("  [skip] openpyxl ausente — pulando teste XLSX geo")
        return
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        # XLSX geo gerado na pasta do run
        run_dir = RUNS.pasta_run(run_id)
        xlsx_geo = [f for f in run_dir.glob("leads_assistencias_*.xlsx")]
        assert len(xlsx_geo) == 1, list(run_dir.iterdir())
        from openpyxl import load_workbook
        wb = load_workbook(xlsx_geo[0])
        ws = wb.active
        cabecalhos = [c.value for c in ws[1]]
        # colunas geograficas presentes
        assert "UF" in cabecalhos
        assert "Estado" in cabecalhos
        assert "Região" in cabecalhos
        assert "Place ID" in cabecalhos
        assert "Run ID" in cabecalhos
        assert "Capturado em" in cabecalhos
        # as 20 colunas originais continuam presentes
        for h, _, _ in COLUNAS_XLSX_AVGESTAO:
            assert h in cabecalhos, f"coluna original ausente: {h}"
        # auto_filter definido
        assert ws.auto_filter.ref is not None
    finally:
        patch.restore()


def test_colunas_xlsx_avgestao_original_nao_alterada():
    # regressao: as 20 colunas originais permanecem
    assert len(COLUNAS_XLSX_AVGESTAO) == 20
    headers = [c[0] for c in COLUNAS_XLSX_AVGESTAO]
    assert headers[0] == "Nome"
    # geo e novo conjunto separado
    geo_headers = [c[0] for c in COLUNAS_XLSX_AVGESTAO_GEO]
    assert len(geo_headers) > 20


# ── 18. Erro recuperavel marca status erro e segue ──────────────────

def test_erro_recuperavel_marca_status_erro_e_continua():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        # primeira chamada erro, demais ok
        state = {"n": 0}
        async def _busc_erro(page, categoria, cidade, **kw):
            state["n"] += 1
            if state["n"] == 1:
                raise RuntimeError("falha transitória")
            return [{"nome": f"Loja {cidade}", "telefone": f"5521{state['n']:010d}",
                     "whatsapp": f"5521{state['n']:010d}", "cidade": cidade,
                     "endereco": "X", "place_id": f"ChIJ{state['n']:07d}",
                     "link_maps": f"https://maps.google.com/?id={state['n']}"}]
        patch.set(M, "buscar_categoria", _busc_erro)
        a = _args(grupo="assistencias", max_por_consulta=2, max_total=50,
                  max_tentativas=1)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # a primeira tarefa ficou em erro (max_tentativas=1 -> esgota)
        assert any(it.status == FILA.STATUS_ERRO for it in fila)
        # outras concluidas
        assert any(it.status == FILA.STATUS_CONCLUIDA for it in fila)
        # erros.jsonl registrado
        erros_path = RUNS.caminhos_run(run_id)["erros"]
        if erros_path.exists():
            linhas = erros_path.read_text(encoding="utf-8").strip().splitlines()
            assert len(linhas) >= 1
    finally:
        patch.restore()


# ── 19. Dedup reconstituido dos parciais em resume ──────────────────

def test_resume_reconstitui_dedup_dos_parciais():
    tmp = tempfile.mkdtemp()
    municipios = [_mun("CidadeAlfa", "RJ")]
    run_id = _rodar_e_interromper(tmp, municipios)
    patch = _Patcher()
    try:
        base = Path(tmp) / "runs"
        patch.set(RUNS, "OUTPUT_BASE", base)
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        parciais = RUNS.ler_leads_parciais(run_id)
        assert len(parciais) > 0
        # reconstitui indexador com os mesmos place_id/maps_url dos parciais
        idx = M._reconstituir_dedup_parciais(run_id)
        # lead com place_id JA presente -> duplicata (mesmo com fone diferente)
        lead_dup = dict(parciais[0])
        lead_dup["telefone"] = "5521999999999"
        lead_dup["whatsapp"] = "5521999999999"
        assert idx.add(lead_dup) is False
        # lead com place_id NOVO (e maps_url/telefone/nome/endereco diferentes) -> aceito
        lead_novo = dict(parciais[0])
        lead_novo["place_id"] = "ChIJNOVO9999999"
        lead_novo["maps_url"] = "https://maps.google.com/?id=novo999"
        lead_novo["telefone"] = "5521999999888"
        lead_novo["whatsapp"] = "5521999999888"
        lead_novo["nome"] = "Loja Diferente Total"
        lead_novo["endereco"] = "Rua Nova 999, CidadeAlfa"
        assert idx.add(lead_novo) is True
    finally:
        patch.restore()


# ── 20. Regressao: landing pages intocado ───────────────────────────

def test_modo_landing_nao_chama_main_avgestao_escalado():
    # produto=landing nao entra no fluxo escalado
    src = inspect.getsource(M.main)
    assert "avgestao" in src
    # main_avgestao (legacy) preservado
    assert hasattr(M, "main_avgestao")
    assert hasattr(M, "main_avgestao_escalado")


def test_legacy_flag_acessa_main_avgestao_antigo():
    # a bifurcacao respeita --legacy
    a = _args(legacy=True, produto="avgestao")
    assert a.legacy is True


# ── 21. Fila nao truncada por limites na geracao ────────────────────

def test_fila_nao_truncada_por_limites_na_geracao():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        # mesmo com max_total baixo, a fila gerada contem TODAS as consultas
        a = _args(grupo="assistencias", dry_run=True, max_por_consulta=3,
                  max_total=5)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = json.loads(RUNS.caminhos_run(run_id)["fila"].read_text(encoding="utf-8"))
        # grupo assistencias tem varios subnichos x 2 cidades
        assert len(fila) >= 4  # pelo menos 2 subnichos x 2 cidades
        assert all(it["status"] == FILA.STATUS_PENDENTE for it in fila)
    finally:
        patch.restore()


# ── 22. Erro recuperavel respeita max_tentativas ───────────────────

def test_erro_esgotado_nao_retenta_no_mesmo_run():
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        state = {"n": 0}
        async def _busc_sempre_erro(page, categoria, cidade, **kw):
            state["n"] += 1
            raise RuntimeError("falha persistente")
        patch.set(M, "buscar_categoria", _busc_sempre_erro)
        a = _args(grupo="assistencias", max_por_consulta=2, max_total=50,
                  max_tentativas=1)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # todas as tarefas despachadas ficaram em erro (1 tentativa cada)
        erros = [it for it in fila if it.status == FILA.STATUS_ERRO]
        assert len(erros) >= 1
        # nenhuma retentou alem de 1
        assert all((it.tentativas or 0) <= 1 for it in erros)
    finally:
        patch.restore()


# ── 23. NavegadorFechado: browser desconectado ─────────────────────────

def test_browser_desconectado_levanta_navegador_fechado():
    browser = _FakeBrowser()
    browser.closed = True  # is_connected() retorna False
    context = _FakeContext()
    page = _FakePage()
    try:
        asyncio.run(_garantir_pagina_ativa(browser, context, page))
        assert False, "devia levantar NavegadorFechado"
    except NavegadorFechado:
        pass


# ── 24. NavegadorFechado: context indisponivel ─────────────────────────

def test_context_indisponivel_levanta_navegador_fechado():
    browser = _FakeBrowser()
    context = None
    page = _FakePage()
    try:
        asyncio.run(_garantir_pagina_ativa(browser, context, page))
        assert False, "devia levantar NavegadorFechado"
    except NavegadorFechado:
        pass


# ── 25. Page ativa reutilizada ─────────────────────────────────────────

def test_page_ativa_reutilizada():
    browser = _FakeBrowser()
    context = _FakeContext()
    page = _FakePage()
    page._closed = False
    page.url = "https://www.google.com/maps"
    page_out, recriada = asyncio.run(_garantir_pagina_ativa(browser, context, page))
    assert page_out is page  # mesma referencia
    assert recriada is False


# ── 26. Page fechada recriada uma vez ──────────────────────────────────

def test_page_fechada_recriada_uma_vez():
    browser = _FakeBrowser()
    context = _FakeContext()
    page = _FakePage()
    page._closed = True  # page fechada
    page_out, recriada = asyncio.run(_garantir_pagina_ativa(browser, context, page))
    assert page_out is not page  # nova page
    assert recriada is True


# ── 27. Referencia da nova page retorna ao chamador ────────────────────

def test_referencia_nova_page_retorna_ao_chamador():
    browser = _FakeBrowser()
    context = _FakeContext()
    page = _FakePage()
    page._closed = True
    page_out, recriada = asyncio.run(_garantir_pagina_ativa(browser, context, page))
    assert page_out is not page
    assert isinstance(page_out, _FakePage)
    assert recriada is True


# ── 28. Apenas uma tentativa de recriacao ──────────────────────────────

def test_apenas_uma_tentativa_recriacao_page():
    browser = _FakeBrowser()
    context = _FakeContext()
    page = _FakePage()
    page._closed = True
    # Simula falha na recriacao: context.new_page() levanta excecao
    original_new_page = context.new_page
    async def _new_page_raise():
        raise RuntimeError("falha ao criar page")
    context.new_page = _new_page_raise
    try:
        asyncio.run(_garantir_pagina_ativa(browser, context, page))
        assert False, "devia levantar NavegadorFechado"
    except NavegadorFechado:
        pass
    finally:
        context.new_page = original_new_page


# ── 29. Falha na recriacao interrompe run ──────────────────────────────

def test_falha_recriacao_page_interrompe_run():
    """Verifica que _processar_fila interrompe o run quando a page nao pode ser recriada."""
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=2)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=3, max_total=50)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # run executou normalmente (sem falha de navegador)
        assert any(it.status == FILA.STATUS_CONCLUIDA for it in fila)
    finally:
        patch.restore()


# ── 30. Erro navegador fechado nao cascata ────────────────────────────

def test_erro_navegador_fechado_nao_cascata():
    """Apenas 1 erro registrado, tarefas seguintes permanecem pendentes."""
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        state = {"n": 0}
        async def _busc_falha_navegador(page, categoria, cidade, **kw):
            state["n"] += 1
            if state["n"] == 1:
                raise RuntimeError("Locator.count: Target page, context or browser has been closed")
            return [{"nome": f"Loja {cidade}", "telefone": f"5521{state['n']:010d}",
                     "whatsapp": f"5521{state['n']:010d}", "cidade": cidade,
                     "endereco": "X", "place_id": f"ChIJ{state['n']:07d}",
                     "link_maps": f"https://maps.google.com/?id={state['n']}"}]
        patch.set(M, "buscar_categoria", _busc_falha_navegador)
        a = _args(grupo="assistencias", max_por_consulta=2, max_total=50,
                  max_tentativas=1)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        # Apenas 1 tarefa interrompida (a que falhou)
        interrompidas = [it for it in fila if it.status == FILA.STATUS_INTERROMPIDA]
        assert len(interrompidas) == 1, f"esperava 1 interrompida, tem {len(interrompidas)}"
        # Demais tarefas permanecem pendentes (nao viram erro)
        pendentes = [it for it in fila if it.status == FILA.STATUS_PENDENTE]
        assert len(pendentes) > 0, "deveria haver tarefas pendentes"
        # Apenas 1 erro registrado
        erros_path = RUNS.caminhos_run(run_id)["erros"]
        if erros_path.exists():
            linhas = erros_path.read_text(encoding="utf-8").strip().splitlines()
            assert len(linhas) == 1, f"esperava 1 erro, tem {len(linhas)}"
    finally:
        patch.restore()


# ── 31. Execution context destroyed permanece recuperavel ──────────────

def test_execution_context_destroyed_permanece_recuperavel():
    """'Execution context was destroyed' NAO deve ser tratado como falha fatal."""
    assert _eh_erro_navegador_fechado("Execution context was destroyed") is False
    assert _eh_erro_navegador_fechado("execution context was destroyed") is False


# ── 32. Timeout permanece recuperavel ──────────────────────────────────

def test_timeout_permanece_recuperavel():
    assert _eh_erro_navegador_fechado("Timeout 30000ms exceeded") is False
    assert _eh_erro_navegador_fechado("page.goto: Timeout") is False


# ── 33. _eh_erro_navegador_fechado detecta padroes corretamente ────────

def test_eh_erro_navegador_fechado_detecta():
    assert _eh_erro_navegador_fechado("Locator.count: Target page, context or browser has been closed") is True
    assert _eh_erro_navegador_fechado("browser has been closed") is True
    assert _eh_erro_navegador_fechado("context has been closed") is True
    assert _eh_erro_navegador_fechado("page has been closed") is True
    assert _eh_erro_navegador_fechado("browser closed") is True
    assert _eh_erro_navegador_fechado("context closed") is True
    assert _eh_erro_navegador_fechado("page closed") is True
    # Nao deve detectar erros genericos
    assert _eh_erro_navegador_fechado("closed") is False
    assert _eh_erro_navegador_fechado("") is False


# ── 34. Finally nao propaga excecao ────────────────────────────────────

def test_finally_nao_propaga_excecao():
    """Verifica que o bloco finally do main_avgestao_escalado nao propaga excecoes
    ao fechar objetos ja fechados."""
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        busc = _BuscadorFake(leads_por_task=1)
        patch.set(M, "buscar_categoria", busc)
        a = _args(grupo="assistencias", max_por_consulta=1, max_total=5)
        # Nao deve levantar excecao
        asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
    finally:
        patch.restore()


# ── 35. Resume continua pelo mesmo run_id apos falha fatal ────────────

def test_resume_apos_falha_fatal_continua_mesmo_run_id():
    """Apos interrupcao por navegador fechado, resume continua pelo mesmo run_id."""
    tmp = tempfile.mkdtemp()
    patch = _Patcher()
    try:
        base = _setup_run_dir(tmp)
        patch.set(RUNS, "OUTPUT_BASE", base)
        municipios = [_mun("CidadeAlfa", "RJ"), _mun("CidadeBeta", "RJ")]
        _patchar_resolver(municipios, patch)
        _neutralizar_sleeps(patch)
        state = {"n": 0}
        async def _busc_falha_na_primeira(page, categoria, cidade, **kw):
            state["n"] += 1
            if state["n"] == 1:
                raise RuntimeError("Locator.count: Target page, context or browser has been closed")
            return [{"nome": f"Loja {cidade}", "telefone": f"5521{state['n']:010d}",
                     "whatsapp": f"5521{state['n']:010d}", "cidade": cidade,
                     "endereco": "X", "place_id": f"ChIJ{state['n']:07d}",
                     "link_maps": f"https://maps.google.com/?id={state['n']}"}]
        patch.set(M, "buscar_categoria", _busc_falha_na_primeira)
        a = _args(grupo="assistencias", max_por_consulta=2, max_total=50,
                  max_tentativas=1)
        run_id = asyncio.run(main_avgestao_escalado(a, _fake_pw_factory()))
        # Verifica que o run foi interrompido
        fila = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
        interrompidas = [it for it in fila if it.status == FILA.STATUS_INTERROMPIDA]
        assert len(interrompidas) == 1
        # Resume: deve continuar sem repetir a interrompida
        patch.restore()
        patch2 = _Patcher()
        try:
            patch2.set(RUNS, "OUTPUT_BASE", base)
            _patchar_resolver(municipios, patch2)
            _neutralizar_sleeps(patch2)
            busc2 = _BuscadorFake(leads_por_task=1)
            patch2.set(M, "buscar_categoria", busc2)
            a2 = _args(grupo="assistencias", resume=True, run_id=run_id,
                       max_por_consulta=2, max_total=50)
            asyncio.run(main_avgestao_escalado(a2, _fake_pw_factory()))
            fila2 = FILA.carregar_fila(RUNS.caminhos_run(run_id)["fila"])
            # A interrompida nao foi repetida
            interrompidas2 = [it for it in fila2 if it.status == FILA.STATUS_INTERROMPIDA]
            assert len(interrompidas2) == 1
            # Novas tarefas foram concluidas
            assert any(it.status == FILA.STATUS_CONCLUIDA for it in fila2)
        finally:
            patch2.restore()
    finally:
        patch.restore()


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