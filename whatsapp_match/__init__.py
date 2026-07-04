#!/usr/bin/env python3
"""
whatsapp_match/__init__.py — Módulo de match de leads no WhatsApp Web.

Funções para pesquisar um telefone no WhatsApp Web, abrir a conversa,
confirmar que pertence ao número correto, detectar mensagens de saída,
e verificar se correspondem à campanha atual via fingerprint.

NUNCA envia mensagens. Apenas leitura.
"""

from .matcher import (
    MatchResult,
    MatchStatus,
    pesquisar_telefone,
    abrir_conversa,
    confirmar_numero,
    detectar_mensagem_saida,
    extrair_texto_mensagem,
    fazer_match_completo,
    _fechar_modal,
)

__all__ = [
    "MatchResult",
    "MatchStatus",
    "pesquisar_telefone",
    "abrir_conversa",
    "confirmar_numero",
    "detectar_mensagem_saida",
    "extrair_texto_mensagem",
    "fazer_match_completo",
    "_fechar_modal",
]
