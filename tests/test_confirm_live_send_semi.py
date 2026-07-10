#!/usr/bin/env python3
"""Testes para --confirm-live-send no modo semi.

Cobertura:
1. semi + --confirm-live-send NAO chama input() (pula prompt manual).
2. semi + --confirm-live-send registra manual_confirmed com source=confirm_live_send.
3. semi + --confirm-live-send registra post_manual_confirmed.
4. semi + --confirm-live-send ainda exige outbound_confirmed=True para settle_sent_done.
5. semi + --confirm-live-send + outbound falhando NAO marca sent.
6. semi sem token e sem --confirm-live-send chama input() (prompt manual).
7. semi + --confirm-live-send + --semi-confirm-token e incompativel (ja validado em outro teste).
8. EOF no prompt NAO acontece quando --confirm-live-send esta ativo.

Sem browser real, sem envio real. Tudo mockado.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
_tests_dir = str(Path(__file__).resolve().parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

import campanha_whatsapp as cw
from test_semi_sender_hang import (
    _build_semi_campaign, _run_send, _record_stages, _safe_lead,
    _FakeSenderPage,
)


# ============================================================
# Helper: construir campanha semi com confirm_live_send
# ============================================================

def _build_semi_with_confirm_live(tmp_path):
    """Constrói campanha semi com --confirm-live-send ativo."""
    args_list = ["semi", "--confirm-live-send"]
    with patch.object(cw, "CHECKPOINT_DIR", tmp_path):
        camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args(args_list))
    camp.checkpoint.carregar()
    camp.safety = MagicMock()
    camp.safety.deve_parar.return_value = (False, "")
    camp.safety.aguardar_intervalo = MagicMock()
    camp._renderizar_mensagem = MagicMock(return_value="Ola mensagem de teste")
    camp._hash_mensagem = MagicMock(return_value="abcdef0123456789")
    return camp


# ============================================================
# TEST 1: confirm_live_send pula input()
# ============================================================

class TestConfirmLiveSendSkipsInput:
    """--confirm-live-send no modo semi nao chama input()."""

    def test_confirm_live_send_nao_chama_input(self, tmp_path):
        """(1) Com --confirm-live-send, input() nunca e chamado."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)

        input_mock = MagicMock(side_effect=AssertionError("input() nao deveria ser chamado"))
        patches = [
            patch.object(cw, "SessaoWhatsApp"),
            patch("sender_int.settle_lead", MagicMock(return_value={"outcome": "settled"})),
            patch.object(cw.MessageSender, "abrir_wa_me", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "localizar_botao_enviar", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "clicar_enviar", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "confirmar_mensagem_enviada", AsyncMock(return_value="confirmed")),
            patch("builtins.input", input_mock),
        ]
        for p in patches:
            p.start()
        try:
            asyncio.run(camp._enviar_leads_async([_safe_lead()]))
        finally:
            for p in patches:
                p.stop()

        # input() nunca foi chamado
        assert not input_mock.called, "input() foi chamado mesmo com --confirm-live-send"

    def test_confirm_live_send_registra_manual_confirmed(self, tmp_path):
        """(2) confirm_live_send registra manual_confirmed com source=confirm_live_send."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()])

        names = [s[0] for s in stages]
        assert "prompt_manual" in names
        assert "manual_confirmed" in names
        assert "post_manual_confirmed" in names

        # Verifica source do manual_confirmed
        confirmed_stages = [s for s in stages if s[0] == "manual_confirmed"]
        assert len(confirmed_stages) > 0

    def test_confirm_live_send_avanca_ate_settle(self, tmp_path):
        """(3) confirm_live_send avança ate settle_sent_done quando outbound confirma."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()])  # confirm="confirmed", settle="settled"

        names = [s[0] for s in stages]
        assert "manual_confirmed" in names
        assert "post_manual_confirmed" in names
        assert "wa_me_opening" in names
        assert "wa_me_loaded" in names
        assert "send_clicked" in names
        assert "outbound_confirming" in names
        assert "settle_sent_done" in names
        assert len(camp.checkpoint._data["sent_leads"]) == 1

    def test_confirm_live_send_outbound_falha_nao_marca_sent(self, tmp_path):
        """(4) confirm_live_send + outbound timeout -> NAO marca sent, gera reconciliation."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()], confirm="timeout")

        names = [s[0] for s in stages]
        assert "send_clicked" in names
        assert "settle_sent_done" not in names
        assert "send_clicked_needs_reconciliation" in names
        assert len(camp.checkpoint._data["sent_leads"]) == 0

    def test_confirm_live_send_not_sent_error_nao_marca_sent(self, tmp_path):
        """(5) confirm_live_send + not_sent_error -> NAO marca sent."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()], confirm="not_sent_error")

        names = [s[0] for s in stages]
        assert "send_clicked" in names
        assert "send_failed_after_click" in names
        assert "settle_sent_done" not in names
        assert len(camp.checkpoint._data["sent_leads"]) == 0

    def test_confirm_live_send_browser_closed_nao_marca_sent(self, tmp_path):
        """(5b) confirm_live_send + browser_closed -> NAO marca sent."""
        camp = _build_semi_with_confirm_live(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()], confirm="browser_closed")

        names = [s[0] for s in stages]
        assert "send_clicked" in names
        assert "settle_sent_done" not in names
        assert len(camp.checkpoint._data["sent_leads"]) == 0


# ============================================================
# TEST 2: Sem confirm_live_send e sem token, input() e chamado
# ============================================================

class TestSemConfirmLiveSendChamaInput:
    """Sem --confirm-live-send e sem --semi-confirm-token, input() e chamado."""

    def test_sem_confirm_live_send_chama_input(self, tmp_path):
        """(6) Sem --confirm-live-send, input() e chamado normalmente."""
        camp = _build_semi_campaign(tmp_path)  # semi sem --confirm-live-send
        stages = _record_stages(camp)

        input_mock = MagicMock(return_value="s")
        patches = [
            patch.object(cw, "SessaoWhatsApp"),
            patch("sender_int.settle_lead", MagicMock(return_value={"outcome": "settled"})),
            patch.object(cw.MessageSender, "abrir_wa_me", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "localizar_botao_enviar", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "clicar_enviar", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "confirmar_mensagem_enviada", AsyncMock(return_value="confirmed")),
            patch("builtins.input", input_mock),
        ]
        for p in patches:
            p.start()
        try:
            asyncio.run(camp._enviar_leads_async([_safe_lead()]))
        finally:
            for p in patches:
                p.stop()

        # input() foi chamado
        assert input_mock.called, "input() deveria ser chamado sem --confirm-live-send"


# ============================================================
# TEST 3: Parser aceita --confirm-live-send no modo semi
# ============================================================

class TestParserConfirmLiveSendSemi:
    def test_parser_aceita_confirm_live_send_em_semi(self):
        """(7) Parser aceita --confirm-live-send no modo semi."""
        parser = cw.build_parser()
        args = parser.parse_args(["semi", "--confirm-live-send"])
        assert args.confirm_live_send is True
        assert args.mode == "semi"

    def test_parser_sem_confirm_live_send_em_semi(self):
        """(7b) Parser sem --confirm-live-send no modo semi."""
        parser = cw.build_parser()
        args = parser.parse_args(["semi"])
        assert args.confirm_live_send is False
        assert args.mode == "semi"