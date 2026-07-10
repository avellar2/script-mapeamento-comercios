"""
Testes de geração e validação de campaign_key.

Roda com:
    python -m pytest tests/test_campaign_key.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.campaign_key import (
    gerar_campaign_key,
    validar_campaign_key,
    extrair_partes,
    interaction_type_from_campaign_key,
    PRIMEIRO_CONTATO_V1,
    FOLLOW_UP_V1,
)


def test_gerar_primeiro_contato():
    """Gera campaign_key para primeiro contato."""
    chave = gerar_campaign_key("avgestao", "assistencias", "primeiro_contato", "v1")
    assert chave == "avgestao:assistencias:primeiro_contato:v1"


def test_gerar_follow_up():
    """Gera campaign_key para follow-up."""
    chave = gerar_campaign_key("avgestao", "assistencias", "follow_up", "v1")
    assert chave == "avgestao:assistencias:follow_up:v1"


def test_gerar_versao_diferente():
    """Gera campaign_key com versão diferente."""
    chave = gerar_campaign_key("avgestao", "refrigeracao", "primeiro_contato", "v2")
    assert chave == "avgestao:refrigeracao:primeiro_contato:v2"


def test_gerar_produto_invalido():
    """Produto inválido levanta ValueError."""
    try:
        gerar_campaign_key("", "assistencias", "primeiro_contato", "v1")
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass


def test_gerar_tipo_invalido():
    """Tipo de abordagem inválido levanta ValueError."""
    try:
        gerar_campaign_key("avgestao", "assistencias", "desconhecido", "v1")
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass


def test_validar_valida():
    """Valida campaign_key correta."""
    assert validar_campaign_key("avgestao:assistencias:primeiro_contato:v1") is True


def test_validar_invalida():
    """Rejeita campaign_key inválida."""
    assert validar_campaign_key("") is False
    assert validar_campaign_key("invalida") is False
    assert validar_campaign_key("avgestao:assistencias:primeiro_contato") is False
    assert validar_campaign_key("avgestao:assistencias:primeiro_contato:versao1") is False


def test_validar_constantes():
    """Constantes são válidas."""
    assert validar_campaign_key(PRIMEIRO_CONTATO_V1) is True
    assert validar_campaign_key(FOLLOW_UP_V1) is True


def test_extrair_partes():
    """Extrai partes corretamente."""
    partes = extrair_partes("avgestao:assistencias:primeiro_contato:v1")
    assert partes is not None
    assert partes["produto"] == "avgestao"
    assert partes["grupo"] == "assistencias"
    assert partes["tipo_abordagem"] == "primeiro_contato"
    assert partes["versao"] == "v1"


def test_extrair_partes_invalida():
    """Extrair partes de chave inválida retorna None."""
    assert extrair_partes("") is None
    assert extrair_partes("invalida") is None


def test_interaction_type_primeiro_contato():
    """primeiro_contato mapeia para primeira_abordagem."""
    assert interaction_type_from_campaign_key("avgestao:assistencias:primeiro_contato:v1") == "primeira_abordagem"


def test_interaction_type_follow_up():
    """follow_up mapeia para follow_up."""
    assert interaction_type_from_campaign_key("avgestao:assistencias:follow_up:v1") == "follow_up"


def test_interaction_type_desconhecido():
    """Tipo desconhecido retorna None."""
    assert interaction_type_from_campaign_key("avgestao:assistencias:outro:v1") is None


def test_interaction_type_invalido():
    """Chave inválida retorna None."""
    assert interaction_type_from_campaign_key("") is None
