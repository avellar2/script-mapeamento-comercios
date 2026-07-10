"""
Testes de detecção de conflitos de telefones legados.

Roda com:
    python -m pytest tests/test_dedup_telefones_legados.py -v
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dedup_telefones import detectar_conflitos, gerar_relatorio, _mascarar


def test_sem_conflitos():
    """Leads com telefone_normalizado correto não geram conflitos."""
    leads = [
        {"id": "1", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "5521999999999", "nome": "Lead A", "status": "novo"},
        {"id": "2", "telefone": "31999999999", "whatsapp": "", "telefone_normalizado": "5531999999999", "nome": "Lead B", "status": "novo"},
    ]
    conflitos = detectar_conflitos(leads)
    assert len(conflitos) == 0


def test_dois_leads_mesmo_canonico():
    """Dois leads com mesmo telefone real convergem para o mesmo canônico."""
    leads = [
        {"id": "1", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "5521999999999", "nome": "Lead A", "status": "novo"},
        {"id": "2", "telefone": "(21) 99999-9999", "whatsapp": "", "telefone_normalizado": "5521999999999", "nome": "Lead B", "status": "novo"},
    ]
    conflitos = detectar_conflitos(leads)
    assert len(conflitos) == 1
    assert conflitos[0]["canonical"] == "5521999999999"
    assert conflitos[0]["total_leads"] == 2


def test_telefone_normalizado_divergente():
    """Dois leads com mesmo telefone real mas telefone_normalizado divergente."""
    leads = [
        {"id": "1", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "5521999999999", "nome": "Lead A", "status": "novo"},
        {"id": "2", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "21999999999", "nome": "Lead B", "status": "novo"},
    ]
    conflitos = detectar_conflitos(leads)
    assert len(conflitos) == 1
    assert conflitos[0]["divergentes"] is True


def test_telefone_normalizado_nulo():
    """Lead com telefone_normalizado nulo aparece como conflito."""
    leads = [
        {"id": "1", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": None, "nome": "Lead A", "status": "novo"},
    ]
    conflitos = detectar_conflitos(leads)
    assert len(conflitos) == 1
    assert conflitos[0]["algum_nulo"] is True


def test_mascarar():
    """Mascara telefone corretamente."""
    assert _mascarar("5521999999999") == "5521****9999"
    assert _mascarar("21999999999") == "2199****9999"
    assert _mascarar("") == ""
    assert _mascarar(None) == ""


def test_gerar_relatorio():
    """Gera relatório CSV sem erros."""
    conflitos = [
        {
            "canonical": "5521999999999",
            "total_leads": 2,
            "divergentes": True,
            "algum_nulo": False,
            "leads": [
                {"id": "1", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "5521999999999", "nome": "Lead A", "status": "novo"},
                {"id": "2", "telefone": "21999999999", "whatsapp": "", "telefone_normalizado": "21999999999", "nome": "Lead B", "status": "novo"},
            ],
        }
    ]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8") as f:
        caminho = f.name

    try:
        gerar_relatorio(conflitos, caminho, mascarar=True)
        conteudo = Path(caminho).read_text(encoding="utf-8")
        assert "5521****9999" in conteudo
        assert "SIM" in conteudo
    finally:
        Path(caminho).unlink(missing_ok=True)
