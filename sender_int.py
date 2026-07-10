#!/usr/bin/env python3
"""
supabase/sender_integration.py — Integração dos senders com lead_outreach.

Fornece helpers para:
- Lock global do perfil WhatsApp
- Normalização unificada de telefone
- Reserva atômica antes do envio
- Finalização atômica após envio
- Tratamento de estados incertos

Nunca faz PATCH separado em leads após settle.
Nunca casa lead por nome.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Adiciona raiz ao path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from config.lock_whatsapp_sender import LockWhatsAppSender
from utils.phone_utils import normalizar_telefone_br
from utils.campaign_key import PRIMEIRO_CONTATO_V1, gerar_campaign_key, validar_campaign_key

logger = logging.getLogger(__name__)


def get_supabase_client(key_type: str = "service_role"):
    """Retorna cliente Supabase."""
    try:
        from supabase import create_client
    except ImportError:
        logger.error("Pacote 'supabase' não instalado. pip install supabase")
        return None

    # Carrega .env
    env_path = Path(_root) / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        import os
                        os.environ.setdefault(k.strip(), v.strip())

    import os
    url = os.environ.get("SUPABASE_URL", "")
    if key_type == "service_role":
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not key:
            logger.error(
                "SUPABASE_SERVICE_ROLE_KEY não encontrada no .env. "
                "Adicione ao .env: SUPABASE_SERVICE_ROLE_KEY=<chave>"
            )
            return None
    else:
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if not key:
            logger.error("SUPABASE_ANON_KEY não encontrada no .env")
            return None

    return create_client(url, key)


def normalizar_telefone_lead(lead: dict) -> str | None:
    """
    Normaliza o telefone de um lead usando a função unificada.

    Args:
        lead: Dict com 'whatsapp', 'telefone', 'telefone_normalizado'

    Returns:
        Telefone canônico ou None se inválido
    """
    tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""
    return normalizar_telefone_br(tel)


def obter_campaign_key(lead: dict) -> str:
    """
    Obtém a campaign_key para um lead.

    Usa produto/grupo do lead ou defaults da campanha AVGESTÃO assistências.

    Args:
        lead: Dict com 'produto' e 'grupo'

    Returns:
        campaign_key
    """
    produto = lead.get("produto", "avgestao") or "avgestao"
    grupo = lead.get("grupo", "assistencias") or "assistencias"
    return gerar_campaign_key(produto, grupo, "primeiro_contato", "v1")


def reserve_lead(
    phone_normalized: str,
    campaign_key: str,
    lead_id: str,
    source: str = "sender:auto",
) -> dict[str, Any] | None:
    """
    Reserva atomicamente um lead para envio.

    Args:
        phone_normalized: Telefone canônico
        campaign_key: Chave da campanha
        lead_id: UUID do lead
        source: Origem da reserva

    Returns:
        Dict com 'outcome', 'reservation_id', 'reservation_token' ou erro
    """
    client = get_supabase_client("service_role")
    if not client:
        return {"outcome": "error", "error_code": "no_client"}

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
        logger.warning("Erro ao reservar lead %s: %s", lead_id, e)
        return {"outcome": "error", "error_code": "rpc_error"}


def settle_lead(
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
        fingerprint: Hash do texto
        campaign_match: Se corresponde à campanha
        obs: Observação

    Returns:
        Dict com 'outcome' e 'status'
    """
    client = get_supabase_client("service_role")
    if not client:
        return {"outcome": "error", "error_code": "no_client"}

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
        return {"outcome": "error", "error_code": "rpc_error"}


def marcar_lead_direto(
    lead_id: str,
    phone_normalized: str,
    campaign_key: str,
    status: str = "abordado",
    message_timestamp: str | None = None,
) -> dict[str, Any] | None:
    """
    Marca lead como abordado DIRETAMENTE (sem reserva prévia).
    Usado apenas por scripts legados de marcação manual.

    Cria uma reserva e já finaliza como sent numa operação.
    """
    # Primeiro tenta reservar
    reserve = reserve_lead(phone_normalized, campaign_key, lead_id, "sender:manual")
    if not reserve:
        return {"outcome": "error", "error_code": "reserve_failed"}

    outcome = reserve.get("outcome")

    if outcome == "reserved":
        # Reservou agora — finaliza como sent
        return settle_lead(
            reserve["reservation_id"],
            reserve["reservation_token"],
            "sent",
            message_timestamp=message_timestamp or datetime.now(timezone.utc).isoformat(),
            obs="marcacao_manual",
        )

    if outcome in ("already_sent", "already_confirmed"):
        return {"outcome": outcome}

    # reserved_by_other, needs_reconciliation, etc.
    return reserve
