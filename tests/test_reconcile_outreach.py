#!/usr/bin/env python3
"""Testes do comando reconcile-outreach (Objetivo 2).

Garantem que o comando e READ-ONLY em relacao ao banco (nao muta lead_outreach /
leads / lead_interactions), grava auditoria LOCAL (JSON) preservando evidencia e
imprime SQL manual para reverter (pois 'sent' e terminal na maquina de estados).

Cobre o caso Fabio Cell / run_20260707_hermes008 sem reenviar.
"""
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import campanha_whatsapp as cw

RUN_ID = "run_20260707_hermes008"
PHONE = "5521964212796"
LEAD_ID = "lead-fabio"


def _build_campaign(tmp_path):
    """Cria campaign com checkpoint em tmp_path e um lead marcado como sent."""
    with patch.object(cw, "CHECKPOINT_DIR", tmp_path):
        camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args(["plan"]))
        camp.run_id = RUN_ID
        camp.checkpoint = cw.CheckpointManager(RUN_ID)
        camp.checkpoint.carregar()
        camp.checkpoint.registrar_envio(LEAD_ID, "deadbeef")
        camp.checkpoint.salvar()
    return camp


def _fake_client(status="sent"):
    """Cliente Supabase mockado: lead_outreach(sent) + leads(abordado) + interactions([])."""
    client = MagicMock()
    lo_result = MagicMock()
    lo_result.data = [{
        "id": "lo-1", "lead_id": LEAD_ID, "phone_normalized": PHONE,
        "campaign_key": cw.PRIMEIRO_CONTATO_V1, "status": status,
        "message_timestamp": "2026-07-07T15:00:00Z", "message_fingerprint": "deadbeef",
    }]
    leads_result = MagicMock()
    leads_result.data = [{"id": LEAD_ID, "nome": "Fabio Cell",
                          "telefone_normalizado": PHONE, "status": "abordado"}]
    inter_result = MagicMock()
    inter_result.data = []

    def table(name):
        t = MagicMock()
        if name == "lead_outreach":
            t.select.return_value.eq.return_value.eq.return_value.order.return_value \
                .limit.return_value.execute.return_value = lo_result
        elif name == "leads":
            t.select.return_value.eq.return_value.limit.return_value.execute.return_value = leads_result
        elif name == "lead_interactions":
            t.select.return_value.eq.return_value.order.return_value.limit.return_value \
                .execute.return_value = inter_result
        return t

    client.table.side_effect = table
    return client


def _reconcile(camp, tmp_path, client, **kwargs):
    """Roda reconcile_outreach com CHECKPOINT_DIR + _root patchados em tmp_path."""
    with ExitStack() as st:
        st.enter_context(patch.object(cw, "CHECKPOINT_DIR", tmp_path))
        st.enter_context(patch.object(cw, "_root", str(tmp_path)))
        st.enter_context(patch("sender_int.get_supabase_client", return_value=client))
        return camp.reconcile_outreach(**kwargs)


class TestReconcileOutreachReadOnly:
    def test_nao_escreve_no_banco(self, tmp_path, capsys):
        """NENHUMA mutacao em lead_outreach/leads/lead_interactions (read-only)."""
        camp = _build_campaign(tmp_path)
        rc = _reconcile(camp, tmp_path, _fake_client("sent"),
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE)
        assert rc == 0
        out = capsys.readouterr().out
        assert "RECONCILIACAO DE ENVIO" in out
        assert "sent" in out
        assert "SQL MANUAL PARA REVERTER" in out
        assert "BEGIN;" in out
        assert "UPDATE public.lead_outreach SET status='failed'" in out
        assert "UPDATE public.leads SET status='pronto_para_enviar'" in out
        assert "COMMIT;" in out
        assert "READ-ONLY" in out or "read-only" in out

    def test_grava_auditoria_local_json(self, tmp_path, capsys):
        """Auditoria local (JSON) preserva evidencia sem mutar DB."""
        camp = _build_campaign(tmp_path)
        rc = _reconcile(camp, tmp_path, _fake_client("sent"),
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1)
        assert rc == 0
        audit_dir = tmp_path / "output" / "avgestao" / "reconcile"
        files = list(audit_dir.glob(f"{RUN_ID}_*.json"))
        assert len(files) == 1
        audit = json.loads(files[0].read_text(encoding="utf-8"))
        assert audit["run_id"] == RUN_ID
        assert audit["outcome"] == "failed_after_click"
        assert audit["reason"] == "whatsapp_message_not_sent_modal"
        assert audit["findings"]
        assert audit["findings"][0]["lead_outreach"]["status"] == "sent"
        assert "read-only" in audit["note"].lower()

    def test_sem_cliente_supabase_ainda_gera_sql_template(self, tmp_path, capsys):
        """Sem cliente Supabase, ainda grava auditoria e imprime SQL template."""
        camp = _build_campaign(tmp_path)
        rc = _reconcile(camp, tmp_path, None,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cliente Supabase indisponivel" in out
        assert "<LEAD_OUTREACH_ID>" in out  # template generico
        assert "BEGIN;" in out

    def test_sem_run_id_retorna_2(self):
        rc = cw.main(["reconcile-outreach", "--campaign-key", cw.PRIMEIRO_CONTATO_V1])
        assert rc == 2

    def test_mascara_telefone_no_relatorio(self, tmp_path, capsys):
        """Telefone e mascarado no relatorio impresso (privacidade)."""
        camp = _build_campaign(tmp_path)
        _reconcile(camp, tmp_path, _fake_client("sent"),
                   run_id=RUN_ID, outcome="failed_after_click",
                   reason="whatsapp_message_not_sent_modal",
                   campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE)
        out = capsys.readouterr().out
        assert PHONE not in out  # nao vazou telefone completo
        assert "5521****2796" in out  # mascarado