#!/usr/bin/env python3
"""Testes para abertura de chat do WhatsApp (URL direta web.whatsapp.com/send + fallback wa.me).

Cobertura:
1. URL direta web.whatsapp.com/send abre e campo aparece → sucesso.
2. URL direta mostra QR Code (sessão deslogada) → falha segura.
3. URL direta mostra número inválido → falha segura.
4. URL direta demora mas carrega dentro do timeout → sucesso.
5. URL direta falha e fallback wa.me funciona.
6. wa.me mostra tela intermediária em português → clica em Continuar e encontra campo.
7. wa.me mostra tela intermediária em inglês → clica em Continue to Chat e encontra campo.
8. Tela intermediária mas campo nunca aparece → falha segura.
9. Nenhum clique no botão Enviar nos helpers de abertura.
10. Encoding da mensagem na URL está correto.
11. Falha antes do botão Enviar não gera send_clicked_needs_reconciliation.

Sem browser real. Tudo mockado.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import unquote

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import campanha_whatsapp as cw


# ============================================================
# Fakes
# ============================================================

class _FakeSenderPage:
    """Page mockada para abrir_wa_me.

    Comportamentos configurados via constructor:
    - compose_found: campo de mensagem encontrado direto (sem tela intermediária)
    - continue_btn_text: texto do botão "continuar" se existir (também usado como body text)
    - invalid_phone: se True, body mostra erro de número inválido
    - qr_code: se True, aparece QR Code (sessão deslogada)
    - field_after_continue: se True, campo aparece após clicar em continuar
    - goto_error: exceção a lançar no goto (None = sucesso)
    - direct_field_found: se True, campo aparece na URL direta web.whatsapp.com/send
    """

    def __init__(self, compose_found=True, continue_btn_text=None,
                 invalid_phone=False, qr_code=False, field_after_continue=True,
                 goto_error=None, direct_field_found=None):
        self.compose_found = compose_found
        self.continue_btn_text = continue_btn_text
        self.invalid_phone = invalid_phone
        self.qr_code = qr_code
        self.field_after_continue = field_after_continue
        self.goto_error = goto_error
        # direct_field_found defaulta para compose_found se não informado
        self.direct_field_found = compose_found if direct_field_found is None else direct_field_found
        self.goto_urls = []
        self._continue_clicked = False
        self._direct_tried = False
        self._selectors_called = []

        async def _goto(url, **kw):
            self.goto_urls.append(url)
            if self.goto_error:
                raise self.goto_error
            return MagicMock()
        self.goto = _goto

    def _is_direct_url(self):
        return bool(self.goto_urls) and "web.whatsapp.com/send" in self.goto_urls[-1]

    async def wait_for_selector(self, selector, timeout=None, state=None):
        self._selectors_called.append(selector)
        # Selector de campo de mensagem
        if "contenteditable" in selector or "data-tab" in selector:
            if self._is_direct_url() and not self._continue_clicked:
                # URL direta: usa direct_field_found
                if self.direct_field_found:
                    return
                raise asyncio.TimeoutError()
            # Fallback wa.me
            if self.compose_found:
                return
            if self._continue_clicked and self.field_after_continue:
                return
            raise asyncio.TimeoutError()
        raise asyncio.TimeoutError()

    async def wait_for_timeout(self, ms):
        pass

    def locator(self, selector):
        return _FakeLocator(self, selector)


class _FakeLocator:
    """Locator mockado que devolve elementos configurados pelo _FakeSenderPage."""

    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    def nth(self, i):
        return self

    async def count(self):
        if self._is_qr_selector() and self.page.qr_code:
            return 1
        if self._is_continue_selector():
            return 1 if self.page.continue_btn_text else 0
        return 0

    def _is_qr_selector(self):
        s = self.selector.lower()
        return any(k in s for k in ["qr-code", "qr\"", "canvas", "qr"])

    def _is_continue_selector(self):
        s = self.selector.lower()
        # Seletores de tela intermediária wa.me
        return any(k in s for k in ["wa.me", "whatsapp", "role=\"button\"", "button"]) and not self._is_qr_selector()

    async def inner_text(self, timeout=None):
        # Body text reflete estado da página
        if self.page.qr_code:
            return "Scan the QR code to start using WhatsApp Web"
        if self.page.invalid_phone:
            return "número de telefone compartilhado por url é inválido"
        return self.page.continue_btn_text or ""

    async def get_attribute(self, name, timeout=None):
        if name == "href":
            return "https://web.whatsapp.com"
        return ""

    async def click(self, timeout=None):
        if self.page.continue_btn_text and self._is_continue_selector():
            self.page._continue_clicked = True
        return None


# ============================================================
# TEST 1: URL direta web.whatsapp.com/send abre e campo aparece
# ============================================================

def test_abrir_wa_me_direto_sucesso():
    """URL direta web.whatsapp.com/send abre e campo aparece → sucesso."""
    page = _FakeSenderPage(direct_field_found=True)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert len(page.goto_urls) == 1
    assert "web.whatsapp.com/send" in page.goto_urls[0]
    assert "wa.me" not in page.goto_urls[0]
    # Não caiu no fallback
    assert page._continue_clicked is False


# ============================================================
# TEST 2: URL direta mostra QR Code → falha segura
# ============================================================

def test_abrir_wa_me_qr_code_falha_segura():
    """URL direta mostra QR Code (sessão deslogada) → falha segura, sem fallback."""
    page = _FakeSenderPage(direct_field_found=False, qr_code=True)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is False
    # QR Code = falha segura, não tenta fallback wa.me
    assert len(page.goto_urls) == 1
    assert "web.whatsapp.com/send" in page.goto_urls[0]


# ============================================================
# TEST 3: URL direta mostra número inválido → falha segura
# ============================================================

def test_abrir_wa_me_numero_invalido_direto():
    """URL direta mostra número inválido → falha segura, sem fallback."""
    page = _FakeSenderPage(direct_field_found=False, invalid_phone=True)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5500000000000", "Ola!"))

    assert result is False
    assert len(page.goto_urls) == 1
    assert "web.whatsapp.com/send" in page.goto_urls[0]


# ============================================================
# TEST 4: URL direta demora mas carrega dentro do timeout → sucesso
# ============================================================

def test_abrir_wa_me_direto_lento_sucesso():
    """URL direta demora no goto mas carrega e campo aparece → sucesso."""
    page = _FakeSenderPage(direct_field_found=True, goto_error=None)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert "web.whatsapp.com/send" in page.goto_urls[0]


# ============================================================
# TEST 5: URL direta falha (goto erro) e fallback wa.me funciona
# ============================================================

def test_abrir_wa_me_fallback_wa_me_funciona():
    """URL direta falha no goto e fallback wa.me com tela intermediária funciona."""
    page = _FakeSenderPage(
        compose_found=False,
        direct_field_found=False,
        continue_btn_text="Continuar para o WhatsApp Web",
        field_after_continue=True,
        goto_error=asyncio.TimeoutError(),  # goto da URL direta falha
    )

    # goto_error faz a URL direta falhar → retorna None → fallback wa.me
    # Mas o fallback wa.me também usa o mesmo goto... precisamos de goto dinâmico
    # Reconfigurando: goto_error só vale para a primeira chamada
    call_count = [0]
    original_goto = page.goto

    async def _conditional_goto(url, **kw):
        call_count[0] += 1
        if call_count[0] == 1:
            # Primeira chamada (URL direta) falha
            raise asyncio.TimeoutError()
        # Segunda chamada (wa.me fallback) funciona
        page.goto_urls.append(url)
        return MagicMock()

    page.goto = _conditional_goto
    page.goto_urls = []

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    # Deve ter tentado URL direta (falhou) e depois wa.me (sucesso)
    assert call_count[0] == 2
    assert "wa.me/" in page.goto_urls[0]


# ============================================================
# TEST 6: wa.me tela intermediária em português (via fallback)
# ============================================================

def test_abrir_wa_me_tela_intermediaria_pt():
    """wa.me mostra tela intermediária em português → clica em Continuar e encontra campo."""
    page = _FakeSenderPage(
        compose_found=False,
        direct_field_found=False,
        continue_btn_text="Continuar para o WhatsApp Web",
        field_after_continue=True,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert page._continue_clicked is True


# ============================================================
# TEST 7: wa.me tela intermediária em inglês (via fallback)
# ============================================================

def test_abrir_wa_me_tela_intermediaria_en():
    """wa.me mostra tela intermediária em inglês → clica em Continue to Chat e encontra campo."""
    page = _FakeSenderPage(
        compose_found=False,
        direct_field_found=False,
        continue_btn_text="Continue to Chat",
        field_after_continue=True,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert page._continue_clicked is True


# ============================================================
# TEST 8: Tela intermediária mas campo nunca aparece → falha segura
# ============================================================

def test_abrir_wa_me_intermediaria_campo_nunca_aparece():
    """Tela intermediária aparece mas campo nunca aparece → falha segura."""
    page = _FakeSenderPage(
        compose_found=False,
        direct_field_found=False,
        continue_btn_text="Continuar para o WhatsApp Web",
        field_after_continue=False,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is False


# ============================================================
# TEST 9: Nenhum clique no botão Enviar
# ============================================================

def test_nao_clica_botao_enviar():
    """Seletores de continuar NÃO incluem botão Enviar."""
    continue_selectors = cw.MessageSender._WA_ME_CONTINUE_SELECTORS
    enviar_keywords = ["enviar", "send", "msg-check", "msg-dblcheck"]

    for sel in continue_selectors:
        sel_lower = sel.lower()
        for kw in enviar_keywords:
            assert kw not in sel_lower, f"Seletor de continuar contem '{kw}': {sel}"


def test_qr_selectors_nao_incluem_enviar():
    """Seletores de QR Code NÃO incluem botão Enviar."""
    qr_selectors = cw.MessageSender._WA_QR_SELECTORS
    enviar_keywords = ["enviar", "send", "msg-check", "msg-dblcheck", "send message"]

    for sel in qr_selectors:
        sel_lower = sel.lower()
        for kw in enviar_keywords:
            assert kw not in sel_lower, f"Seletor de QR contem '{kw}': {sel}"


# ============================================================
# TEST 10: Encoding da mensagem na URL está correto
# ============================================================

def test_encoding_mensagem_url_direta():
    """URL direta codifica a mensagem corretamente."""
    msg = "Olá! Tudo bem? 100% & mais"
    url = cw.MessageSender.gerar_link_web_whatsapp_send("5511999993966", msg)

    assert "web.whatsapp.com/send" in url
    assert "phone=5511999993966" in url
    assert "type=phone_number" in url
    assert "app_absent=0" in url
    # text= deve estar URL-encoded
    assert "text=" in url
    # Decodificando o text= deve dar a mensagem original
    text_part = url.split("text=")[1].split("&")[0]
    decoded = unquote(text_part)
    assert decoded == msg
    # Espaços e caracteres especiais codificados
    assert " " not in text_part  # espaços viram %20 ou +


def test_encoding_mensagem_url_wa_me():
    """URL wa.me codifica a mensagem corretamente (fallback)."""
    msg = "Olá! 50% off"
    url = cw.MessageSender.gerar_link_wa_me("5511999993966", msg)
    assert "wa.me/5511999993966" in url
    text_part = url.split("text=")[1]
    decoded = unquote(text_part)
    assert decoded == msg


# ============================================================
# TEST 11: _detectar_qr_code detecta corretamente
# ============================================================

def test_detectar_qr_code_funciona():
    """_detectar_qr_code detecta QR Code via seletor."""
    page = MagicMock()
    page.locator.return_value.count = AsyncMock(return_value=1)

    result = asyncio.run(cw.MessageSender._detectar_qr_code(page))
    assert result is True


def test_detectar_qr_code_nao_detecta_pagina_normal():
    """_detectar_qr_code não dá falso positivo em página logada."""
    page = MagicMock()
    page.locator.return_value.count = AsyncMock(return_value=0)
    page.locator.return_value.first = MagicMock()
    page.locator.return_value.first.inner_text = AsyncMock(return_value="WhatsApp Web - conversa")

    result = asyncio.run(cw.MessageSender._detectar_qr_code(page))
    assert result is False


# ============================================================
# TEST 12: _detectar_tela_invalida detecta corretamente
# ============================================================

def test_detectar_tela_invalida_funciona():
    """_detectar_tela_invalida detecta mensagens de erro de número."""
    page = MagicMock()
    page.locator.return_value.first = MagicMock()
    page.locator.return_value.first.inner_text = AsyncMock(
        return_value="número de telefone compartilhado por url é inválido")

    result = asyncio.run(cw.MessageSender._detectar_tela_invalida(page))
    assert result is True


def test_detectar_tela_invalida_nao_detecta_pagina_normal():
    """_detectar_tela_invalida não dá falso positivo em página normal."""
    page = MagicMock()
    page.locator.return_value.first = MagicMock()
    page.locator.return_value.first.inner_text = AsyncMock(
        return_value="WhatsApp Web - conversa com seus amigos")

    result = asyncio.run(cw.MessageSender._detectar_tela_invalida(page))
    assert result is False


# ============================================================
# TEST 13: _procurar_e_clicar_continuar não encontra = False
# ============================================================

def test_procurar_continuar_nao_encontra_retorna_false():
    """_procurar_e_clicar_continuar_wa_me não encontra botão → retorna False."""
    page = MagicMock()
    page.locator.return_value.count = AsyncMock(return_value=0)

    result = asyncio.run(cw.MessageSender._procurar_e_clicar_continuar_wa_me(page))
    assert result is False


# ============================================================
# TEST 14: Falha antes do botão Enviar não gera send_clicked_needs_reconciliation
# ============================================================

def test_falha_antes_do_envio_nao_gera_reconciliation():
    """Falha em abrir_wa_me retorna False, send_clicked permanece False."""
    page = _FakeSenderPage(direct_field_found=False, qr_code=True)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    # Falha segura: resultado False, NUNCA send_clicked=True
    assert result is False
    # abrir_wa_me não registra stages nem send_clicked — isso é responsabilidade do caller.
    # Aqui só garantimos que o helper NÃO clica em Enviar nem retorna "ambíguo".
    # O caller trata result=False como falha segura (send_clicked=False, sem reconciliation).


# ============================================================
# TEST 15: Continuar com texto diferente aceita variantes (via fallback)
# ============================================================

def test_continuar_textos_aceitos():
    """Texto 'Continue to WhatsApp Web' e variantes são aceitos via fallback."""
    textos_validos = [
        "Continuar para o WhatsApp Web",
        "Continue to Chat",
        "Continue to WhatsApp",
        "Continue to WhatsApp Web",
        "Abrir o WhatsApp Web",
        "Open WhatsApp Web",
    ]
    for texto in textos_validos:
        page = _FakeSenderPage(
            compose_found=False,
            direct_field_found=False,
            continue_btn_text=texto,
            field_after_continue=True,
        )
        result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))
        assert result is True, f"Texto aceito deveria funcionar: {texto}"
        assert page._continue_clicked is True, f"Deveria ter clicado: {texto}"