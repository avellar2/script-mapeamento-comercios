"""
Testes de fingerprint de mensagens para reconciliação de campanhas.

Roda com:
    python -m pytest tests/test_campaign_fingerprint.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.campaign_fingerprint import (
    normalizar_texto,
    fingerprint_mensagem,
    chaves_estaveis_da_campanha,
    corresponde_campanha,
)


def test_normalizar_texto():
    """Normaliza texto corretamente."""
    assert normalizar_texto("Olá, tudo bem?") == "ola tudo bem"
    assert normalizar_texto("  Bom  DIA!  ") == "bom dia"
    assert normalizar_texto("") == ""


def test_normalizar_acentos():
    """Remove acentos."""
    assert normalizar_texto("Você está na área?") == "voce esta na area"


def test_fingerprint_estavel():
    """Mesmo texto gera mesmo hash."""
    fp1 = fingerprint_mensagem("Olá, tudo bem?")
    fp2 = fingerprint_mensagem("Olá, tudo bem?")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex


def test_fingerprint_vazio():
    """Texto vazio retorna string vazia."""
    assert fingerprint_mensagem("") == ""
    assert fingerprint_mensagem(None) == ""


def test_chaves_avgestao_assistencias_primeiro_contato():
    """Retorna frases-chave para avgestao:assistencias:primeiro_contato."""
    frases = chaves_estaveis_da_campanha("avgestao:assistencias:primeiro_contato:v1")
    assert "ola tudo bem" in frases
    assert "avgestao" in frases
    assert "assistencia tecnica" in frases


def test_chaves_avgestao_assistencias_follow_up():
    """Retorna frases-chave para avgestao:assistencias:follow_up."""
    frases = chaves_estaveis_da_campanha("avgestao:assistencias:follow_up:v1")
    assert "falei com voce" in frases
    assert "semana passada" in frases


def test_chaves_campaign_key_invalida():
    """Campaign key inválida retorna lista vazia."""
    assert chaves_estaveis_da_campanha("") == []
    assert chaves_estaveis_da_campanha("invalida") == []


def test_corresponde_campanha_true():
    """Mensagem que contém frases da campanha retorna True."""
    msg = "Olá, tudo bem? Aqui é da AVGESTÃO. Vi que você faz assistência técnica..."
    assert corresponde_campanha(msg, "avgestao:assistencias:primeiro_contato:v1") is True


def test_corresponde_campanha_false():
    """Mensagem não relacionada retorna False."""
    msg = "Promoção imperdível! Compre agora com 50% de desconto!"
    assert corresponde_campanha(msg, "avgestao:assistencias:primeiro_contato:v1") is False


def test_corresponde_campanha_vazio():
    """Texto vazio retorna False."""
    assert corresponde_campanha("", "avgestao:assistencias:primeiro_contato:v1") is False
    assert corresponde_campanha(None, "avgestao:assistencias:primeiro_contato:v1") is False


def test_corresponde_campanha_campaign_key_invalida():
    """Campaign key inválida retorna False."""
    assert corresponde_campanha("Olá, tudo bem?", "") is False
