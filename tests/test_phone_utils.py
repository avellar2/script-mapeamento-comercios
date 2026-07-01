"""
Testes de normalização de telefone brasileiro.

Roda com:
    python -m pytest tests/test_phone_utils.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.phone_utils import normalizar_telefone_br, variantes_busca_telefone


def test_normalizar_com_55():
    """Já começa com 55 e tem 13 dígitos (celular)."""
    assert normalizar_telefone_br("5521999999999") == "5521999999999"


def test_normalizar_sem_55():
    """Sem 55, 11 dígitos (celular com DDD)."""
    assert normalizar_telefone_br("21999999999") == "5521999999999"


def test_normalizar_com_parenteses():
    """Formato brasileiro com parênteses, espaço e hífen."""
    assert normalizar_telefone_br("(21) 99999-9999") == "5521999999999"


def test_normalizar_com_mais_55():
    """Formato internacional com +55."""
    assert normalizar_telefone_br("+5521999999999") == "5521999999999"


def test_normalizar_com_00():
    """Prefixo 00 internacional (00 + 55 + DDD + número)."""
    assert normalizar_telefone_br("005521999999999") == "5521999999999"


def test_normalizar_com_0_inicial():
    """Zero inicial (021...)."""
    assert normalizar_telefone_br("021999999999") == "5521999999999"


def test_normalizar_fixo():
    """Telefone fixo com 10 dígitos."""
    assert normalizar_telefone_br("2133333333") == "552133333333"


def test_normalizar_fixo_com_55():
    """Telefone fixo já com 55."""
    assert normalizar_telefone_br("552133333333") == "552133333333"


def test_normalizar_invalido_curto():
    """Número muito curto (sem DDD)."""
    assert normalizar_telefone_br("999999999") is None


def test_normalizar_invalido_vazio():
    """String vazia."""
    assert normalizar_telefone_br("") is None


def test_normalizar_invalido_none():
    """None."""
    assert normalizar_telefone_br(None) is None


def test_normalizar_invalido_letras():
    """Apenas letras."""
    assert normalizar_telefone_br("abc") is None


def test_normalizar_ddd_11():
    """DDD 11 (São Paulo)."""
    assert normalizar_telefone_br("11999999999") == "5511999999999"


def test_normalizar_ddd_31():
    """DDD 31 (Belo Horizonte)."""
    assert normalizar_telefone_br("31999999999") == "5531999999999"


def test_normalizar_ddd_41():
    """DDD 41 (Curitiba)."""
    assert normalizar_telefone_br("41999999999") == "5541999999999"


def test_normalizar_ddd_51():
    """DDD 51 (Porto Alegre)."""
    assert normalizar_telefone_br("51999999999") == "5551999999999"


def test_normalizar_ddd_61():
    """DDD 61 (Brasília)."""
    assert normalizar_telefone_br("61999999999") == "5561999999999"


def test_normalizar_ddd_71():
    """DDD 71 (Salvador)."""
    assert normalizar_telefone_br("71999999999") == "5571999999999"


def test_normalizar_ddd_81():
    """DDD 81 (Recife)."""
    assert normalizar_telefone_br("81999999999") == "5581999999999"


def test_normalizar_ddd_91():
    """DDD 91 (Belém)."""
    assert normalizar_telefone_br("91999999999") == "5591999999999"


def test_normalizar_ddd_85():
    """DDD 85 (Fortaleza)."""
    assert normalizar_telefone_br("85999999999") == "5585999999999"


def test_normalizar_ddd_invalido_00():
    """DDD 00 inválido."""
    assert normalizar_telefone_br("00999999999") is None


def test_normalizar_ddd_invalido_10():
    """DDD 10 inválido."""
    assert normalizar_telefone_br("10999999999") is None


def test_variantes_busca_celular():
    """Gera variantes para celular com 13 dígitos."""
    variantes = variantes_busca_telefone("5521999999999")
    assert "+5521999999999" in variantes
    assert "5521999999999" in variantes
    assert "21999999999" in variantes
    assert "(21) 99999-9999" in variantes


def test_variantes_busca_fixo():
    """Gera variantes para fixo com 12 dígitos."""
    variantes = variantes_busca_telefone("552133333333")
    assert "+552133333333" in variantes
    assert "552133333333" in variantes
    assert "2133333333" in variantes
    assert "(21) 3333-3333" in variantes


def test_variantes_busca_invalido():
    """Telefone inválido retorna lista vazia."""
    assert variantes_busca_telefone("") == []
    assert variantes_busca_telefone(None) == []
    assert variantes_busca_telefone("123") == []
