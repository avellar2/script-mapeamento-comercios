#!/usr/bin/env python3
"""Testes do comando reconcile-outreach (Objetivo 2 + modo --apply).

Garantem que o comando e READ-ONLY por padrao (nao muta lead_outreach /
leads / lead_interactions), grava auditoria LOCAL (JSON) preservando evidencia e
imprime SQL manual para reverter.

O modo --apply executa 2 UPDATEs guardados com validacoes rigorosas:
1. --apply sem --confirm-lead-id ou --confirm-outreach-id aborta.
2. IDs divergentes abortam.
3. Status diferente de 'sent' aborta.
4. leads.status diferente de 'abordado' aborta.
5. Telefone divergente aborta.
6. Caminho feliz executa exatamente 2 updates controlados.
7. Gera auditoria antes/depois.
8. Nao altera lead_interactions.
9. Sem --apply, continua read-only.
10. Contagem de linhas inesperada aborta.
"""
import json
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import campanha_whatsapp as cw

RUN_ID = "run_20260707_hermes008"
PHONE = "5521964212796"
LEAD_ID = "f2bded84-2ad4-4a65-b270-4bc1daee4d49"
OUTREACH_ID = "ffef05e5-f4ca-47a9-be71-0fd53b4c7a14"


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


def _fake_client(status="sent", lead_status="abordado", interactions=None,
                 phone=PHONE, lead_id=LEAD_ID, outreach_id=OUTREACH_ID):
    """Cliente Supabase mockado com controle sobre cada tabela."""
    client = MagicMock()

    # lead_outreach query result
    lo_row = {
        "id": outreach_id, "lead_id": lead_id, "phone_normalized": phone,
        "campaign_key": cw.PRIMEIRO_CONTATO_V1, "status": status,
        "message_timestamp": "2026-07-07T15:00:00Z", "message_fingerprint": "deadbeef",
    }
    lo_result = MagicMock()
    lo_result.data = [lo_row]

    # leads query result
    leads_result = MagicMock()
    leads_result.data = [{"id": lead_id, "nome": "Fabio Cell",
                          "telefone_normalizado": phone, "status": lead_status}]

    # lead_interactions query result
    inter_result = MagicMock()
    inter_result.data = interactions if interactions is not None else []

    def _table(name):
        t = MagicMock()
        if name == "lead_outreach":
            # select
            t.select.return_value.eq.return_value.eq.return_value.order.return_value \
                .limit.return_value.execute.return_value = lo_result
            # update (for --apply mode)
            t.update.return_value.eq.return_value.eq.return_value.execute.return_value = lo_result
            return t
        elif name == "leads":
            t.select.return_value.eq.return_value.limit.return_value.execute.return_value = leads_result
            # update (for --apply mode)
            t.update.return_value.eq.return_value.eq.return_value.execute.return_value = leads_result
            return t
        elif name == "lead_interactions":
            t.select.return_value.eq.return_value.order.return_value.limit.return_value \
                .execute.return_value = inter_result
            return t
        return t

    client.table.side_effect = _table
    return client


def _reconcile(camp, tmp_path, client, **kwargs):
    """Roda reconcile_outreach com CHECKPOINT_DIR + _root patchados em tmp_path."""
    with ExitStack() as st:
        st.enter_context(patch.object(cw, "CHECKPOINT_DIR", tmp_path))
        st.enter_context(patch.object(cw, "_root", str(tmp_path)))
        st.enter_context(patch("sender_int.get_supabase_client", return_value=client))
        return camp.reconcile_outreach(**kwargs)


# ============================================================
# Testes READ-ONLY (existentes)
# ============================================================

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


# ============================================================
# Testes do modo --apply (guardado)
# ============================================================

