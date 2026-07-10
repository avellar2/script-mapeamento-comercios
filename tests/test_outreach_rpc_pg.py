"""
Testes de integração das RPCs de lead_outreach via PostgreSQL direto.

Roda com PostgreSQL local (porta 5433, banco avgestao_outreach_test).

Roda com:
    python -m pytest tests/test_outreach_rpc_pg.py -v -s
"""

import os
import sys
import uuid
import random
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from outreach_pg_adapter import (
    reserve_outreach,
    settle_outreach,
    confirm_outreach_from_whatsapp,
    get_outreach_state,
    release_reconciliation,
    get_conn,
)


# ============================================================
# Helpers
# ============================================================

def _random_digits(n):
    """Gera n dígitos aleatórios."""
    return "".join(str(random.randint(0, 9)) for _ in range(n))


def create_lead(produto="avgestao", grupo="assistencias", phone=None):
    """Cria um lead fictício e retorna (lead_id, phone)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        if phone is None:
            phone = unique_phone()
        # phone is 13 digits (55+DDD+9digits). Extract local part for whatsapp.
        local = phone[2:]  # remove 55 prefix
        cur.execute(
            "INSERT INTO public.leads (nome, telefone, whatsapp, telefone_normalizado, produto, grupo) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (f"Lead {local[:6]}", local, local, phone, produto, grupo)
        )
        lead_id = cur.fetchone()[0]
        conn.commit()
        return str(lead_id), phone
    finally:
        conn.close()


def cleanup_lead(lead_id):
    """Remove lead e outreach associados."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM public.lead_outreach WHERE lead_id = %s", (lead_id,))
        cur.execute("DELETE FROM public.lead_interactions WHERE lead_id = %s", (lead_id,))
        cur.execute("DELETE FROM public.leads WHERE id = %s", (lead_id,))
        conn.commit()
    finally:
        conn.close()


def unique_phone():
    """Gera telefone único válido (55 + DDD válido + 9 dígitos = 13 chars)."""
    ddd = random.choice([11, 21, 31, 41, 51, 61, 71, 81, 85, 91, 92, 95, 98])
    return f"55{ddd}9{_random_digits(8)}"


# ============================================================
# Testes de Reserva
# ============================================================

class TestReserva:
    def test_reserva_aceita(self):
        """Reserva é aceita para lead válido."""
        lead_id, phone = create_lead()
        try:
            result = reserve_outreach(phone, "avgestao:assistencias:primeiro_contato:v1", lead_id, "sender:test")
            assert result is not None
            assert result.get("outcome") == "reserved"
            assert "reservation_id" in result
            assert "reservation_token" in result
            assert "expires_at" in result
        finally:
            cleanup_lead(lead_id)

    def test_reserva_phone_invalido(self):
        """Telefone inválido é recusado."""
        lead_id, _ = create_lead()
        try:
            result = reserve_outreach("123", "avgestao:assistencias:primeiro_contato:v1", lead_id, "sender:test")
            assert result is not None
            assert result.get("outcome") == "invalid_phone"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_campaign_key_invalida(self):
        """Campaign key inválida é recusada."""
        lead_id, phone = create_lead()
        try:
            result = reserve_outreach(phone, "invalida", lead_id, "sender:test")
            assert result is not None
            assert result.get("outcome") == "invalid_campaign_key"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_source_invalido(self):
        """Source inválido é recusado."""
        lead_id, phone = create_lead()
        try:
            result = reserve_outreach(phone, "avgestao:assistencias:primeiro_contato:v1", lead_id, "invalido")
            assert result is not None
            assert result.get("outcome") == "invalid_source"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_duplicada_bloqueada(self):
        """Segunda reserva para mesmo telefone+campanha é bloqueada."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r1 = reserve_outreach(phone, campaign, lead_id, "sender:test")
            assert r1.get("outcome") == "reserved"
            r2 = reserve_outreach(phone, campaign, lead_id, "sender:test")
            assert r2.get("outcome") == "reserved_by_other"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_phone_formatacao_diferente(self):
        """Mesmo telefone com formatação diferente normaliza igual."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r1 = reserve_outreach(phone, campaign, lead_id, "sender:test")
            assert r1.get("outcome") == "reserved"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_campaign_key_diferente(self):
        """Campaign key diferente não interfere."""
        lead_id, phone = create_lead()
        try:
            r1 = reserve_outreach(phone, "avgestao:assistencias:primeiro_contato:v1", lead_id, "sender:test")
            assert r1.get("outcome") == "reserved"
            r2 = reserve_outreach(phone, "avgestao:assistencias:follow_up:v1", lead_id, "sender:test")
            assert r2.get("outcome") == "reserved"
        finally:
            cleanup_lead(lead_id)


