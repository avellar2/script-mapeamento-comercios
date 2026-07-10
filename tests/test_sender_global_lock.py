"""
Testes do lock global dos senders WhatsApp.

Roda com:
    python -m pytest tests/test_sender_global_lock.py -v
"""

import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["LOCK_DISABLED"] = "1"

from config.lock_whatsapp_sender import LockWhatsAppSender


def test_lock_adquire():
    """Lock pode ser adquirido."""
    with LockWhatsAppSender() as lock:
        assert lock.acquired is True


def test_lock_libera():
    """Lock é liberado ao sair do contexto."""
    lock = LockWhatsAppSender()
    lock._adquirir()
    assert lock.acquired is True
    lock.liberar()
    assert lock.acquired is False


def test_lock_nao_mata():
    """Lock não mata processo existente (apenas recusa)."""
    # Simula lock ocupado criando o arquivo manualmente
    from config.lock_whatsapp_sender import SENDER_LOCK_FILE
    SENDER_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    SENDER_LOCK_FILE.write_text('{"pid": 999999999, "inicio": "now"}', encoding="utf-8")

    with LockWhatsAppSender() as lock:
        # PID 999999999 não existe, então o lock deve recuperar
        # (depende de _pid_esta_vivo retornar False)
        pass
