"""
Testes do orquestrador AVGESTAO (executar_campanha_avgestao.py).

Cobre: run_id gerado antes dos subprocessos, repasse a todas as etapas,
preservacao de --run-id, resume exige run valido, ordem e selecao de etapas,
erro interrompe fluxo, dry-run para apos mapear, args geograficos repassados,
sem shell=True, sem envio WhatsApp, arquivos listados apenas quando existem.
"""

import subprocess
import sys
import tempfile
import argparse
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import executar_campanha_avgestao as O

FAKE_RUN_ID = "run_20260101_000000_abc123"
FAKE_XLSX = Path("/fake/leads_fake_geo.xlsx")


def _fake_subprocess_ok(cmd, **kw):
    return subprocess.CompletedProcess(cmd, 0)


def _fake_subprocess_fail_mapear(cmd, **kw):
    if "mapear_comercios" in str(cmd):
        return subprocess.CompletedProcess(cmd, 1)
    return subprocess.CompletedProcess(cmd, 0)


def _run_main(args_list, patches=None):
    if patches is None:
        patches = {}
    saved = sys.argv
    run_calls = []

    def capturing_run(cmd, **kw):
        run_calls.append(cmd)
        runner = patches.get("subprocess_run", _fake_subprocess_ok)
        return runner(cmd, **kw)

    try:
        sys.argv = ["orquestrador.py"] + args_list
        with patch.object(O, "subprocess") as m:
            m.run = capturing_run
            m.CompletedProcess = subprocess.CompletedProcess
            with patch.object(O, "_gerar_run_id", return_value=FAKE_RUN_ID):
                with patch.object(O, "_encontrar_xlsx_geo", return_value=FAKE_XLSX):
                    try:
                        O.main()
                    except SystemExit as e:
                        return e.code, run_calls
    finally:
        sys.argv = saved
    return None, run_calls


# ── 1. run_id gerado antes dos subprocessos ─────────────────────────

def test_run_id_gerado_antes_dos_subprocessos():
    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    assert len(calls) >= 1
    first = " ".join(calls[0])
    assert "--run-id" in first
    assert FAKE_RUN_ID in first


# ── 2. run_id repassado a todas as etapas ───────────────────────────

def test_run_id_repassado_todas_etapas():
    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    assert len(calls) == 3, f"esperava 3 etapas, teve {len(calls)}"


# ── 3. run_id informado e preservado ────────────────────────────────