# ============================================================
# Testes de Atomicidade (Concorrência)
# ============================================================

class TestAtomicidade:
    def test_duas_reservas_concorrentes(self):
        """Duas reservas concorrentes: apenas uma vence."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        resultados = []
        lock = threading.Lock()

        def reservar():
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            with lock:
                resultados.append(r)

        try:
            t1 = threading.Thread(target=reservar)
            t2 = threading.Thread(target=reservar)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            assert len(resultados) == 2
            outcomes = [r.get("outcome") for r in resultados if r]
            winners = sum(1 for o in outcomes if o == "reserved")
            blocked = sum(1 for o in outcomes if o == "reserved_by_other")
            assert winners == 1, f"Expected 1 winner, got {winners}"
            assert blocked == 1, f"Expected 1 blocked, got {blocked}"
        finally:
            cleanup_lead(lead_id)

    def test_reserva_idempotente(self):
        """Mesma reserva repetida é idempotente."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r1 = reserve_outreach(phone, campaign, lead_id, "sender:test")
            r2 = reserve_outreach(phone, campaign, lead_id, "sender:test")
            assert r1 is not None
            assert r2 is not None
            assert r2.get("outcome") in ("reserved_by_other", "already_sent", "already_confirmed")
        finally:
            cleanup_lead(lead_id)


# ============================================================
# Testes de Settle
# ============================================================

class TestSettle:
    def test_settle_sent(self):
        """Settle com token correto conclui."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            assert r.get("outcome") == "reserved"
            s = settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            assert s.get("outcome") == "settled"
            assert s.get("status") == "sent"
        finally:
            cleanup_lead(lead_id)

    def test_settle_idempotente(self):
        """Retry com mesmo token retorna already_settled."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            s2 = settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            assert s2.get("outcome") == "already_settled"
        finally:
            cleanup_lead(lead_id)

    def test_settle_token_diferente_rejeitado(self):
        """Token diferente é rejeitado."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            s = settle_outreach(r["reservation_id"], str(uuid.uuid4()), "sent")
            assert s.get("outcome") == "invalid_token"
        finally:
            cleanup_lead(lead_id)

    def test_settle_status_invalido(self):
        """Status inválido é recusado."""
        s = settle_outreach(str(uuid.uuid4()), str(uuid.uuid4()), "invalido")
        assert s.get("outcome") == "invalid_status"

    def test_settle_cria_interacao(self):
        """Settle sent cria interação no lead."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            settle_outreach(r["reservation_id"], r["reservation_token"], "sent",
                          obs="teste interacao")
            conn = get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM public.lead_interactions WHERE lead_id = %s", (lead_id,))
                count = cur.fetchone()[0]
                assert count >= 1, f"Expected at least 1 interaction, got {count}"
            finally:
                conn.close()
        finally:
            cleanup_lead(lead_id)

    def test_settle_atualiza_lead(self):
        """Settle sent atualiza status do lead para abordado."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            conn = get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT status FROM public.leads WHERE id = %s", (lead_id,))
                status = cur.fetchone()[0]
                assert status == "abordado"
            finally:
                conn.close()
        finally:
            cleanup_lead(lead_id)

    def test_settle_hash_calculado_pelo_banco(self):
        """Token hash é calculado pelo banco."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            conn = get_conn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT settlement_token_hash FROM public.lead_outreach WHERE id = %s",
                          (r["reservation_id"],))
                row = cur.fetchone()
                assert row[0] is not None, "Hash should be calculated"
                assert len(row[0]) == 64, "SHA-256 hex = 64 chars"
            finally:
                conn.close()
        finally:
            cleanup_lead(lead_id)


