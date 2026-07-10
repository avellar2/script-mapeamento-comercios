"""
config/lock_whatsapp_match.py — Lock exclusivo do sincronizador WhatsApp.

Usa perfil próprio (profiles/whatsapp_match) e lock próprio
(output/avgestao/whatsapp_match.lock).

Não compartilha com captador_global.lock nem com whatsapp_sender_global.lock.

Quando ocupado: recusa a nova execução, não mata o processo existente,
não abre outra janela.
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
MATCH_LOCK_FILE = LOCK_DIR / "whatsapp_match.lock"


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _comando() -> str:
    try:
        return " ".join(sys.argv)[:500]
    except Exception:
        return ""


def _ler_metadados(caminho: Path) -> Optional[dict]:
    try:
        if caminho.exists() and caminho.stat().st_size > 0:
            return json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _escrever_metadados(caminho: Path, metadados: dict, fd: Optional[int] = None) -> None:
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
            pass
    caminho.write_text(conteudo, encoding="utf-8")


def _lock_arquivo(caminho: Path) -> Optional[int]:
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        if not caminho.exists():
            caminho.touch()
        fd = os.open(str(caminho), os.O_RDWR | os.O_CREAT)
        if msvcrt is not None:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB, 1)
        return fd
    except (OSError, BlockingIOError, ImportError):
        try:
            os.close(fd)  # type: ignore
        except Exception:
            pass
        return None
    except Exception:
        return None


def _unlock_arquivo(fd: int) -> None:
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
                err = ctypes.windll.kernel32.GetLastError()
                if err == 5:
                    return True
                return False
            finally:
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    try:
        return os.path.isdir(f"/proc/{pid}")
    except Exception:
        return False


class LockWhatsAppMatch:
    """Lock exclusivo do sincronizador WhatsApp.

    Uso:
        with LockWhatsAppMatch() as lock:
            if not lock.acquired:
                print("Já existe sincronização ativa.")
                sys.exit(1)
            # executa sincronização
    """

    def __init__(self, comando: str = ""):
        self.comando = comando or _comando()
        self.fd: Optional[int] = None
        self.acquired = False

    def __enter__(self) -> "LockWhatsAppMatch":
        self._adquirir()
        return self

    def __exit__(self, *args) -> None:
        self.liberar()

    def _adquirir(self) -> None:
        fd = _lock_arquivo(MATCH_LOCK_FILE)
        if fd is not None:
            self.fd = fd
            self.acquired = True
            metadados = {
                "pid": os.getpid(),
                "inicio": _agora_iso(),
                "hostname": _hostname(),
                "comando": self.comando,
                "tipo": "whatsapp_match",
            }
            _escrever_metadados(MATCH_LOCK_FILE, metadados, fd=fd)
            return

        metadados = _ler_metadados(MATCH_LOCK_FILE)
        if metadados:
            pid_dono = metadados.get("pid")
            if pid_dono and not _pid_esta_vivo(pid_dono):
                stale_path = MATCH_LOCK_FILE.with_name(
                    MATCH_LOCK_FILE.stem + f".stale_{int(time.time())}.lock"
                )
                try:
                    MATCH_LOCK_FILE.rename(stale_path)
                except Exception:
                    return
                fd = _lock_arquivo(MATCH_LOCK_FILE)
                if fd is not None:
                    self.fd = fd
                    self.acquired = True
                    metadados = {
                        "pid": os.getpid(),
                        "inicio": _agora_iso(),
                        "hostname": _hostname(),
                        "comando": self.comando,
                        "tipo": "whatsapp_match",
                    }
                    _escrever_metadados(MATCH_LOCK_FILE, metadados, fd=fd)
                    return

        self.acquired = False

    def liberar(self) -> None:
        if self.fd is not None:
            _unlock_arquivo(self.fd)
            self.fd = None
            self.acquired = False