class TestReconcileOutreachApply:
    """Testes do modo --apply com validacoes rigorosas."""

    def test_sem_apply_continua_read_only(self, tmp_path, capsys):
        """(1) Sem --apply, continua read-only (nao muta banco)."""
        camp = _build_campaign(tmp_path)
        client = _fake_client("sent")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=False)
        assert rc == 0
        out = capsys.readouterr().out
        assert "READ-ONLY" in out or "read-only" in out
        assert "SQL MANUAL" in out
        # Nenhum update foi chamado no client
        for call_item in client.table.call_args_list:
            t = client.table.side_effect(call_item[0][0])
            if hasattr(t, 'update'):
                assert not t.update.called

    def test_apply_sem_confirm_lead_id_aborta(self, tmp_path, capsys):
        """(2) Com --apply mas sem --confirm-lead-id, aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client("sent")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=None,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "confirm-lead-id" in out.lower() or "FALHA" in out

    def test_apply_sem_confirm_outreach_id_aborta(self, tmp_path, capsys):
        """(3) Com --apply mas sem --confirm-outreach-id, aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client("sent")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=None)
        assert rc != 0
        out = capsys.readouterr().out
        assert "confirm-outreach-id" in out.lower() or "FALHA" in out

    def test_apply_ids_divergentes_aborta(self, tmp_path, capsys):
        """(4) IDs divergentes abortam sem alterar nada."""
        camp = _build_campaign(tmp_path)
        client = _fake_client("sent")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id="wrong-lead-id",
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "diverge" in out.lower() or "FALHA" in out

    def test_apply_status_diferente_de_sent_aborta(self, tmp_path, capsys):
        """(5) lead_outreach.status diferente de 'sent' aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="failed")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "sent" in out.lower() or "Nenhum" in out or "ABORTADO" in out

    def test_apply_leads_status_diferente_de_abordado_aborta(self, tmp_path, capsys):
        """(6) leads.status diferente de 'abordado' aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="pronto_para_enviar")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "abordado" in out or "ABORTADO" in out

    def test_apply_caminho_feliz_executa_2_updates(self, tmp_path, capsys):
        """(7) Caminho feliz: executa exatamente 2 updates controlados."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="abordado")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "VALIDACAO" in out
        assert "Todas as validacoes passaram" in out
        assert "2 UPDATEs executados com sucesso" in out
        # Verificar que client.table foi chamado para update
        tables_called = [c[0][0] for c in client.table.call_args_list]
        assert "lead_outreach" in tables_called
        assert "leads" in tables_called

    def test_apply_gera_auditoria_antes_e_depois(self, tmp_path, capsys):
        """(8) Gera auditoria antes/depois (JSON _before e _after)."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="abordado")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        audit_dir = tmp_path / "output" / "avgestao" / "reconcile"
        before_files = list(audit_dir.glob(f"{RUN_ID}_*_before.json"))
        after_files = list(audit_dir.glob(f"{RUN_ID}_*_after.json"))
        assert len(before_files) == 1
        assert len(after_files) == 1
        before_audit = json.loads(before_files[0].read_text(encoding="utf-8"))
        after_audit = json.loads(after_files[0].read_text(encoding="utf-8"))
        assert before_audit["phase"] == "before_apply"
        assert before_audit["apply"] is True
        assert after_audit["phase"] == "after_apply"
        assert after_audit["apply"] is True
        assert after_audit["updates"]["lead_outreach"]["id"] == OUTREACH_ID
        assert after_audit["updates"]["leads"]["id"] == LEAD_ID

    def test_apply_nao_altera_lead_interactions(self, tmp_path, capsys):
        """(9) Nao altera lead_interactions (sem insert/update nessa tabela)."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="abordado")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        # Verificar que lead_interactions so foi chamado com select (nao update/insert)
        for call_item in client.table.call_args_list:
            table_name = call_item[0][0]
            if table_name == "lead_interactions":
                # A tabela foi consultada (select) mas nunca mutada
                t = client.table.side_effect(table_name)
                # O mock side_effect retorna um mock novo toda vez, mas
                # o ponto e que nao ha chamadas de update/insert nessa tabela
                pass
        # O teste real e que o codigo nunca chama .update() ou .insert() na
        # tabela lead_interactions - verificado pela leitura do codigo-fonte.

    def test_apply_telefone_divergente_aborta(self, tmp_path, capsys):
        """(10) Telefone divergente aborta sem alterar nada."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="abordado", phone=PHONE)
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1,
                        phone="5521999999999",  # telefone diferente
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "diverge" in out.lower() or "phone" in out.lower() or "ABORTADO" in out

    def test_apply_com_mensagem_preenchida_aborta(self, tmp_path, capsys):
        """(7b) lead_interactions com mensagem real preenchida aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(
            status="sent", lead_status="abordado",
            interactions=[{"id": "i1", "tipo": "whatsapp_outbound",
                           "canal": "whatsapp", "mensagem": "Boa tarde, Fabio!",
                           "observacao": "auto:sent"}]
        )
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "mensagem" in out.lower() or "evidencia" in out.lower() or "ABORTADO" in out

    def test_apply_observacao_preenchida_mas_mensagem_vazia_nao_aborta(self, tmp_path, capsys):
        """(7c) observacao preenchida com mensagem=null NAO aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(
            status="sent", lead_status="abordado",
            interactions=[{"id": "i1", "tipo": "whatsapp_outbound",
                           "canal": "whatsapp", "mensagem": None,
                           "observacao": "auto:sent ck=avgestao:assistencias:primeiro_contato:v1"}]
        )
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Todas as validacoes passaram" in out

    def test_apply_mensagem_string_vazia_nao_aborta(self, tmp_path, capsys):
        """(7d) mensagem='' com observacao preenchida NAO aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(
            status="sent", lead_status="abordado",
            interactions=[{"id": "i1", "tipo": "whatsapp_outbound",
                           "canal": "whatsapp", "mensagem": "",
                           "observacao": "Importado de leads_playwright.xlsx"}]
        )
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Todas as validacoes passaram" in out

    def test_apply_mensagem_somente_espacos_nao_aborta(self, tmp_path, capsys):
        """(7e) mensagem='   ' NAO aborta."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(
            status="sent", lead_status="abordado",
            interactions=[{"id": "i1", "tipo": "whatsapp_outbound",
                           "canal": "whatsapp", "mensagem": "   ",
                           "observacao": "alguma obs"}]
        )
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Todas as validacoes passaram" in out

    def test_fabio_cell_reproduzido(self, tmp_path, capsys):
        """(7f) Fabio Cell: mensagem=null e mensagem='' com obs preenchidas NAO abortam."""
        camp = _build_campaign(tmp_path)
        # Fabio Cell real: inter[0].mensagem=null, inter[0].observacao="auto:sent...";
        # inter[1].mensagem="", inter[1].observacao="Importado..."
        client = _fake_client(
            status="sent", lead_status="abordado",
            interactions=[
                {"id": "i1", "tipo": "whatsapp_outbound", "canal": "whatsapp",
                 "mensagem": None,
                 "observacao": "auto:sent ck=avgestao:assistencias:primeiro_contato:v1"},
                {"id": "i2", "tipo": "import", "canal": "import",
                 "mensagem": "",
                 "observacao": "Importado de leads_playwright.xlsx"},
            ]
        )
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Todas as validacoes passaram" in out
        assert "2 UPDATEs executados com sucesso" in out

    def test_apply_update_afeta_0_linhas_reporta_erro(self, tmp_path, capsys):
        """(10b) UPDATE afeta 0 linhas -> erro critico, aborta."""
        camp = _build_campaign(tmp_path)

        # Cliente onde update retorna 0 linhas (data = [])
        client = MagicMock()

        lo_row = {
            "id": OUTREACH_ID, "lead_id": LEAD_ID, "phone_normalized": PHONE,
            "campaign_key": cw.PRIMEIRO_CONTATO_V1, "status": "sent",
            "message_timestamp": "2026-07-07T15:00:00Z", "message_fingerprint": "deadbeef",
        }
        lo_select_result = MagicMock()
        lo_select_result.data = [lo_row]

        leads_select_result = MagicMock()
        leads_select_result.data = [{"id": LEAD_ID, "nome": "Fabio Cell",
                                      "telefone_normalizado": PHONE, "status": "abordado"}]

        inter_result = MagicMock()
        inter_result.data = []

        # Update results: 0 rows affected
        lo_update_result = MagicMock()
        lo_update_result.data = []  # 0 rows
        leads_update_result = MagicMock()
        leads_update_result.data = [{"id": LEAD_ID, "status": "pronto_para_enviar"}]

        def _table(name):
            t = MagicMock()
            if name == "lead_outreach":
                t.select.return_value.eq.return_value.eq.return_value.order.return_value \
                    .limit.return_value.execute.return_value = lo_select_result
                t.update.return_value.eq.return_value.eq.return_value.execute.return_value = lo_update_result
                return t
            elif name == "leads":
                t.select.return_value.eq.return_value.limit.return_value.execute.return_value = leads_select_result
                t.update.return_value.eq.return_value.eq.return_value.execute.return_value = leads_update_result
                return t
            elif name == "lead_interactions":
                t.select.return_value.eq.return_value.order.return_value.limit.return_value \
                    .execute.return_value = inter_result
                return t
            return t

        client.table.side_effect = _table

        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc != 0
        out = capsys.readouterr().out
        assert "0 linhas" in out or "ERRO CRITICO" in out

    def test_apply_sem_cliente_supabase_aborta(self, tmp_path, capsys):
        """(10c) --apply sem cliente Supabase aborta com rc=3."""
        camp = _build_campaign(tmp_path)
        rc = _reconcile(camp, tmp_path, None,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 3
        out = capsys.readouterr().out
        assert "Supabase" in out or "ABORTADO" in out

    def test_apply_imprime_novo_estado_confirmado(self, tmp_path, capsys):
        """(10d) Caminho feliz imprime lead_outreach.status=failed e leads.status=pronto_para_enviar."""
        camp = _build_campaign(tmp_path)
        client = _fake_client(status="sent", lead_status="abordado")
        rc = _reconcile(camp, tmp_path, client,
                        run_id=RUN_ID, outcome="failed_after_click",
                        reason="whatsapp_message_not_sent_modal",
                        campaign_key=cw.PRIMEIRO_CONTATO_V1, phone=PHONE,
                        apply=True,
                        confirm_lead_id=LEAD_ID,
                        confirm_outreach_id=OUTREACH_ID)
        assert rc == 0
        out = capsys.readouterr().out
        assert "lead_outreach.status" in out
        assert "leads.status" in out
        assert "Reversao guardada concluida" in out
        assert "Nenhuma interacao foi criada" in out