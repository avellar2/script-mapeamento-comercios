#!/usr/bin/env python3
"""Testes do helper MessageSender.confirmar_mensagem_enviada.

Garante que o sistema NAO marca 'sent' apenas porque clicou em Enviar. Depois do
clique, confirma no DOM do WhatsApp Web:
  - message-out com trecho da mensagem  -> confirmed
  - modal "Sua mensagem nao foi enviada" / "Tentar novamente" -> not_sent_error
  - browser/contexto fechado            -> browser_closed
  - nenhum sinal no tempo limite         -> timeout
  - falhas repetidas ao ler o DOM        -> ambiguous

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
# Reutiliza helpers do test_semi_sender_hang (fake page async + _run_send).
_tests_dir = str(Path(__file__).resolve().parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

import campanha_whatsapp as cw
from test_semi_sender_hang import _build_semi_campaign, _run_send, _record_stages, _safe_lead


MENSAGEM = (
    "Boa tarde, pessoal da RM INFORMATICA! Tudo bem?\n\n"
    "Aqui e o Vanderson, criador do AVGESTAO, um sistema feito para organizar assistencias.\n\n"
    "Posso liberar e configurar o acesso de voces?"
)


class _FakeConfirmPage:
    """Page mockada: is_closed() sync + evaluate(js, arg) async."""

    def __init__(self, results=None, is_closed=False, evaluate_exc=None):
        self._results = results or []
        self._idx = 0
        self._closed = is_closed
        self._evaluate_exc = evaluate_exc

    def is_closed(self):
        return self._closed

    async def evaluate(self, js, arg=None):
        if self._evaluate_exc is not None:
            raise self._evaluate_exc
        if self._idx < len(self._results):
            r = self._results[self._idx]
            self._idx += 1
            return r
        return self._results[-1] if self._results else {"outbound": False, "error": False}


def _run_confirm(page, mensagem=MENSAGEM, timeout=2):
    return asyncio.run(cw.MessageSender.confirmar_mensagem_enviada(
        page, mensagem, timeout_segundos=timeout, _poll_interval=0, _settle_delay=0))


class TestConfirmarMensagemEnviada:
    def test_confirma_quando_message_out_com_trecho(self):
        """(1) message-out com texto esperado -> confirmed (permite settle sent)."""
        page = _FakeConfirmPage(results=[{"outbound": True, "error": False}])
        assert _run_confirm(page) == "confirmed"

    def test_nao_confirma_quando_modal_nao_enviada(self):
        """(2) modal 'Sua mensagem nao foi enviada' -> not_sent_error, nao sent."""
        page = _FakeConfirmPage(results=[{"outbound": False, "error": True}])
        assert _run_confirm(page) == "not_sent_error"

    def test_detecta_tentar_novamente(self):
        """(3) botao 'Tentar novamente' -> not_sent_error, nao sent."""
        # O JS trata 'tentar novamente' como error no body.innerText.
        page = _FakeConfirmPage(results=[{"outbound": False, "error": True}])
        assert _run_confirm(page) == "not_sent_error"

    def test_browser_fechado_apos_clique(self):
        """(4) browser/contexto fecha -> browser_closed, nao sent."""
        page = _FakeConfirmPage(is_closed=True)
        assert _run_confirm(page) == "browser_closed"

    def test_browser_fechado_via_target_closed_exception(self):
        """(4b) evaluate levanta TargetClosedError -> browser_closed."""
        page = _FakeConfirmPage(evaluate_exc=RuntimeError("Target page, context or browser has been closed"))
        assert _run_confirm(page) == "browser_closed"

    def test_timeout_sem_message_out(self):
        """(5) timeout esperando message-out -> timeout, nao sent."""
        page = _FakeConfirmPage(results=[{"outbound": False, "error": False}])
        assert _run_confirm(page, timeout=0.1) == "timeout"

    def test_ambiguous_quando_falhas_repetidas(self):
        """(5b) erros repetidos ao ler DOM (sem sinal) -> ambiguous."""
        page = _FakeConfirmPage(evaluate_exc=RuntimeError("erro generico de leitura"))
        assert _run_confirm(page, timeout=5) == "ambiguous"

    def test_outbound_vence_erro(self):
        """Se message-out aparece, confirmed mesmo se houver toast de erro residual."""
        page = _FakeConfirmPage(results=[{"outbound": True, "error": True}])
        assert _run_confirm(page) == "confirmed"

    def test_mensagem_vazia_retorna_ambiguous(self):
        page = _FakeConfirmPage(results=[{"outbound": True, "error": False}])
        assert _run_confirm(page, mensagem="   ", timeout=0.1) == "ambiguous"


class TestSettleSentDoneSoComOutboundConfirmado:
    """(6) settle_sent_done so pode ocorrer quando outbound_confirmed=True (via confirmed)."""

    def test_confirmed_settled_gera_settle_sent_done(self, tmp_path):
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)
        _, settle_mock = _run_send(camp, [_safe_lead()])  # confirm="confirmed", settle settled
        names = [s[0] for s in stages]
        assert "settle_sent_done" in names
        sent_stage = [s for s in stages if s[0] == "settle_sent_done"][0]
        assert sent_stage[2] is True  # outbound_confirmed=True
        assert any(c.args[:3] == ("res-1", "tok-1", "sent") for c in settle_mock.call_args_list)
        assert len(camp.checkpoint._data["sent_leads"]) == 1

    def test_nao_confirma_nao_gera_settle_sent_done(self, tmp_path):
        """Caso Fabio Cell: clique confirmado mas mensagem nao aparece no historico."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)
        fabio = {
            "lead": {"id": "lead-fabio", "nome": "Fabio Cell", "grupo": "assistencias"},
            "tel_norm": "5521964212796", "nome": "Fabio Cell", "masked": "5521****2796",
            "reservation_id": "res-fabio", "reservation_token": "tok-fabio",
        }
        _, settle_mock = _run_send(camp, [fabio], confirm="timeout")
        names = [s[0] for s in stages]
        assert "send_clicked" in names          # clicou em Enviar
        assert "settle_sent_done" not in names   # NAO marcou sent
        assert "send_clicked_needs_reconciliation" in names
        # NUNCA chama settle com "sent"
        assert not any(c.args[:3] == ("res-fabio", "tok-fabio", "sent") for c in settle_mock.call_args_list)
        assert len(camp.checkpoint._data["sent_leads"]) == 0