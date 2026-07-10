"""Adaptador PostgreSQL direto para testes locais das RPCs de outreach."""

import json
import os
import psycopg2
import psycopg2.extras


def get_conn():
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        dsn = "host=localhost port=5433 dbname=avgestao_outreach_test user=postgres"
    return psycopg2.connect(dsn)


def call_rpc(func_name, params):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        args = ", ".join(["%s" for _ in params])
        sql = f"SELECT {func_name}({args}) as result"
        cur.execute(sql, list(params.values()))
        row = cur.fetchone()
        conn.commit()
        if row and row["result"]:
            val = row["result"]
            if isinstance(val, str):
                return json.loads(val)
            return val
        return None
    finally:
        conn.close()


def reserve_outreach(phone, campaign_key, lead_id, source="sender:auto"):
    return call_rpc("public.reserve_outreach", {
        "p_phone_normalized": phone,
        "p_campaign_key": campaign_key,
        "p_lead_id": lead_id,
        "p_source": source,
    })


def settle_outreach(reservation_id, reservation_token, new_status,
                    message_timestamp=None, fingerprint=None,
                    campaign_match=None, obs=None):
    return call_rpc("public.settle_outreach", {
        "p_reservation_id": reservation_id,
        "p_reservation_token": reservation_token,
        "p_new_status": new_status,
        "p_message_timestamp": message_timestamp,
        "p_fingerprint": fingerprint,
        "p_campaign_match": campaign_match,
        "p_obs": obs,
    })


def confirm_outreach_from_whatsapp(phone, campaign_key, lead_id,
                                    message_timestamp, fingerprint,
                                    campaign_match, source="whatsapp_reconciliation"):
    return call_rpc("public.confirm_outreach_from_whatsapp", {
        "p_phone_normalized": phone,
        "p_campaign_key": campaign_key,
        "p_lead_id": lead_id,
        "p_message_timestamp": message_timestamp,
        "p_fingerprint": fingerprint,
        "p_campaign_match": campaign_match,
        "p_source": source,
    })


def get_outreach_state(phone, campaign_key):
    return call_rpc("public.get_outreach_state", {
        "p_phone_normalized": phone,
        "p_campaign_key": campaign_key,
    })


def release_reconciliation(phone, campaign_key, reason="manual_review"):
    return call_rpc("public.release_reconciliation", {
        "p_phone_normalized": phone,
        "p_campaign_key": campaign_key,
        "p_reason": reason,
    })
