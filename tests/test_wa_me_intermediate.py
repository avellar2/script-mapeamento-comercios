#!/usr/bin/env python3
"""Testes para tratamento de tela intermediária do wa.me.

Cobertura:
1. wa.me redireciona direto e campo aparece → sucesso.
2. wa.me mostra tela intermediária em português → clica em Continuar e encontra campo.
3. wa.me mostra tela intermediária em inglês → clica em Continue to Chat e encontra campo.
4. wa.me mostra número inválido → retorna falha segura.
5. tela intermediária mas campo nunca aparece → retorna falha segura.
6. Nenhum clique no botão Enviar nos helpers de tela intermediária.

Sem browser real. Tudo mockado.
"""
import asyncio
import sys
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

class _FakeSenderPage:
    """Page mockada para abrir_wa_me.

    Comportamentos configurados via constructor:
    - compose_found: campo de mensagem encontrado direto (sem tela intermediária)
    - continue_btn_text: texto do botão "continuar" se existir
    - invalid_phone: se True, botão ou tela mostra erro de número inválido
    - field_after_continue: se True, campo aparece após clicar em continuar
    """

    def __init__(self, compose_found=True, continue_btn_text=None,
                 invalid_phone=False, field_after_continue=True,
                 goto_error=None):
        self.compose_found = compose_found
        self.continue_btn_text = continue_btn_text
        self.invalid_phone = invalid_phone
        self.field_after_continue = field_after_continue
        self.goto_error = goto_error
        self.goto_url = None
        self._continue_clicked = False
        self._selectors_called = []

        async def _goto(url, **kw):
            self.goto_url = url
            if self.goto_error:
                raise self.goto_error
            return MagicMock()
        self.goto = _goto

    async def wait_for_selector(self, selector, timeout=None, state=None):
        self._selectors_called.append(selector)
        # Selector de campo de mensagem
        if "contenteditable" in selector or "data-tab" in selector:
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
        if self._is_continue_selector():
            return 1 if self.page.continue_btn_text else 0
        return 0

    def _is_continue_selector(self):
        s = self.selector.lower()
        return any(k in s for k in ["wa.me", "whatsapp", "role=\"button\"", "button"])

    async def inner_text(self, timeout=None):
        return self.page.continue_btn_text or ""

    async def get_attribute(self, name, timeout=None):
        if name == "href":
            return "https://web.whatsapp.com"
        return ""

    async def click(self, timeout=None):
        if self.page.continue_btn_text:
            self.page._continue_clicked = True
        return None


# ============================================================
# TEST 1: wa.me direto - campo aparece
# ============================================================

def test_abrir_wa_me_direto_sucesso():
    """wa.me redireciona direto e campo aparece → sucesso."""
    page = _FakeSenderPage(compose_found=True)

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert page.goto_url is not None
    assert "wa.me" in page.goto_url


# ============================================================
# TEST 2: wa.me tela intermediária em português
# ============================================================

def test_abrir_wa_me_tela_intermediaria_pt():
    """wa.me mostra tela intermediária em português → clica em Continuar e encontra campo."""
    page = _FakeSenderPage(
        compose_found=False,
        continue_btn_text="Continuar para o WhatsApp Web",
        field_after_continue=True,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert page._continue_clicked is True


# ============================================================
# TEST 3: wa.me tela intermediária em inglês
# ============================================================

def test_abrir_wa_me_tela_intermediaria_en():
    """wa.me mostra tela intermediária em inglês → clica em Continue to Chat e encontra campo."""
    page = _FakeSenderPage(
        compose_found=False,
        continue_btn_text="Continue to Chat",
        field_after_continue=True,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is True
    assert page._continue_clicked is True


# ============================================================
# TEST 4: wa.me número inválido
# ============================================================

def test_abrir_wa_me_numero_invalido():
    """wa.me mostra número inválido → retorna falha segura."""
    page = _FakeSenderPage(
        compose_found=False,
        continue_btn_text="número de telefone compartilhado por url é inválido",
        invalid_phone=True,
        field_after_continue=False,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5500000000000", "Ola!"))

    assert result is False


# ============================================================
# TEST 5: tela intermediária mas campo nunca aparece
# ============================================================

def test_abrir_wa_me_intermediaria_campo_nunca_aparece():
    """Tela intermediária aparece mas campo nunca aparece → falha segura."""
    page = _FakeSenderPage(
        compose_found=False,
        continue_btn_text="Continuar para o WhatsApp Web",
        field_after_continue=False,
    )

    result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))

    assert result is False


# ============================================================
# TEST 6: Nenhum clique no botão Enviar
# ============================================================

def test_nao_clica_botao_enviar():
    """Seletores de continuar NÃO incluem botão Enviar."""
    continue_selectors = cw.MessageSender._WA_ME_CONTINUE_SELECTORS
    enviar_keywords = ["enviar", "send", "msg-check", "msg-dblcheck"]

    for sel in continue_selectors:
        sel_lower = sel.lower()
        for kw in enviar_keywords:
            assert kw not in sel_lower, f"Seletor de continuar contem '{kw}': {sel}"


# ============================================================
# TEST 7: _detectar_tela_invalida detecta corretamente
# ============================================================

def test_detectar_tela_invalida_funciona():
    """_detectar_tela_invalida detecta mensagens de erro de número."""
    page = MagicMock()

    body_with_error = MagicMock()
    body_with_error._text = "número de telefone compartilhado por url é inválido"

    page.locator.return_value.first = body_with_error

    async def mock_inner_text(timeout=None):
        return "número de telefone compartilhado por url é inválido"

    body_with_error.inner_text = AsyncMock(side_effect=mock_inner_text)

    result = asyncio.run(cw.MessageSender._detectar_tela_invalida(page))
    assert result is True


# ============================================================
# TEST 8: _detectar_tela_invalida não detecta página normal
# ============================================================

def test_detectar_tela_invalida_nao_detecta_pagina_normal():
    """_detectar_tela_invalida não dá falso positivo em página normal do WhatsApp."""
    page = MagicMock()

    body_normal = MagicMock()
    body_normal._text = "WhatsApp Web - conversa com seus amigos"

    page.locator.return_value.first = body_normal

    async def mock_inner_text(timeout=None):
        return "WhatsApp Web - conversa com seus amigos"

    body_normal.inner_text = AsyncMock(side_effect=mock_inner_text)

    result = asyncio.run(cw.MessageSender._detectar_tela_invalida(page))
    assert result is False


# ============================================================
# TEST 9: _procurar_e_clicar_continuar não encontra = False
# ============================================================

def test_procurar_continuar_nao_encontra_retorna_false():
    """_procurar_e_clicar_continuar_wa_me não encontra botão → retorna False."""
    page = MagicMock()
    page.locator.return_value.count = AsyncMock(return_value=0)

    result = asyncio.run(cw.MessageSender._procurar_e_clicar_continuar_wa_me(page))
    assert result is False


# ============================================================
# TEST 10: Continuar com texto diferente aceita variantes
# ============================================================

def test_continuar_textos_aceitos():
    """Texto 'Continue to WhatsApp Web' e variantes são aceitos."""
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
            continue_btn_text=texto,
            field_after_continue=True,
        )
        result = asyncio.run(cw.MessageSender.abrir_wa_me(page, "5511999993966", "Ola!"))
        assert result is True, f"Texto aceito deveria funcionar: {texto}"
        assert page._continue_clicked is True, f"Deveria ter clicado: {texto}"
