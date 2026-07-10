"""
config/lock.py — Lock global e lock por run para o captador AVGESTAO.

Usa msvcrt.locking() no Windows para trava real do SO.
Nao usa portalocker nem dependencias externas.

Uso:
    with LockGlobal(run_id) as lock:
        if lock.acquired:
            # executa captacao
            ...

    with LockRun(run_id) as lock:
        if lock.acquired:
            # processa run
            ...
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import msvcrt  # Windows only
except ImportError:
    msvcrt = None  # type: ignore


LOCK_DIR = Path("output/avgestao")
GLOBAL_LOCK_FILE = LOCK_DIR / "captador_global.lock"
HEARTBEAT_INTERVAL = 30  # segundos


class LockError(Exception):
    """Erro relacionado a lock do captador."""


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _comando() -> str:
    """Retorna a linha de comando atual truncada."""
    try:
        return " ".join(sys.argv)[:500]
    except Exception:
        return ""


def _ler_metadados(caminho: Path) -> Optional[dict]:
    """Le metadados do arquivo de lock, se existir e for valido."""
    try:
        if caminho.exists() and caminho.stat().st_size > 0:
            return json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _escrever_metadados(caminho: Path, metadados: dict, fd: Optional[int] = None) -> None:
    """Escreve metadados no arquivo de lock.

    No Windows, quando o arquivo tem um lock ativo via msvcrt.locking(),
    Path.write_text() falha com PermissionError porque tenta abrir um segundo
    handle. Nesse caso, escrevemos diretamente via fd (os.write) que já está
    aberto e com o lock adquirido.

    Se fd não for fornecido ou for inválido (ex: mock em testes), usa write_text.
    """
    conteudo = json.dumps(metadados, ensure_ascii=False, indent=2)
    if fd is not None:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            dados = conteudo.encode("utf-8")
            os.write(fd, dados)
            os.fsync(fd)
            return
        except OSError:
            # fd inválido (mock em testes) — fallback para write_text
            pass
    caminho.write_text(conteudo, encoding="utf-8")


def _lock_arquivo(caminho: Path) -> Optional[int]:
    """Adquire lock real do SO no arquivo. Retorna fd ou None se falhar.

    No Windows usa msvcrt.locking() com LK_NBLCK (non-blocking).
    Fora do Windows, usa lockf (fallback parcial).
    """
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        if not caminho.exists():
            caminho.touch()
        fd = os.open(str(caminho), os.O_RDWR | os.O_CREAT)
        if msvcrt is not None:
            # Windows: lock real com non-blocking
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            # POSIX fallback
            import fcntl
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB, 1)
        return fd
    except (OSError, BlockingIOError, ImportError):
        # Lock ja adquirido por outro processo
        try:
            os.close(fd)  # type: ignore
        except Exception:
            pass
        return None
    except Exception:
        return None


def _unlock_arquivo(fd: int) -> None:
    """Libera lock real do SO."""
    try:
        if msvcrt is not None:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.lockf(fd, fcntl.LOCK_UN, 1)
        os.close(fd)
    except Exception:
        try:
            os.close(fd)
        except Exception:
            pass


def _pid_esta_vivo(pid: int) -> bool:
    """Verifica se um PID esta ativo no sistema.

    Nao usa os.kill (sinal real) para evitar qualquer interacao com
    grupo de console ou processo-pai. No Windows usa OpenProcess via
    ctypes com PROCESS_QUERY_LIMITED_INFORMATION; no POSIX usa /proc.

    Regras:
    - pid <= 0 retorna False (PID invalido).
    - ERROR_ACCESS_DENIED (5) significa que o processo existe mas
      nao temos permissao — retorna True (provavelmente ativo).
    - Todo handle aberto e fechado com CloseHandle em finally.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            try:
                if handle:
                    return True
                # Handle NULL — verifica por que falhou
                err = ctypes.windll.kernel32.GetLastError()
                # ERROR_ACCESS_DENIED = 5: processo existe, sem permissao
                if err == 5:
                    return True
                return False
            finally:
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    # POSIX: verifica via /proc (sem enviar sinal)
    try:
        return os.path.isdir(f"/proc/{pid}")
    except Exception:
        return False


