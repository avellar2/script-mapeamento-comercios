#!/usr/bin/env python3
"""Regressao do travamento silencioso do modo semi apos confirmacao manual.

Cobre a correcao que garante:
- input() nao bloqueia o event loop (asyncio.to_thread + asyncio.wait_for);
- stage manual_confirmed persistido imediatamente apos 's';
- stage post_manual_confirmed;
- ladder de stages pos-confirmacao com timeout duro;
- falha ANTES do clique em Enviar = send_clicked=false, sem needs_manual_reconciliation;
- falha DEPOIS do clique confirmado = send_clicked=true, pode gerar send_clicked_needs_reconciliation;
- contexto/locks limpos e reserva tratada pelo fluxo oficial em falha pre-clique.

Sem browser real, sem envio real. Tudo mockado.
"""
import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import campanha_whatsapp as cw


# ============================================================
# Fakes
# ============================================================

class _FakeComposeLocator:
    """Locator do compose box: .first retorna self; inner_text/fill mockados."""

    def __init__(self, text="mensagem preenchida"):
        self._text = text
        self.filled = []

    @property
    def first(self):
        return self

    async def inner_text(self, timeout=None):
        return self._text

    async def fill(self, text, timeout=None):
        self.filled.append(text)
        return None


class _FakeSenderPage:
    """Page do sender. wait_for_selector distingue compose vs mensagem existente."""

    def __init__(self, compose_found=True, existing_found=False, compose_text="mensagem preenchida"):
        self.compose_found = compose_found
        self.existing_found = existing_found
        self.compose_text = compose_text

    async def wait_for_selector(self, selector, timeout=None):
        if "contenteditable" in selector:
            if not self.compose_found:
                raise asyncio.TimeoutError()
            return True
        # outgoing / existing message selectors
        if self.existing_found:
            return True
        raise asyncio.TimeoutError()

    def locator(self, selector):
        return _FakeComposeLocator(self.compose_text)


def _build_semi_campaign(tmp_path, dry_run=False):
    args_list = ["semi", "--dry-run"] if dry_run else ["semi"]
    with patch.object(cw, "CHECKPOINT_DIR", tmp_path):
        camp = cw.CampanhaWhatsApp(cw.build_parser().parse_args(args_list))
    camp.checkpoint.carregar()
    camp.safety = MagicMock()
    camp.safety.deve_parar.return_value = (False, "")
    camp.safety.aguardar_intervalo = MagicMock()
    camp._renderizar_mensagem = MagicMock(return_value="Ola mensagem de teste")
    camp._hash_mensagem = MagicMock(return_value="abcdef0123456789")
    return camp


def _safe_lead():
    return {
        "lead": {"id": "lead-1", "nome": "RM INFORMATICA", "cidade": "Rio", "grupo": "assistencias"},
        "tel_norm": "5521999993966",
        "nome": "RM INFORMATICA",
        "masked": "5521****3966",
        "reservation_id": "res-1",
        "reservation_token": "tok-1",
    }


def _record_stages(camp):
    stages = []
    orig = camp.checkpoint.registrar_estagio

    def rec(lead_id, stage, send_clicked=None, outbound_confirmed=None):
        stages.append((stage, send_clicked, outbound_confirmed))
        return orig(lead_id, stage, send_clicked, outbound_confirmed)

    camp.checkpoint.registrar_estagio = rec
    return stages


def _run_send(camp, safe_leads, page=None, abrir=None, localizar=None, clicar=None,
              settle=None, input_value="s"):
    if page is None:
        page = _FakeSenderPage()
    fake_sessao = MagicMock()
    fake_sessao.page = page
    fake_sessao.esta_valida.return_value = True
    fake_sessao.__aenter__ = AsyncMock(return_value=fake_sessao)
    fake_sessao.__aexit__ = AsyncMock(return_value=None)
    settle_side = settle if settle is not None else (lambda *a, **k: {"outcome": "settled"})
    settle_mock = MagicMock(side_effect=settle_side)
    patches = [
        patch.object(cw, "SessaoWhatsApp", return_value=fake_sessao),
        patch("sender_int.settle_lead", settle_mock),
        patch.object(cw.MessageSender, "abrir_wa_me",
                      AsyncMock(side_effect=abrir) if abrir is not None else AsyncMock(return_value=True)),
        patch.object(cw.MessageSender, "localizar_botao_enviar",
                      AsyncMock(side_effect=localizar) if localizar is not None else AsyncMock(return_value=True)),
        patch.object(cw.MessageSender, "clicar_enviar",
                      AsyncMock(side_effect=clicar) if clicar is not None else AsyncMock(return_value=True)),
        patch("builtins.input", return_value=input_value),
    ]
    for p in patches:
        p.start()
    try:
        asyncio.run(camp._enviar_leads_async(safe_leads))
    finally:
        for p in patches:
            p.stop()
    return fake_sessao, settle_mock


# ============================================================
# Testes
# ============================================================

