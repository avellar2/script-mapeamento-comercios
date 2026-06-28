"""
Testes de config/runs.py (run, checkpoint, escrita atomica, config_hash, resume).

Roda de duas formas:
    py -3.12 tests/test_runs.py
    pytest tests/test_runs.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config.runs as R
from config.runs import (
    gerar_run_id, pasta_run, caminhos_run,
    salvar_config, carregar_config,
    salvar_fila_run, salvar_checkpoint, carregar_checkpoint,
    novo_checkpoint, salvar_resumo, carregar_resumo,
    salvar_estado_interrupcao, salvar_json_atomico, carregar_json,
    config_hash, verificar_compatibilidade_resume, VERSAO_FILA,
    anexar_linha_csv, ler_leads_parciais, registrar_erro,
)
from config.fila import gerar_fila, carregar_fila, STATUS_EM_ANDAMENTO, STATUS_INTERROMPIDA
from config.avgestao import get_grupo
from config.territorios import resolver_cidades


class _TempRuns:
    """Redireciona OUTPUT_BASE para um diretorio temporario."""

    def __enter__(self):
        self._base = R.OUTPUT_BASE
        self.tmp = tempfile.TemporaryDirectory()
        R.OUTPUT_BASE = Path(self.tmp.name) / "runs"
        return self

    def __exit__(self, *exc):
        R.OUTPUT_BASE = self._base
        self.tmp.cleanup()
        return False


def _config_base(**over):
    c = {
        "produto": "avgestao",
        "grupos": ["assistencias"],
        "escopo": "uf",
        "escopo_descritor": "RJ",
        "municipios": resolver_cidades(escopo="uf", uf=["RJ"], limite_cidades=3),
        "subnichos": ["celular", "computadores"],
        "consultas": ["assistencia tecnica de celular em Duque de Caxias, RJ"],
        "ordem_cidades": "alfabetica",
        "max_por_consulta": 20,
        "max_por_cidade": None,
        "max_por_subnicho": None,
        "max_total": 300,
        "delay_min": 2.0,
        "delay_max": 5.0,
        "max_tentativas": 3,
        "headless": False,
    }
    c.update(over)
    return c


# ── run id e caminhos ──────────────────────────────────────────────

def test_gerar_run_id_formato():
    rid = gerar_run_id()
    assert rid.startswith("run_")
    assert rid.replace("run_", "").count("_") == 2


def test_pasta_run_cria_dir():
    with _TempRuns():
        rid = gerar_run_id()
        p = pasta_run(rid)
        assert p.exists() and p.is_dir()
        caminhos = caminhos_run(rid)
        assert caminhos["config"].parent == p
        assert caminhos["fila"].name == "fila.json"


# ── config roundtrip ───────────────────────────────────────────────

def test_salvar_carregar_config_roundtrip():
    with _TempRuns():
        rid = gerar_run_id()
        cfg = _config_base()
        salvar_config(rid, cfg)
        carregada = carregar_config(rid)
        assert carregada["grupos"] == ["assistencias"]
        assert carregada["max_total"] == 300
        assert carregada["config_hash"]
        assert carregada["versao_fila"] == VERSAO_FILA


# ── config_hash ─────────────────────────────────────────────────────

def test_config_hash_deterministico():
    cfg = _config_base()
    h1 = config_hash(cfg)
    h2 = config_hash(cfg)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_config_hash_ignora_delay_headless_max_tentativas():
    cfg = _config_base()
    h1 = config_hash(cfg)
    # mudancas NAO estruturais nao alteram o hash
    cfg2 = _config_base(delay_min=10.0, delay_max=20.0, max_tentativas=5, headless=True)
    h2 = config_hash(cfg2)
    assert h1 == h2, "delay/headless/max_tentativas nao devem invalidar o run"


def test_config_hash_muda_quando_max_total_muda():
    # alterar limites exige novo run
    cfg = _config_base(max_total=300)
    h1 = config_hash(cfg)
    cfg2 = _config_base(max_total=600)
    h2 = config_hash(cfg2)
    assert h1 != h2


def test_config_hash_muda_quando_grupos_mudam():
    h1 = config_hash(_config_base(grupos=["assistencias"]))
    h2 = config_hash(_config_base(grupos=["assistencias", "refrigeracao"]))
    assert h1 != h2


def test_config_hash_muda_quando_escopo_muda():
    h1 = config_hash(_config_base(escopo="uf", escopo_descritor="RJ"))
    h2 = config_hash(_config_base(escopo="regiao", escopo_descritor="sudeste"))
    assert h1 != h2


# ── verificar_compatibilidade_resume ───────────────────────────────

def test_resume_compativel_quando_so_delay_muda():
    salvo = _config_base()
    salvar = salvar_config  # noqa
    atual = _config_base(delay_min=99.0, delay_max=99.0, max_tentativas=7, headless=True)
    motivos = verificar_compatibilidade_resume(salvo, atual)
    assert motivos == [], motivos


def test_resume_incompativel_quando_max_total_muda():
    salvo = _config_base(max_total=300)
    atual = _config_base(max_total=600)
    motivos = verificar_compatibilidade_resume(salvo, atual)
    assert len(motivos) >= 1
    assert any("max_total" in m for m in motivos)


def test_resume_incompativel_quando_grupos_mudam():
    salvo = _config_base(grupos=["assistencias"])
    atual = _config_base(grupos=["assistencias", "refrigeracao"])
    motivos = verificar_compatibilidade_resume(salvo, atual)
    assert any("grupos" in m for m in motivos)


def test_resume_incompativel_quando_escopo_muda():
    salvo = _config_base(escopo="uf", escopo_descritor="RJ")
    atual = _config_base(escopo="brasil", escopo_descritor="brasil")
    motivos = verificar_compatibilidade_resume(salvo, atual)
    assert any("escopo" in m for m in motivos)


# ── escrita atomica ─────────────────────────────────────────────────

def test_salvar_json_atomico_substitui_sem_tmp_residual():
    with _TempRuns():
        rid = gerar_run_id()
        caminho = caminhos_run(rid)["config"]
        salvar_json_atomico(caminho, {"a": 1})
        salvar_json_atomico(caminho, {"a": 2, "b": 3})
        # sem arquivo .tmp residual
        assert not caminho.with_name(caminho.name + ".tmp").exists()
        data = carregar_json(caminho)
        assert data == {"a": 2, "b": 3}  # substituiu completamente (nao append)


def test_salvar_json_atomico_preserva_unicode():
    with _TempRuns():
        rid = gerar_run_id()
        caminho = caminhos_run(rid)["resumo"]
        salvar_json_atomico(caminho, {"cidade": "São João de Meriti"})
        texto = caminho.read_text(encoding="utf-8")
        assert "São João de Meriti" in texto


# ── checkpoint ──────────────────────────────────────────────────────

def test_novo_checkpoint_zerado():
    cp = novo_checkpoint("run_x", 10)
    assert cp["total_tarefas"] == 10
    assert cp["concluidas"] == 0
    assert cp["pendentes"] == 10
    assert cp["ignoradas_limite"] == 0
    assert cp["status_run"] == "em_andamento"


def test_salvar_carregar_checkpoint_roundtrip():
    with _TempRuns():
        rid = gerar_run_id()
        cp = novo_checkpoint(rid, 5)
        cp["concluidas"] = 2
        cp["pendentes"] = 3
        salvar_checkpoint(rid, cp)
        carregado = carregar_checkpoint(rid)
        assert carregado["concluidas"] == 2
        assert carregado["pendentes"] == 3


# ── resumo ──────────────────────────────────────────────────────────

def test_salvar_carregar_resumo_roundtrip():
    with _TempRuns():
        rid = gerar_run_id()
        salvar_resumo(rid, {"unicos": 920})
        assert carregar_resumo(rid)["unicos"] == 920


# ── leads parciais (csv incremental) ─────────────────────────────────

def test_anexar_linha_csv_incremental():
    with _TempRuns():
        rid = gerar_run_id()
        anexar_linha_csv(rid, [{"nome": "A", "cidade": "RJ", "uf": "RJ"}])
        anexar_linha_csv(rid, [{"nome": "B", "cidade": "SP", "uf": "SP"}])
        anexar_linha_csv(rid, [{"nome": "C", "cidade": "MG", "uf": "MG"}])
        leads = ler_leads_parciais(rid)
        # 1 cabecalho + 3 linhas
        assert len(leads) == 3
        assert leads[0]["nome"] == "A"
        assert leads[2]["nome"] == "C"


# ── erros jsonl ─────────────────────────────────────────────────────

def test_registrar_erro_jsonl():
    with _TempRuns():
        rid = gerar_run_id()
        registrar_erro(rid, {"id_tarefa": "t1", "cidade": "RJ", "subnicho": "celular"},
                       ValueError("timeout"))
        p = caminhos_run(rid)["erros"]
        linhas = p.read_text(encoding="utf-8").strip().split("\n")
        assert len(linhas) == 1
        reg = json.loads(linhas[0])
        assert reg["id_tarefa"] == "t1"
        assert "timeout" in reg["erro"]


# ── Ctrl+C simulado (resgate de interrupcao) ─────────────────────────

def test_resgate_interrupcao_marca_tarefa_e_salva():
    with _TempRuns():
        rid = gerar_run_id()
        municipios = resolver_cidades(escopo="uf", uf=["RJ"], limite_cidades=2)
        fila = gerar_fila([get_grupo("assistencias")], municipios, max_por_consulta=3)
        cp = novo_checkpoint(rid, len(fila))
        # simula tarefa em andamento
        fila[0].status = STATUS_EM_ANDAMENTO
        atual = fila[0].id_tarefa

        salvar_estado_interrupcao(rid, fila, cp, atual, "KeyboardInterrupt simulado")

        # recarrega fila e checkpoint do disco
        fila_salva = carregar_fila(caminhos_run(rid)["fila"])
        item = next(i for i in fila_salva if i.id_tarefa == atual)
        assert item.status == STATUS_INTERROMPIDA
        assert "KeyboardInterrupt" in (item.erro or "")

        cp_salvo = carregar_checkpoint(rid)
        assert cp_salvo["status_run"] == "interrompido"
        assert "KeyboardInterrupt" in cp_salvo["motivo_interrupcao"]
        assert cp_salvo["interrompidas"] >= 1


def test_resgate_interrupcao_nao_muda_tarefa_concluida():
    with _TempRuns():
        rid = gerar_run_id()
        municipios = resolver_cidades(escopo="uf", uf=["RJ"], limite_cidades=1)
        fila = gerar_fila([get_grupo("assistencias")], municipios, max_por_consulta=3)
        fila[0].status = "concluida"
        cp = novo_checkpoint(rid, len(fila))
        salvar_estado_interrupcao(rid, fila, cp, fila[0].id_tarefa, "captcha")
        fila_salva = carregar_fila(caminhos_run(rid)["fila"])
        assert fila_salva[0].status == "concluida"  # nao reescreve concluida


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
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())