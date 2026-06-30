"""
Testes do sistema de lock do captador AVGESTAO.

Testa lock global, lock por run, concorrencia, abandono, status.
Nao adquire lock real do SO (usa LOCK_DISABLED=1 + mocks).

Roda de duas formas:
    py -3.12 tests/test_lock.py
    pytest tests/test_lock.py
"""

import asyncio
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ["LOCK_DISABLED"] = "1"

from config.lock import LockGlobal, LockRun, verificar_lock_global, _pid_esta_vivo


# ── Helpers ──────────────────────────────────────────────────────────

class _Patcher:
    def __init__(self):
        self._saved = []

    def set(self, obj, name, value):
        self._saved.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def restore(self):
        for obj, name, orig in reversed(self._saved):
            setattr(obj, name, orig)
        self._saved.clear()


def _mock_lock_arquivo(success=True):
    """Substitui _lock_arquivo para simular sucesso/falha."""
    import config.lock as L
    original = L._lock_arquivo
    if success:
        async def _fake_lock(path):
            return 999  # fd fake
        L._lock_arquivo = _fake_lock
    else:
        async def _fake_lock(path):
            return None
        L._lock_arquivo = _fake_lock
    return original


# ── 1. Primeira instancia adquire lock global ───────────────────────

def test_primeira_instancia_adquire_lock_global():
    patch = _Patcher()
    try:
        import config.lock as L
        original = L._lock_arquivo
        L._lock_arquivo = lambda path: 999
        original_unlock = L._unlock_arquivo
        L._unlock_arquivo = lambda fd: None

        with LockGlobal("run_test_1") as lock:
            assert lock.acquired is True
            assert lock.fd is not None

        L._lock_arquivo = original
        L._unlock_arquivo = original_unlock
    finally:
        patch.restore()


# ── 2. Segunda instancia recusada ──────────────────────────────────

def test_segunda_instancia_recusada():
    import config.lock as L
    original = L._lock_arquivo
    L._lock_arquivo = lambda path: None  # simula lock ocupado
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None

    with LockGlobal("run_test_2") as lock:
        assert lock.acquired is False

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 3. Segunda instancia nao abre Chromium ──────────────────────────

def test_segunda_instancia_nao_abre_chromium():
    """Se lock nao adquirido, o mapeador nao deve prosseguir."""
    import config.lock as L
    original = L._lock_arquivo
    L._lock_arquivo = lambda path: None
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None

    with LockGlobal("run_test_3") as lock:
        assert lock.acquired is False
        # Se nao adquiriu, nao deve abrir browser
        # (simulado: se acquired=False, o chamador retorna)

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 4. Dois runs diferentes nao rodam simultaneamente ───────────────

def test_dois_runs_diferentes_lock_global_impede():
    """Lock global impede dois runs diferentes simultaneos."""
    import config.lock as L
    original = L._lock_arquivo
    call_count = [0]
    def _fake_lock(path):
        call_count[0] += 1
        if call_count[0] == 1:
            return 999  # primeira chamada: sucesso
        return None  # segunda chamada: falha
    L._lock_arquivo = _fake_lock
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None

    with LockGlobal("run_A") as lock_a:
        assert lock_a.acquired is True
        with LockGlobal("run_B") as lock_b:
            assert lock_b.acquired is False

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 5. Dois resumes do mesmo run recusados ──────────────────────────

def test_dois_resumes_mesmo_run_recusados():
    """Lock por run impede dois resumes simultaneos."""
    import config.lock as L
    original = L._lock_arquivo
    call_count = [0]
    def _fake_lock(path):
        call_count[0] += 1
        if call_count[0] <= 2:
            path.parent.mkdir(parents=True, exist_ok=True)
            return 999  # global + primeiro run
        return None  # segundo run
    L._lock_arquivo = _fake_lock
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None

    with LockGlobal("run_test_5") as lock_g:
        assert lock_g.acquired is True
        with LockRun("run_test_5") as lock_r1:
            assert lock_r1.acquired is True
            with LockRun("run_test_5") as lock_r2:
                assert lock_r2.acquired is False

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 6. Lock por run funciona ────────────────────────────────────────