# ============================================================
# Testes de Confirm
# ============================================================

class TestConfirm:
    def test_confirm_cria_registro(self):
        """Confirmação cria registro confirmed_from_whatsapp."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = confirm_outreach_from_whatsapp(
                phone, campaign, lead_id,
                datetime.now(timezone.utc).isoformat(),
                "fp_test_confirm",
                True,
                "whatsapp_reconciliation"
            )
            assert r.get("outcome") == "confirmed"
        finally:
            cleanup_lead(lead_id)

    def test_confirm_idempotente(self):
        """Segunda confirmação retorna already_confirmed."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            confirm_outreach_from_whatsapp(
                phone, campaign, lead_id,
                datetime.now(timezone.utc).isoformat(),
                "fp_test_confirm",
                True,
                "whatsapp_reconciliation"
            )
            r2 = confirm_outreach_from_whatsapp(
                phone, campaign, lead_id,
                datetime.now(timezone.utc).isoformat(),
                "fp_test_confirm",
                True,
                "whatsapp_reconciliation"
            )
            assert r2.get("outcome") == "already_confirmed"
        finally:
            cleanup_lead(lead_id)

    def test_confirm_campaign_match_false(self):
        """campaign_match=False retorna ambiguous."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = confirm_outreach_from_whatsapp(
                phone, campaign, lead_id,
                datetime.now(timezone.utc).isoformat(),
                "fp_test",
                False,
                "whatsapp_reconciliation"
            )
            assert r.get("outcome") == "ambiguous_not_confirmed"
        finally:
            cleanup_lead(lead_id)

    def test_confirm_phone_invalido(self):
        """Telefone inválido é recusado."""
        r = confirm_outreach_from_whatsapp(
            "123", "avgestao:assistencias:primeiro_contato:v1",
            str(uuid.uuid4()),
            datetime.now(timezone.utc).isoformat(),
            "fp_test", True, "whatsapp_reconciliation"
        )
        assert r.get("outcome") == "invalid_phone"

    def test_confirm_promote_needs_reconciliation(self):
        """Promove needs_reconciliation para confirmed."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            conn = get_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO public.lead_outreach (lead_id, phone_normalized, campaign_key, status, source, message_direction) "
                    "VALUES (%s, %s, %s, 'needs_reconciliation', 'test', 'outbound')",
                    (lead_id, phone, campaign)
                )
                conn.commit()
            finally:
                conn.close()

            r = confirm_outreach_from_whatsapp(
                phone, campaign, lead_id,
                datetime.now(timezone.utc).isoformat(),
                "fp_test",
                True,
                "whatsapp_reconciliation"
            )
            assert r.get("outcome") == "confirmed"
        finally:
            cleanup_lead(lead_id)


# ============================================================
# Testes de Release
# ============================================================

class TestRelease:
    def test_release_needs_reconciliation(self):
        """Libera needs_reconciliation."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            conn = get_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO public.lead_outreach (lead_id, phone_normalized, campaign_key, status, source, message_direction) "
                    "VALUES (%s, %s, %s, 'needs_reconciliation', 'test', 'outbound')",
                    (lead_id, phone, campaign)
                )
                conn.commit()
            finally:
                conn.close()

            r = release_reconciliation(phone, campaign, "manual_review")
            assert r.get("outcome") == "released"
        finally:
            cleanup_lead(lead_id)

    def test_release_sent_nao_pode(self):
        """Sent não pode ser liberado."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            rel = release_reconciliation(phone, campaign)
            assert rel.get("outcome") == "invalid_transition"
        finally:
            cleanup_lead(lead_id)

    def test_release_sem_registro(self):
        """Sem registro retorna not_found."""
        r = release_reconciliation(unique_phone(), "avgestao:assistencias:primeiro_contato:v1")
        assert r.get("outcome") == "not_found"

    def test_release_phone_invalido(self):
        """Telefone inválido é recusado."""
        r = release_reconciliation("123", "avgestao:assistencias:primeiro_contato:v1")
        assert r.get("outcome") == "invalid_phone"


