#!/usr/bin/env python3
"""Testes da saudacao flexivel por horario (Objetivo 3).

Regra:
  05:00 ate 11:59 -> Bom dia
  12:00 ate 17:59 -> Boa tarde
  18:00 ate 04:59 -> Boa noite
"""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import campanha_whatsapp as cw

FUSO = cw.FUSO


def _dt(hh, mm=0):
    return datetime(2026, 7, 8, hh, mm, 0, tzinfo=FUSO)


class TestGerarSaudacao:
    def test_manha_09h(self):
        assert cw.gerar_saudacao(_dt(9, 0)) == "Bom dia"

    def test_tarde_14h(self):
        assert cw.gerar_saudacao(_dt(14, 0)) == "Boa tarde"

    def test_noite_20h(self):
        assert cw.gerar_saudacao(_dt(20, 0)) == "Boa noite"

    def test_limites_manha(self):
        assert cw.gerar_saudacao(_dt(5, 0)) == "Bom dia"
        assert cw.gerar_saudacao(_dt(11, 59)) == "Bom dia"

    def test_limites_tarde(self):
        assert cw.gerar_saudacao(_dt(12, 0)) == "Boa tarde"
        assert cw.gerar_saudacao(_dt(17, 59)) == "Boa tarde"

    def test_limites_noite(self):
        assert cw.gerar_saudacao(_dt(18, 0)) == "Boa noite"
        assert cw.gerar_saudacao(_dt(23, 59)) == "Boa noite"
        assert cw.gerar_saudacao(_dt(0, 0)) == "Boa noite"
        assert cw.gerar_saudacao(_dt(4, 59)) == "Boa noite"

    def test_default_usa_fuso_atual(self):
        """Sem arg, usa datetime.now(FUSO) e retorna uma das tres."""
        assert cw.gerar_saudacao() in ("Bom dia", "Boa tarde", "Boa noite")


class TestRenderComSaudacao:
    def test_template_com_saudacao_renderiza(self):
        """(9) Template com {saudacao} renderiza a saudacao por horario."""
        args = cw.build_parser().parse_args(["plan"])
        camp = cw.CampanhaWhatsApp(args)
        camp._template_text = "{saudacao}, pessoal da {empresa}! Tudo bem?"
        with patch.object(cw, "gerar_saudacao", return_value="Boa noite"):
            msg = camp._renderizar_mensagem({"nome": "Smart Fix"})
        assert msg == "Boa noite, pessoal da Smart Fix! Tudo bem?"

    def test_template_sem_saudacao_continua_funcionando(self):
        """(10) Template sem {saudacao} continua funcionando (compat)."""
        args = cw.build_parser().parse_args(["plan"])
        camp = cw.CampanhaWhatsApp(args)
        camp._template_text = "Oi {nome}! Bem-vindo."
        msg = camp._renderizar_mensagem({"nome": "Empresa X"})
        assert msg == "Oi Empresa X! Bem-vindo."

    def test_saudacao_e_variavel_valida(self):
        """{saudacao} nao e mais bloqueada como variavel desconhecida."""
        args = cw.build_parser().parse_args(["plan"])
        camp = cw.CampanhaWhatsApp(args)
        camp._template_text = "{saudacao}, {empresa}!"
        # Nao deve sair (SystemExit) por variavel desconhecida.
        msg = camp._renderizar_mensagem({"nome": "Loja"})
        assert msg.startswith(("Bom dia", "Boa tarde", "Boa noite"))

    def test_template_oficial_usa_placeholder_saudacao(self):
        """O template oficial avgestao usa {saudacao} (nao hardcoded Boa tarde)."""
        tpl = Path(_root) / "templates" / "avgestao_assistencias_primeiro_contato.txt"
        content = tpl.read_text(encoding="utf-8")
        assert content.startswith("{saudacao}, pessoal da {empresa}! Tudo bem?")
        assert "Boa tarde," not in content.splitlines()[0]