class TestSemiSenderHang:
    """Regressao do travamento silencioso do modo semi apos confirmacao manual."""

    def test_s_confirma_avanca_para_wa_me_opening(self, tmp_path):
        """(1) Confirmar 's' avanca pós manual_confirmed ate settle_sent_done."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()])
        names = [s[0] for s in stages]
        assert "prompt_manual" in names
        assert "manual_confirmed" in names
        assert "post_manual_confirmed" in names
        assert "wa_me_opening" in names
        assert "wa_me_loaded" in names
        assert "send_clicked" in names
        assert "settle_sent_done" in names
        assert len(camp.checkpoint._data["sent_leads"]) == 1

    def test_timeout_wa_me_falha_segura_antes_clique(self, tmp_path):
        """(2) Timeout abrindo wa.me -> falha segura, send_clicked=false."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)

        async def _boom(*a, **k):
            raise asyncio.TimeoutError()

        _run_send(camp, [_safe_lead()], abrir=_boom)
        names = [s[0] for s in stages]
        assert "wa_me_timeout" in names
        assert "send_clicked" not in names
        assert "send_clicked_needs_reconciliation" not in names
        assert "needs_manual_reconciliation" not in names
        assert any(f["reason"] == "wa_me_timeout" for f in camp.checkpoint._data["failed_leads"])

    def test_timeout_botao_enviar_falha_segura_antes_clique(self, tmp_path):
        """(3) Timeout procurando botao Enviar -> falha segura antes do clique."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)

        async def _boom(*a, **k):
            raise asyncio.TimeoutError()

        _run_send(camp, [_safe_lead()], localizar=_boom)
        names = [s[0] for s in stages]
        assert "send_button_timeout" in names
        assert "send_clicking" not in names
        assert "send_clicked" not in names
        assert "send_clicked_needs_reconciliation" not in names

    def test_send_clicked_false_nao_gera_reconciliation(self, tmp_path):
        """(4) send_clicked=false em falha pre-clique nao gera needs_manual_reconciliation."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()], localizar=AsyncMock(return_value=False))
        names = [s[0] for s in stages]
        assert "send_button_not_found" in names
        assert "send_clicked" not in names
        assert "send_clicked_needs_reconciliation" not in names
        assert "needs_manual_reconciliation" not in names
        # nenhum stage pre-clique carrega send_clicked=True
        post_click = {"send_clicked", "send_clicked_needs_reconciliation",
                      "needs_manual_reconciliation", "outbound_confirming", "settle_sent_done"}
        for (st, sc, oc) in stages:
            if st not in post_click:
                assert sc is not True, f"stage {st} marcou send_clicked=True antes do clique"

    def test_send_clicked_true_outbound_fail_gera_reconciliation(self, tmp_path):
        """(5) send_clicked=true + falha outbound -> send_clicked_needs_reconciliation."""
        camp = _build_semi_campaign(tmp_path)
        stages = _record_stages(camp)
        _run_send(camp, [_safe_lead()], settle=lambda *a, **k: {"outcome": "failed"})
        names = [s[0] for s in stages]
        assert "send_clicked" in names
        assert "outbound_confirming" in names
        assert "send_clicked_needs_reconciliation" in names
        rec = [s for s in stages if s[0] == "send_clicked_needs_reconciliation"][0]
        assert rec[1] is True and rec[2] is False

    def test_contexto_fechado_em_falha_antes_clique(self, tmp_path):
        """(6) SessaoWhatsApp.__aexit__ chamado (contexto limpo) em falha pre-clique."""
        camp = _build_semi_campaign(tmp_path)

        async def _boom(*a, **k):
            raise asyncio.TimeoutError()

        fake_sessao, _ = _run_send(camp, [_safe_lead()], abrir=_boom)
        assert fake_sessao.__aexit__.called

    def test_reserva_tratada_pelo_fluxo_oficial_em_falha_pre_clique(self, tmp_path):
        """(7) Reserva e settling via settle_lead('failed') em falha antes do clique."""
        camp = _build_semi_campaign(tmp_path)

        async def _boom(*a, **k):
            raise asyncio.TimeoutError()

        _, settle_mock = _run_send(camp, [_safe_lead()], abrir=_boom)
        calls = settle_mock.call_args_list
        assert any(c.args[:3] == ("res-1", "tok-1", "failed") for c in calls), \
            "esperado settle_lead('res-1','tok-1','failed',...) em falha pre-clique"

    def test_timeout_input_manual_falha_segura(self, tmp_path):
        """(8) Timeout no input() manual -> safe release/skip, sem reconciliacao."""
        camp = _build_semi_campaign(tmp_path)
        camp.args.manual_confirm_timeout_seconds = 0.3
        stages = _record_stages(camp)
        fake_sessao = MagicMock()
        fake_sessao.page = _FakeSenderPage()
        fake_sessao.esta_valida.return_value = True
        fake_sessao.__aenter__ = AsyncMock(return_value=fake_sessao)
        fake_sessao.__aexit__ = AsyncMock(return_value=None)
        settle_mock = MagicMock(side_effect=lambda *a, **k: {"outcome": "settled"})

        def _slow_input(_prompt):
            time.sleep(2)
            return "s"

        patches = [
            patch.object(cw, "SessaoWhatsApp", return_value=fake_sessao),
            patch("sender_int.settle_lead", settle_mock),
            patch.object(cw.MessageSender, "abrir_wa_me", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "localizar_botao_enviar", AsyncMock(return_value=True)),
            patch.object(cw.MessageSender, "clicar_enviar", AsyncMock(return_value=True)),
            patch("builtins.input", side_effect=_slow_input),
        ]
        for p in patches:
            p.start()
        try:
            asyncio.run(camp._enviar_leads_async([_safe_lead()]))
        finally:
            for p in patches:
                p.stop()
        names = [s[0] for s in stages]
        assert "manual_confirm_timeout" in names
        assert "manual_confirmed" not in names
        assert "wa_me_opening" not in names
        assert "send_clicked" not in names
        assert "send_clicked_needs_reconciliation" not in names
        assert any(c.args[:3] == ("res-1", "tok-1", "released") for c in settle_mock.call_args_list)
        assert any(s["reason"] == "manual_confirm_timeout" for s in camp.checkpoint._data["skipped_leads"])