# ============================================================
# Testes de get_outreach_state (Leitura Anônima)
# ============================================================

class TestGetState:
    def test_get_state_sem_registro(self):
        """Consulta sem registro retorna none."""
        r = get_outreach_state(unique_phone(), "avgestao:assistencias:primeiro_contato:v1")
        assert r.get("outcome") == "none"

    def test_get_state_com_registro(self):
        """Consulta com registro retorna status."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            reserve_outreach(phone, campaign, lead_id, "sender:test")
            r = get_outreach_state(phone, campaign)
            assert r.get("outcome") == "found"
            assert r.get("status") == "reserved"
        finally:
            cleanup_lead(lead_id)

    def test_get_state_nao_retorna_token(self):
        """get_outreach_state não retorna token."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            reserve_outreach(phone, campaign, lead_id, "sender:test")
            r = get_outreach_state(phone, campaign)
            assert "reservation_token" not in r
            assert "settlement_token_hash" not in r
        finally:
            cleanup_lead(lead_id)

    def test_get_state_args_invalidos(self):
        """Args nulos retornam invalid_args."""
        r = get_outreach_state(None, None)
        assert r.get("outcome") == "invalid_args"


# ============================================================
# Testes de Máquina de Estados
# ============================================================

class TestMaquinaEstados:
    def test_transicoes_invalidas(self):
        """Transições inválidas são rejeitadas."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            # confirmed_from_whatsapp não é status válido para settle
            s = settle_outreach(r["reservation_id"], r["reservation_token"],
                              "confirmed_from_whatsapp")
            assert s.get("outcome") in ("invalid_status", "invalid_transition")
        finally:
            cleanup_lead(lead_id)

    def test_reserved_para_sent(self):
        """reserved -> sent é válida."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            s = settle_outreach(r["reservation_id"], r["reservation_token"], "sent")
            assert s.get("outcome") == "settled"
        finally:
            cleanup_lead(lead_id)

    def test_reserved_para_failed(self):
        """reserved -> failed é válida."""
        lead_id, phone = create_lead()
        campaign = "avgestao:assistencias:primeiro_contato:v1"
        try:
            r = reserve_outreach(phone, campaign, lead_id, "sender:test")
            s = settle_outreach(r["reservation_id"], r["reservation_token"], "failed")
            assert s.get("outcome") == "settled"
        finally:
            cleanup_lead(lead_id)


# ============================================================
# Testes de RLS e Permissões
# ============================================================

class TestRLS:
    def test_rls_ativado(self):
        """RLS está ativado em lead_outreach."""
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'lead_outreach'")
            row = cur.fetchone()
            assert row[0] is True, "RLS should be enabled"
            assert row[1] is True, "Force RLS should be enabled"
        finally:
            conn.close()

    def test_grants_corretos(self):
        """Grants estão configurados corretamente."""
        conn = get_conn()
        try:
            cur = conn.cursor()
            # reserve_outreach: service_role tem EXECUTE
            cur.execute("""
                SELECT grantee, privilege_type
                FROM information_schema.routine_privileges
                WHERE routine_name = 'reserve_outreach'
                AND grantee = 'service_role'
            """)
            rows = cur.fetchall()
            assert any(r[1] == 'EXECUTE' for r in rows), "service_role should have EXECUTE on reserve_outreach"

            # get_outreach_state: anon tem EXECUTE
            cur.execute("""
                SELECT grantee, privilege_type
                FROM information_schema.routine_privileges
                WHERE routine_name = 'get_outreach_state'
                AND grantee = 'anon'
            """)
            rows = cur.fetchall()
            assert any(r[1] == 'EXECUTE' for r in rows), "anon should have EXECUTE on get_outreach_state"
        finally:
            conn.close()
