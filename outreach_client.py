#!/usr/bin/env python3
"""
Wrapper para chamar as RPCs de lead_outreach de forma segura.

Usa SUPABASE_SERVICE_ROLE_KEY para operações de escrita (reserve, settle,
confirm, release) e SUPABASE_ANON_KEY para leitura (get_outreach_state).

A service role key é carregada apenas do .env local, nunca enviada ao
navegador, nunca commitada e nunca registrada em logs.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

logger = logging.getLogger(__name__)


def _carregar_env() -> None:
    """Carrega variáveis do .env se disponível."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())


def _get_client(key_type: str = "anon"):
    """
    Retorna um cliente Supabase configurado.

    Args:
        key_type: 'anon' para leitura, 'service_role' para escrita

    Returns:
        Cliente Supabase ou None se não configurado
    """
    if not HAS_SUPABASE:
        logger.error("Pacote 'supabase' não instalado. pip install supabase")
        return None

    _carregar_env()
    url = os.environ.get("SUPABASE_URL", "")

    if key_type == "service_role":
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not key:
            logger.error(
                "SUPABASE_SERVICE_ROLE_KEY não encontrada no .env. "
                "Esta chave é necessária para operações de escrita. "
                "Adicione ao .env: SUPABASE_SERVICE_ROLE_KEY=<sua_chave>"
            )
            return None
    else:
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if not key:
            logger.error("SUPABASE_ANON_KEY não encontrada no .env")
            return None

    return create_client(url, key)


# ============================================================
# RPCs de LEITURA (anon key)
# ============================================================

def get_outreach_state(
    phone_normalized: str,
    campaign_key: str
) -> dict[str, Any] | None:
    """
    Consulta o estado de outreach para um telefone + campanha.

    Args:
        phone_normalized: Telefone canônico (ex: 5521999999999)
        campaign_key: Chave da campanha

    Returns:
        Dict com 'outcome', 'status', 'campaign_match', 'message_timestamp'
        ou None se erro de configuração
    """
    client = _get_client("anon")
    if not client:
        return None

    try:
        result = client.rpc(
            "get_outreach_state",
            {
                "p_phone_normalized": phone_normalized,
                "p_campaign_key": campaign_key,
            }
        ).execute()
        return result.data if result.data else {"outcome": "none"}
    except Exception as e:
        logger.warning("Erro ao consultar outreach state: %s", e)
        return {"outcome": "error", "error_code": "client_error"}


# ============================================================
# RPCs de ESCRITA (service role key)
# ============================================================

def reserve_outreach(
    phone_normalized: str,
    campaign_key: str,
    lead_id: str,
    source: str = "sender:auto"
) -> dict[str, Any] | None:
    """
    Reserva atomicamente um lead para envio.

    Args:
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        lead_id: UUID do lead
        source: Origem da reserva

    Returns:
        Dict com 'outcome', 'reservation_id', 'reservation_token',
        'expires_at' em caso de sucesso, ou 'outcome' de erro
    """
    client = _get_client("service_role")
    if not client:
        return None

    try:
        result = client.rpc(
            "reserve_outreach",
            {
                "p_phone_normalized": phone_normalized,
                "p_campaign_key": campaign_key,
                "p_lead_id": lead_id,
                "p_source": source,
            }
        ).execute()
        return result.data if result.data else {"outcome": "error"}
    except Exception as e:
        logger.warning("Erro ao reservar lead: %s", e)
        return {"outcome": "error", "error_code": "client_error"}


def settle_outreach(
    reservation_id: str,
    reservation_token: str,
    new_status: str,
    message_timestamp: str | None = None,
    fingerprint: str | None = None,
    campaign_match: bool | None = None,
    obs: str | None = None,
) -> dict[str, Any] | None:
    """
    Finaliza uma reserva (sent, failed, released, needs_reconciliation).

    Args:
        reservation_id: UUID da reserva
        reservation_token: Token de posse
        new_status: Novo status
        message_timestamp: Timestamp ISO da mensagem
        fingerprint: Hash do texto da mensagem
        campaign_match: Se a mensagem corresponde à campanha
        obs: Observação para lead_interactions

    Returns:
        Dict com 'outcome' e 'status'
    """
    client = _get_client("service_role")
    if not client:
        return None

    params = {
        "p_reservation_id": reservation_id,
        "p_reservation_token": reservation_token,
        "p_new_status": new_status,
    }
    if message_timestamp is not None:
        params["p_message_timestamp"] = message_timestamp
    if fingerprint is not None:
        params["p_fingerprint"] = fingerprint
    if campaign_match is not None:
        params["p_campaign_match"] = campaign_match
    if obs is not None:
        params["p_obs"] = obs

    try:
        result = client.rpc("settle_outreach", params).execute()
        return result.data if result.data else {"outcome": "error"}
    except Exception as e:
        logger.warning("Erro ao finalizar reserva: %s", e)
        return {"outcome": "error", "error_code": "client_error"}


def confirm_outreach_from_whatsapp(
    phone_normalized: str,
    campaign_key: str,
    lead_id: str,
    message_timestamp: str,
    fingerprint: str,
    campaign_match: bool,
    source: str = "whatsapp_reconciliation",
) -> dict[str, Any] | None:
    """
    Confirma abordagem via reconciliação do WhatsApp.

    Args:
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        lead_id: UUID do lead
        message_timestamp: Timestamp ISO da mensagem
        fingerprint: Hash do texto da mensagem
        campaign_match: Se a mensagem corresponde à campanha
        source: Origem da confirmação

    Returns:
        Dict com 'outcome'
    """
    client = _get_client("service_role")
    if not client:
        return None

    try:
        result = client.rpc(
            "confirm_outreach_from_whatsapp",
            {
                "p_phone_normalized": phone_normalized,
                "p_campaign_key": campaign_key,
                "p_lead_id": lead_id,
                "p_message_timestamp": message_timestamp,
                "p_fingerprint": fingerprint,
                "p_campaign_match": campaign_match,
                "p_source": source,
            }
        ).execute()
        return result.data if result.data else {"outcome": "error"}
    except Exception as e:
        logger.warning("Erro ao confirmar outreach: %s", e)
        return {"outcome": "error", "error_code": "client_error"}


def release_reconciliation(
    phone_normalized: str,
    campaign_key: str,
    reason: str = "manual_review",
) -> dict[str, Any] | None:
    """
    Libera um needs_reconciliation (apenas fluxo manual/auditado).

    Args:
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        reason: Motivo da liberação

    Returns:
        Dict com 'outcome'
    """
    client = _get_client("service_role")
    if not client:
        return None

    try:
        result = client.rpc(
            "release_reconciliation",
            {
                "p_phone_normalized": phone_normalized,
                "p_campaign_key": campaign_key,
                "p_reason": reason,
            }
        ).execute()
        return result.data if result.data else {"outcome": "error"}
    except Exception as e:
        logger.warning("Erro ao liberar reconciliação: %s", e)
        return {"outcome": "error", "error_code": "client_error"}
