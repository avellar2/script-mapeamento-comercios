"""
Testes de atomicidade da reserva (concorrência).

REQUER banco PostgreSQL/Supabase local com migration aplicada.
Não executa em produção.

Roda com:
    python -m pytest tests/test_reserva_atomicidade.py -v -s
"""

import os
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    reason="SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY necessários"
)

from outreach_client import reserve_outreach


LEAD_ID = "00000000-0000-0000-0000-000000000001"
PHONE = "5521999999999"
CAMPAIGN_KEY = "avgestao:assistencias:primeiro_contato:v1"


def test_duas_reservas_concorrentes():
    """Duas reservas concorrentes: apenas uma vence."""
    resultados = []
    lock = threading.Lock()

    def reservar():
        result = reserve_outreach(PHONE, CAMPAIGN_KEY, LEAD_ID, "sender:test")
        with lock:
            resultados.append(result)

    t1 = threading.Thread(target=reservar)
    t2 = threading.Thread(target=reservar)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(resultados) == 2

    outcomes = [r.get("outcome") for r in resultados if r]
    # Pelo menos um deve ser reserved
    assert "reserved" in outcomes
    # Pelo menos um deve ser reserved_by_other ou already_sent
    assert any(o in ("reserved_by_other", "already_sent", "already_confirmed") for o in outcomes)


def test_reserva_idempotente():
    """Mesma reserva repetida é idempotente."""
    r1 = reserve_outreach(PHONE, CAMPAIGN_KEY, LEAD_ID, "sender:test")
    r2 = reserve_outreach(PHONE, CAMPAIGN_KEY, LEAD_ID, "sender:test")

    assert r1 is not None
    assert r2 is not None

    # A segunda deve ser recusada (reserved_by_other, already_sent, etc.)
    assert r2.get("outcome") in (
        "reserved_by_other", "already_sent", "already_confirmed"
    )
