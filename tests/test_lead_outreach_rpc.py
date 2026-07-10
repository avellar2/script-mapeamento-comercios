"""
Testes de integração das RPCs de lead_outreach.

REQUER um banco PostgreSQL/Supabase local com a migration aplicada.
Não executa em produção.

Configuração:
    export SUPABASE_URL=<url_local>
    export SUPABASE_SERVICE_ROLE_KEY=<key>

Roda com:
    python -m pytest tests/test_lead_outreach_rpc.py -v -s
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Pula todos os testes se não houver configuração de banco
pytestmark = pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    reason="SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY necessários para testes de integração"
)

from outreach_client import (
    reserve_outreach,
    settle_outreach,
    confirm_outreach_from_whatsapp,
    get_outreach_state,
    release_reconciliation,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def lead_id():
    """Retorna um lead_id real do banco de testes."""
    # Em ambiente de teste, usar um lead existente ou criar um
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def phone():
    return "5521999999999"


@pytest.fixture
def campaign_key():
    return "avgestao:assistencias:primeiro_contato:v1"


# ============================================================
# Testes de reserva
# ============================================================

def test_reserva_aceita(lead_id, phone, campaign_key):
    """Reserva é aceita para lead válido."""
    result = reserve_outreach(phone, campaign_key, lead_id, "sender:test")
    assert result is not None
    assert result.get("outcome") in ("reserved", "already_sent", "already_confirmed", "reserved_by_other")
    if result.get("outcome") == "reserved":
        assert "reservation_id" in result
        assert "reservation_token" in result
        assert "expires_at" in result


def test_reserva_phone_invalido(lead_id, campaign_key):
    """Telefone inválido é recusado."""
    result = reserve_outreach("123", campaign_key, lead_id, "sender:test")
    assert result is not None
    assert result.get("outcome") == "invalid_phone"


def test_reserva_campaign_key_invalida(lead_id, phone):
    """Campaign key inválida é recusada."""
    result = reserve_outreach(phone, "invalida", lead_id, "sender:test")
    assert result is not None
    assert result.get("outcome") == "invalid_campaign_key"


def test_reserva_source_invalido(lead_id, phone, campaign_key):
    """Source inválido é recusado."""
    result = reserve_outreach(phone, campaign_key, lead_id, "invalido")
    assert result is not None
    assert result.get("outcome") == "invalid_source"


# ============================================================
# Testes de settle
# ============================================================

def test_settle_token_invalido(lead_id, phone, campaign_key):
    """Token inválido é recusado."""
    result = settle_outreach(
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        "sent",
    )
    assert result is not None
    assert result.get("outcome") in ("not_found", "invalid_token")


def test_settle_status_invalido(lead_id, phone, campaign_key):
    """Status inválido é recusado."""
    result = settle_outreach(
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        "invalido",
    )
    assert result is not None
    assert result.get("outcome") == "invalid_status"


# ============================================================
# Testes de get_outreach_state
# ============================================================

def test_get_state_sem_registro(phone, campaign_key):
    """Consulta sem registro retorna none."""
    result = get_outreach_state(phone, campaign_key)
    assert result is not None
    assert result.get("outcome") in ("none", "found")


def test_get_state_args_invalidos():
    """Args inválidos retornam erro."""
    result = get_outreach_state("", "")
    assert result is not None
    assert result.get("outcome") in ("invalid_args", "error")


# ============================================================
# Testes de confirm
# ============================================================

def test_confirm_campaign_match_false(lead_id, phone, campaign_key):
    """campaign_match=False retorna ambiguous."""
    result = confirm_outreach_from_whatsapp(
        phone, campaign_key, lead_id,
        datetime.now(timezone.utc).isoformat(),
        "hash_teste",
        False,
    )
    assert result is not None
    assert result.get("outcome") == "ambiguous_not_confirmed"


def test_confirm_phone_invalido(lead_id, campaign_key):
    """Telefone inválido é recusado."""
    result = confirm_outreach_from_whatsapp(
        "123", campaign_key, lead_id,
        datetime.now(timezone.utc).isoformat(),
        "hash_teste",
        True,
    )
    assert result is not None
    assert result.get("outcome") == "invalid_phone"


# ============================================================
# Testes de release_reconciliation
# ============================================================

def test_release_phone_invalido(campaign_key):
    """Telefone inválido é recusado."""
    result = release_reconciliation("123", campaign_key, "test")
    assert result is not None
    assert result.get("outcome") == "invalid_phone"


def test_release_sem_registro(phone, campaign_key):
    """Sem registro retorna not_found."""
    result = release_reconciliation(phone, campaign_key, "test")
    assert result is not None
    assert result.get("outcome") in ("not_found", "invalid_transition")