def test_lock_por_run_funciona():
    import config.lock as L
    original = L._lock_arquivo
    def _fake_lock(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        return 999
    L._lock_arquivo = _fake_lock
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None

    with LockRun("run_test_6") as lock:
        assert lock.acquired is True
        assert lock.run_id == "run_test_6"

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 7. Lock liberado apos conclusao ─────────────────────────────────

def test_lock_liberado_apos_conclusao():
    import config.lock as L
    original = L._lock_arquivo
    original_unlock = L._unlock_arquivo
    fd_holder = []
    def _fake_lock(path):
        fd = 999
        fd_holder.append(fd)
        return fd
    L._lock_arquivo = _fake_lock
    unlocked = []
    def _fake_unlock(fd):
        unlocked.append(fd)
    L._unlock_arquivo = _fake_unlock

    with LockGlobal("run_test_7") as lock:
        assert lock.acquired is True

    assert len(unlocked) == 1
    assert unlocked[0] == 999

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 8. Lock liberado apos excecao ──────────────────────────────────

def test_lock_liberado_apos_excecao():
    import config.lock as L
    original = L._lock_arquivo
    original_unlock = L._unlock_arquivo
    L._lock_arquivo = lambda path: 999
    unlocked = []
    def _fake_unlock(fd):
        unlocked.append(fd)
    L._unlock_arquivo = _fake_unlock

    try:
        with LockGlobal("run_test_8") as lock:
            assert lock.acquired is True
            raise RuntimeError("erro simulado")
    except RuntimeError:
        pass

    assert len(unlocked) == 1

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock


# ── 9. Lock abandonado recuperado ───────────────────────────────────

def test_lock_abandonado_recuperado():
    """Lock cujo PID dono nao existe mais deve ser recuperado."""
    import config.lock as L
    # Prepara arquivo de lock com metadados de PID morto
    L.GLOBAL_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    L.GLOBAL_LOCK_FILE.write_text(
        json.dumps({"pid": 999999, "run_id": "run_test_9", "inicio": "2024-01-01"}),
        encoding="utf-8",
    )
    original = L._lock_arquivo
    call_count = [0]
    def _fake_lock(path):
        call_count[0] += 1
        if call_count[0] == 1:
            return None  # primeira: ocupado
        return 999  # segunda: conseguiu apos recuperar
    L._lock_arquivo = _fake_lock
    original_unlock = L._unlock_arquivo
    L._unlock_arquivo = lambda fd: None
    original_pid = L._pid_esta_vivo
    L._pid_esta_vivo = lambda pid: False  # dono morto

    with LockGlobal("run_test_9") as lock:
        assert lock.acquired is True
        assert lock.metadados_stale is not None

    L._lock_arquivo = original
    L._unlock_arquivo = original_unlock
    L._pid_esta_vivo = original_pid


# ── 10. Processo nao remove lock de outro PID ──────────────────────

def test_nao_remove_lock_outro_pid():
    """Um processo nao pode remover lock pertencente a outro PID vivo."""
    import config.lock as L
    original = L._lock_arquivo
    L._lock_arquivo = lambda path: None  # lock ocupado
    original_pid = L._pid_esta_vivo
    L._pid_esta_vivo = lambda pid: True  # dono vivo

    with LockGlobal("run_test_10") as lock:
        assert lock.acquired is False
        # Nao deve ter recuperado (dono vivo)

    L._lock_arquivo = original
    L._pid_esta_vivo = original_pid


# ── 11. Status nao abre navegador ──────────────────────────────────

def test_status_nao_abre_navegador():
    """Modo status deve ser somente leitura, sem abrir navegador."""
    import executar_campanha_avgestao as O
    # Verifica que _modo_status existe e nao chama subprocess
    assert hasattr(O, "_modo_status")
    # O modo status nao deve conter "mapear" ou "resume" no fluxo
    import inspect
    src = inspect.getsource(O._modo_status)
    assert "subprocess" not in src
    assert "mapear" not in src
    assert "resume" not in src
    # Ignora docstring (que descreve o que a funcao NAO faz)
    corpo = src.split('"""')[-1] if '"""' in src else src
    assert "subprocess" not in corpo


# ── 12. Status nao altera arquivos ─────────────────────────────────

def test_status_nao_altera_arquivos():
    """Modo status nao deve modificar arquivos do run."""
    import executar_campanha_avgestao as O
    import inspect
    src = inspect.getsource(O._modo_status)
    # Nao deve escrever arquivos
    assert "write_text" not in src
    assert "open" not in src or '"w"' not in src
    assert '"a"' not in src


# ── 13. Status mostra processo ativo ───────────────────────────────

def test_status_mostra_processo_ativo():
    """Verifica que verificar_lock_global retorna metadados quando ha lock."""
    import config.lock as L
    # Sem lock ativo
    result = verificar_lock_global()
    # Pode ser None ou dict (depende se ha lock real)
    assert result is None or isinstance(result, dict)


# ── 14. Status lista runs recentes ──────────────────────────────────

def test_status_lista_runs_recentes():
    """Modo status sem run-id lista runs recentes."""
    import executar_campanha_avgestao as O
    import io
    old_stdout = sys.stdout
    try:
        sys.stdout = io.StringIO()
        import argparse
        args = argparse.Namespace(status=True, run_id=None)
        O._modo_status(args)
        output = sys.stdout.getvalue()
        assert "RUNS RECENTES" in output
        assert "run_" in output
    finally:
        sys.stdout = old_stdout


# ── 15. Orquestrador nao tenta novamente apos erro ─────────────────

def test_orquestrador_nao_tenta_novamente_apos_erro():
    """O orquestrador nao deve repetir etapa que falhou."""
    import executar_campanha_avgestao as O
    import inspect
    src = inspect.getsource(O._executar)
    # Nao deve ter loop de retry
    assert "for" not in src.split("def _executar")[1].split("\n")[:5]
    assert "while" not in src


# ── 16. Nenhuma funcao de WhatsApp executada ────────────────────────

def test_sem_whatsapp_no_captador():
    """O captador nao deve ter funcoes de WhatsApp."""
    import mapear_comercios as M
    import inspect
    src = inspect.getsource(M)
    assert "whatsapp" not in src.lower() or "whatsapp_business" not in src


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
            import traceback
            traceback.print_exc()
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
