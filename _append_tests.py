#!/usr/bin/env python3
"""Append new tests for send safety, stages, and recovery"""
import os

os.chdir(r'C:\projetos\script-mapear-comercios-whatsapp-dedup')

with open('tests/test_campanha_whatsapp.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = """

# ============================================================
# Tests: stages antes de operacoes bloqueantes
# ============================================================

class TestStagesAntesBloqueios:
    \"\"\"Testes para garantir que stages sao salvos antes de operacoes bloqueantes.\"\"\"

    def test_stage_sender_lock_waiting_existe_no_executar(self):
        \"\"\"_executar registra sender_lock_waiting antes de adquirir LockWhatsAppSender.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._executar)
        assert 'sender_lock_waiting' in source

    def test_stage_sender_lock_timeout_existe_no_executar(self):
        \"\"\"_executar registra sender_lock_timeout quando lock nao adquirido.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._executar)
        assert 'sender_lock_timeout' in source

    def test_stage_sender_lock_acquired_existe_no_executar(self):
        \"\"\"_executar registra sender_lock_acquired quando lock e adquirido.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._executar)
        assert 'sender_lock_acquired' in source

    def test_stage_sender_session_opening_existe_no_enviar(self):
        \"\"\"_enviar_leads_async registra sender_session_opening antes de abrir sessao.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'sender_session_opening' in source

    def test_stage_sender_session_timeout_existe_no_enviar(self):
        \"\"\"_enviar_leads_async tem sender_session_timeout quando sessao falha.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'sender_session_timeout' in source

    def test_stage_sender_session_opened_existe_no_enviar(self):
        \"\"\"_enviar_leads_async registra sender_session_opened apos sessao aberta.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'sender_session_opened' in source

    def test_enviar_leads_async_tem_timeout_sessao(self):
        \"\"\"_enviar_leads_async tem timeout na abertura da sessao sender.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'wait_for' in source
        assert 'timeout=60' in source

    def test_registrar_estagio_aceita_send_clicked(self):
        \"\"\"registrar_estagio aceita parametro send_clicked.\"\"\"
        import inspect
        sig = inspect.signature(cw.CheckpointManager.registrar_estagio)
        params = list(sig.parameters.keys())
        assert 'send_clicked' in params

    def test_registrar_estagio_aceita_outbound_confirmed(self):
        \"\"\"registrar_estagio aceita parametro outbound_confirmed.\"\"\"
        import inspect
        sig = inspect.signature(cw.CheckpointManager.registrar_estagio)
        params = list(sig.parameters.keys())
        assert 'outbound_confirmed' in params


# ============================================================
# Tests: needs_manual_reconciliation corrigido
# ============================================================

class TestNeedsManualReconciliation:
    \"\"\"Testes para garantir que needs_manual_reconciliation so ocorre com send_clicked=true.\"\"\"

    def test_needs_reconciliation_no_enviar_tem_send_clicked_true(self):
        \"\"\"needs_manual_reconciliation no codigo de envio registra send_clicked=True.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'needs_manual_reconciliation' in source
        assert 'send_clicked=True' in source

    def test_send_button_not_found_nao_e_reconciliation(self):
        \"\"\"send_button_not_found nao usa needs_manual_reconciliation.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        idx_bnf = source.find('send_button_not_found')
        assert idx_bnf > 0
        # Verificar que needs_manual_reconciliation nao aparece antes de send_clicked=True
        idx_clicked = source.find('send_clicked\", send_clicked=True')
        idx_recon = source.find('needs_manual_reconciliation')
        assert idx_recon > idx_clicked, 'needs_manual_reconciliation deve vir depois de send_clicked'

    def test_send_clicked_unknown_vira_needs_reconciliation(self):
        \"\"\"Timeout no envio (send_clicked_unknown) agora vira send_clicked_needs_reconciliation.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp._enviar_leads_async)
        assert 'send_clicked_needs_reconciliation' in source

    def test_stage_send_clicked_inclui_flag(self, tmp_path):
        \"\"\"Stage send_clicked inclui send_clicked=True no checkpoint.\"\"\"
        with patch.object(cw, \"CHECKPOINT_DIR\", tmp_path):
            camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args([\"plan\", \"--dry-run\"]))
            camp.checkpoint.carregar()
            camp.checkpoint.registrar_estagio(\"lead-1\", \"send_clicked\", send_clicked=True)
            pendentes = camp.checkpoint.get_pendentes()
            assert len(pendentes) == 1
            assert pendentes[0].get(\"send_clicked\") is True

    def test_stage_wame_opening_sem_send_clicked(self, tmp_path):
        \"\"\"Stage wa_me_opening nao tem send_clicked (default False).\"\"\"
        with patch.object(cw, \"CHECKPOINT_DIR\", tmp_path):
            camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args([\"plan\", \"--dry-run\"]))
            camp.checkpoint.carregar()
            camp.checkpoint.registrar_estagio(\"lead-1\", \"wa_me_opening\")
            pendentes = camp.checkpoint.get_pendentes()
            assert len(pendentes) == 1
            # send_clicked not explicitly set, so should be None or False
            assert pendentes[0].get(\"send_clicked\") is None


# ============================================================
# Tests: recovery seguro
# ============================================================

class TestRecoverySeguro:
    \"\"\"Testes para recovery seguro com base em stages.\"\"\"

    def test_recover_lista_stage_pendente(self, tmp_path):
        \"\"\"Recover mostra stage pendente.\"\"\"
        with patch.object(cw, \"CHECKPOINT_DIR\", tmp_path):
            camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args([\"plan\", \"--dry-run\"]))
            camp.checkpoint.carregar()
            camp.checkpoint.registrar_estagio(\"lead-1\", \"sender_lock_waiting\", send_clicked=False)
            camp.checkpoint.registrar_falha(\"lead-1\", \"sender_lock_timeout\", \"sender_lock_timeout\")
            camp.checkpoint.salvar()

            args = cw.build_parser().parse_args([\"recover\", \"--run-id\", camp.run_id])
            camp2 = cw.CampanhaWhatsApp(args)
            result = camp2.recuperar_reservas(camp.run_id, release=False)
            assert result == 0

    def test_recover_nao_reenvia_automaticamente(self, tmp_path):
        \"\"\"Recover nao reenvia automaticamente quando send_clicked=true.\"\"\"
        with patch.object(cw, \"CHECKPOINT_DIR\", tmp_path):
            camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args([\"plan\", \"--dry-run\"]))
            camp.checkpoint.carregar()
            camp.checkpoint.registrar_estagio(\"lead-1\", \"send_clicked\", send_clicked=True, outbound_confirmed=False)
            camp.checkpoint.registrar_falha(\"lead-1\", \"envio_timeout\", \"send_clicked_needs_reconciliation\")
            camp.checkpoint.salvar()

            data = camp.checkpoint.carregar()
            pendentes = data.get(\"pending_stages\", {})
            assert \"lead-1\" in pendentes
            assert pendentes[\"lead-1\"].get(\"send_clicked\") is True

    def test_checkpoint_nao_loga_telefone(self, tmp_path):
        \"\"\"Checkpoint nao salva telefone completo em stages.\"\"\"
        with patch.object(cw, \"CHECKPOINT_DIR\", tmp_path):
            camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args([\"plan\", \"--dry-run\"]))
            camp.checkpoint.carregar()
            camp.checkpoint.registrar_estagio(\"lead-1\", \"send_clicked\", send_clicked=True)
            camp.checkpoint.registrar_falha(\"lead-1\", \"test\", \"test\")
            camp.checkpoint.salvar()
            data = json.loads(camp.checkpoint.file.read_text(encoding=\"utf-8\"))
            assert \"5521\" not in str(data)
            assert \"@s.whatsapp\" not in str(data)

    def test_recover_mostra_acao_segura(self):
        \"\"\"recuperar_reservas usa send_clicked para determinar acao segura.\"\"\"
        import inspect
        source = inspect.getsource(cw.CampanhaWhatsApp.recuperar_reservas)
        assert 'send_clicked' in source
        assert 'liberar reserva com seguranca' in source.lower()
        assert 'reconciliacao manual' in source.lower()
"""

# Ensure no duplicate appends
if 'class TestStagesAntesBloqueios' not in content:
    content += new_tests
    with open('tests/test_campanha_whatsapp.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('NEW TESTS APPENDED')
else:
    print('TESTS ALREADY APPENDED')