class LockGlobal:
    """Lock global de captacao: apenas uma instancia por maquina.

    Uso:
        with LockGlobal(run_id) as lock:
            if not lock.acquired:
                print("Ja existe captacao ativa")
                return
            # executa captacao
    """

    def __init__(self, run_id: str, comando: str = ""):
        self.run_id = run_id
        self.comando = comando or _comando()
        self.fd: Optional[int] = None
        self.acquired = False
        self.metadados_stale: Optional[dict] = None

    def __enter__(self) -> "LockGlobal":
        self._adquirir()
        return self

    def __exit__(self, *args) -> None:
        self.liberar()

    def _adquirir(self) -> None:
        """Tenta adquirir o lock global.

        Se o lock estiver ocupado, verifica se o PID dono ainda esta vivo.
        Se nao estiver (lock abandonado), recupera.
        """
        # Tenta adquirir lock real
        fd = _lock_arquivo(GLOBAL_LOCK_FILE)
        if fd is not None:
            # Conseguiu o lock
            self.fd = fd
            self.acquired = True
            metadados = {
                "pid": os.getpid(),
                "run_id": self.run_id,
                "inicio": _agora_iso(),
                "hostname": _hostname(),
                "comando": self.comando,
                "tipo": "global",
            }
            _escrever_metadados(GLOBAL_LOCK_FILE, metadados, fd=fd)
            return

        # Lock ocupado — verifica se o dono ainda vive
        metadados = _ler_metadados(GLOBAL_LOCK_FILE)
        if metadados:
            pid_dono = metadados.get("pid")
            if pid_dono and not _pid_esta_vivo(pid_dono):
                # Lock abandonado — recupera
                self.metadados_stale = metadados
                stale_path = GLOBAL_LOCK_FILE.with_name(
                    GLOBAL_LOCK_FILE.stem + f".stale_{int(time.time())}.lock"
                )
                try:
                    GLOBAL_LOCK_FILE.rename(stale_path)
                except Exception:
                    pass
                # Tenta novamente
                fd = _lock_arquivo(GLOBAL_LOCK_FILE)
                if fd is not None:
                    self.fd = fd
                    self.acquired = True
                    metadados = {
                        "pid": os.getpid(),
                        "run_id": self.run_id,
                        "inicio": _agora_iso(),
                        "hostname": _hostname(),
                        "comando": self.comando,
                        "tipo": "global",
                        "recuperado_de": str(stale_path),
                    }
                    _escrever_metadados(GLOBAL_LOCK_FILE, metadados, fd=fd)
                    return

        # Nao conseguiu — mostra info do dono
        if metadados:
            print(
                f"  Já existe uma captação ativa:\n"
                f"    PID: {metadados.get('pid')}\n"
                f"    Run ID: {metadados.get('run_id')}\n"
                f"    Início: {metadados.get('inicio')}\n"
                f"    Comando: {metadados.get('comando', '')[:100]}"
            )

    def liberar(self) -> None:
        """Libera o lock global."""
        if self.fd is not None:
            _unlock_arquivo(self.fd)
            self.fd = None
            self.acquired = False
            # Limpa metadados (so se ainda for nosso)
            try:
                if GLOBAL_LOCK_FILE.exists():
                    GLOBAL_LOCK_FILE.unlink()
            except Exception:
                pass


class LockRun:
    """Lock por run: mesmo run_id nunca processado por dois processos.

    Uso:
        with LockRun(run_id) as lock:
            if not lock.acquired:
                print("Run ja esta sendo processado")
                return
            # processa run
    """

    def __init__(self, run_id: str, comando: str = ""):
        self.run_id = run_id
        self.comando = comando or _comando()
        self.fd: Optional[int] = None
        self.acquired = False
        self.caminho = LOCK_DIR / "runs" / run_id / "run.lock"

    def __enter__(self) -> "LockRun":
        self._adquirir()
        return self

    def __exit__(self, *args) -> None:
        self.liberar()

    def _adquirir(self) -> None:
        """Tenta adquirir o lock do run."""
        fd = _lock_arquivo(self.caminho)
        if fd is not None:
            self.fd = fd
            self.acquired = True
            metadados = {
                "pid": os.getpid(),
                "run_id": self.run_id,
                "inicio": _agora_iso(),
                "hostname": _hostname(),
                "comando": self.comando,
                "tipo": "run",
            }
            _escrever_metadados(self.caminho, metadados, fd=fd)
            return

        # Lock ocupado
        metadados = _ler_metadados(self.caminho)
        if metadados:
            pid_dono = metadados.get("pid")
            if pid_dono and not _pid_esta_vivo(pid_dono):
                # Lock abandonado
                self.metadados_stale = metadados
                stale_path = self.caminho.with_name(
                    self.caminho.stem + f".stale_{int(time.time())}.lock"
                )
                try:
                    self.caminho.rename(stale_path)
                except Exception:
                    pass
                fd = _lock_arquivo(self.caminho)
                if fd is not None:
                    self.fd = fd
                    self.acquired = True
                    metadados = {
                        "pid": os.getpid(),
                        "run_id": self.run_id,
                        "inicio": _agora_iso(),
                        "hostname": _hostname(),
                        "comando": self.comando,
                        "tipo": "run",
                        "recuperado_de": str(stale_path),
                    }
                    _escrever_metadados(self.caminho, metadados, fd=fd)
                    return

            print(
                f"  Run {self.run_id} já está sendo processado:\n"
                f"    PID: {metadados.get('pid')}\n"
                f"    Início: {metadados.get('inicio')}"
            )

    def liberar(self) -> None:
        """Libera o lock do run."""
        if self.fd is not None:
            _unlock_arquivo(self.fd)
            self.fd = None
            self.acquired = False
            try:
                if self.caminho.exists():
                    self.caminho.unlink()
            except Exception:
                pass


def verificar_lock_global() -> Optional[dict]:
    """Verifica se existe lock global ativo (sem adquirir).

    Retorna metadados do dono ou None se livre/abandonado.
    """
    metadados = _ler_metadados(GLOBAL_LOCK_FILE)
    if not metadados:
        return None
    pid = metadados.get("pid")
    if pid and _pid_esta_vivo(pid):
        return metadados
    # Abandonado
    return None