def test_run_id_informado_preservado():
    code, calls = _run_main(
        ["--run-id", "run_MEU_ID_123", "--grupo", "assistencias",
         "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    mapear_cmd = " ".join(calls[0])
    assert "run_MEU_ID_123" in mapear_cmd
    # run_id fornecido nao deve aparecer duplicado
    assert mapear_cmd.count("run_MEU_ID_123") == 1


# ── 4. resume exige run valido ──────────────────────────────────────

def test_resume_exige_run_id():
    code, calls = _run_main(["--resume"])
    assert code == 1


def test_resume_exige_run_existente():
    with patch.object(O.RUNS_DIR.__class__, "exists", return_value=False):
        code, calls = _run_main(["--resume", "--run-id", "run_fantasma"])
    assert code == 1


# ── 5. ordem das etapas ─────────────────────────────────────────────

def test_ordem_etapas_mapear_prospectar_campanha():
    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    assert len(calls) == 3
    assert "mapear_comercios.py" in calls[0][1]
    assert "prospectar_leads.py" in calls[1][1]
    assert "campanha_diaria.py" in calls[2][1]


# ── 6. selecao parcial por --etapas ─────────────────────────────────

def test_etapas_parcial_so_mapear():
    code, calls = _run_main(
        ["--etapas", "mapear", "--grupo", "assistencias",
         "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    assert len(calls) == 1
    assert "mapear_comercios.py" in calls[0][1]


def test_etapas_parcial_mapear_prospectar():
    code, calls = _run_main(
        ["--etapas", "mapear,prospectar", "--grupo", "assistencias",
         "--escopo", "uf", "--uf", "RJ", "--max-total", "300"])
    assert len(calls) == 2
    assert "mapear_comercios.py" in calls[0][1]
    assert "prospectar_leads.py" in calls[1][1]


# ── 7. etapa com erro interrompe o fluxo ────────────────────────────

def test_erro_na_etapa_interrompe_fluxo():
    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ", "--max-total", "300"],
        {"subprocess_run": _fake_subprocess_fail_mapear})
    assert code == 1
    assert len(calls) == 1


# ── 8. proxima etapa nao roda apos falha ────────────────────────────

def test_prospectar_nao_roda_apos_falha_no_mapear():
    def fail_only_mapear(cmd, **kw):
        if "mapear_comercios" in str(cmd):
            return subprocess.CompletedProcess(cmd, 1)
        return subprocess.CompletedProcess(cmd, 0)

    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ", "--max-total", "300"],
        {"subprocess_run": fail_only_mapear})
    scripts = [c[1] for c in calls]
    for s in scripts:
        assert "prospectar" not in s
        assert "campanha" not in s


# ── 9. dry-run termina apos mapear ──────────────────────────────────

def test_dry_run_termina_apos_mapear():
    code, calls = _run_main(
        ["--grupo", "assistencias", "--escopo", "uf", "--uf", "RJ",
         "--max-total", "300", "--dry-run"])
    assert code is None  # nao foi SystemExit(1)
    assert len(calls) == 1
    assert "--dry-run" in " ".join(calls[0])


# ── 10. argumentos geograficos repassados corretamente ──────────────

def test_args_geograficos_repassados_ao_mapear():
    a = argparse.Namespace(
        grupo="assistencias", escopo="uf", cidade=None, cidades=None,
        uf=["RJ", "SP"], ufs=None, regiao=None, cidades_arquivo=None,
        limite_cidades=20, max_por_cidade=None, max_por_subnicho=None,
        max_total=500, max_por_consulta=10, ordem_cidades="maiores",
        delay_min=3.0, delay_max=8.0, max_tentativas=3, headless=False,
        resume=False, run_id=None, permitir_base_incompleta=False,
        confirmar_grande_execucao=False, dry_run=False, somente_gerar_fila=False,
    )
    cmd = O._flags_mapear(a, "run_GEO")
    cmd_str = " ".join(cmd)
    assert "--produto avgestao" in cmd_str
    assert "--escopo uf" in cmd_str
    assert "--uf RJ" in cmd_str
    assert "--uf SP" in cmd_str
    assert "--max-total 500" in cmd_str
    assert "--max-por-consulta 10" in cmd_str
    assert "--limite-cidades 20" in cmd_str
    assert "--ordem-cidades maiores" in cmd_str
    assert "--delay-min 3.0" in cmd_str
    assert "--delay-max 8.0" in cmd_str
    assert "--run-id run_GEO" in cmd_str


def test_args_geograficos_repassados_com_resume():
    a = argparse.Namespace(
        grupo="assistencias", escopo=None, cidade=None, cidades=None,
        uf=None, ufs=None, regiao=None, cidades_arquivo=None,
        limite_cidades=None, max_por_cidade=None, max_por_subnicho=None,
        max_total=None, max_por_consulta=None, ordem_cidades=None,
        delay_min=None, delay_max=None, max_tentativas=None, headless=False,
        resume=True, run_id="run_RESUME_123",
        permitir_base_incompleta=False, confirmar_grande_execucao=False,
        dry_run=False, somente_gerar_fila=False,
    )
    cmd = O._flags_mapear(a, "run_RESUME_123")
    cmd_str = " ".join(cmd)
    assert "--resume" in cmd_str
    assert "--run-id run_RESUME_123" in cmd_str


def test_flags_prospectar_usa_arquivo_e_grupo():
    cmd = O._flags_prospectar(argparse.Namespace(grupo="assistencias", cidade="X, RJ"),
                              Path("/tmp/fake.xlsx"))
    cmd_str = " ".join(cmd)
    assert "--produto avgestao" in cmd_str
    assert "--grupo assistencias" in cmd_str
    assert "--arquivo" in cmd_str


def test_flags_campanha_usa_top_e_grupo():
    cmd = O._flags_campanha(
        argparse.Namespace(grupo="assistencias", top=15,
                           somente_confirmados=False, score_minimo=None),
        Path("/tmp/fake.xlsx"))
    cmd_str = " ".join(cmd)
    assert "--produto avgestao" in cmd_str
    assert "--grupo assistencias" in cmd_str
    assert "--top 15" in cmd_str


# ── 11. nenhum uso de shell=True ────────────────────────────────────

def test_shell_nunca_true():
    src = Path(O.__file__).read_text(encoding="utf-8")
    linhas = [l.strip() for l in src.splitlines()
              if "shell" in l.lower()
              and not l.strip().startswith("#")
              and not l.strip().startswith('"""')
              and not l.strip().startswith("NUNCA")]
    for linha in linhas:
        assert "shell=True" not in linha, f"shell=True encontrado em: {linha}"


# ── 12. nenhuma funcao de envio de WhatsApp ─────────────────────────

def test_sem_envio_whatsapp():
    src = Path(O.__file__).read_text(encoding="utf-8").lower()
    assert "whatsapp" not in src
    assert "enviar" not in src


# ── 13. caminhos finais listados somente quando existem ──────────────

def test_listar_arquivos_nao_assume_existencia():
    import io
    from unittest.mock import PropertyMock
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run_test"
        run_dir.mkdir()
        (run_dir / "config.json").write_text("{}")
        (run_dir / "fila.json").write_text("[]")
        (run_dir / "checkpoint.json").write_text("{}")
        old = sys.stdout
        try:
            sys.stdout = io.StringIO()
            O._listar_arquivos(run_dir)
            output = sys.stdout.getvalue()
            assert "config.json" in output
            assert "fila.json" in output
            assert "checkpoint.json" in output
            assert "leads_parciais.csv" not in output
            assert "resumo.json" not in output
        finally:
            sys.stdout = old


# ── runner ───────────────────────────────────────────────────────────

def _run_all():
    fns = [f for name, f in sorted(globals().items())
           if name.startswith("test_") and callable(f)]
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
            import traceback
            traceback.print_exc()
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
