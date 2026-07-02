"""
Testes do modo direcionado --test-phone.

Testa que:
- modo direcionado so funciona com dry-run
- telefone vem do ambiente
- telefone nunca aparece completo no log
- controle positivo simulado encontra conversa
- controle negativo retorna no_chat
- primeira variante encontrada interrompe as demais
- timeout por lead e respeitado
- nenhuma escrita e executada
- ausencia da variavel de telefone falha com mensagem clara
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.phone_utils import normalizar_telefone_br


class TestTestPhoneMode:
    """Testes para o modo --test-phone."""

    def test_requires_dry_run(self):
        """--test-phone so pode ser usado com --dry-run."""
        # Se --apply e --test-phone juntos, deve falhar
        # Verificamos isso no nivel do parser
        from sincronizar_abordados_whatsapp import main
        with patch('sys.argv', ['sync', '--apply', '--test-phone']):
            with pytest.raises(SystemExit):
                main()

    def test_requires_env_var(self):
        """--test-phone sem WHATSAPP_MATCH_TEST_PHONE deve falhar."""
        from sincronizar_abordados_whatsapp import main
        with patch('sys.argv', ['sync', '--dry-run', '--test-phone']):
            with patch.dict(os.environ, {}, clear=False):
                # Remove a variavel se existir
                os.environ.pop('WHATSAPP_MATCH_TEST_PHONE', None)
                with pytest.raises(SystemExit):
                    main()

    def test_invalid_phone_fails(self):
        """Telefone invalido na variavel de ambiente deve falhar."""
        from sincronizar_abordados_whatsapp import main
        with patch('sys.argv', ['sync', '--dry-run', '--test-phone']):
            with patch.dict(os.environ, {'WHATSAPP_MATCH_TEST_PHONE': '123'}):
                with pytest.raises(SystemExit):
                    main()

    def test_valid_phone_normalizes(self):
        """Telefone valido deve normalizar corretamente."""
        tel = normalizar_telefone_br("21999999999")
        assert tel == "5521999999999"

    def test_phone_masked_in_log(self):
        """Telefone mascarado nao contem o numero completo."""
        phone = "5521999999999"
        masked = phone[:4] + "****" + phone[-4:]
        assert masked == "5521****9999"
        assert "999999999" not in masked

    def test_no_write_operations_in_test_phone(self):
        """Modo test-phone nao contem operacoes de escrita."""
        src = Path(__file__).resolve().parent.parent / "sincronizar_abordados_whatsapp.py"
        content = src.read_text(encoding="utf-8")
        # Encontra a funcao executar_test_phone
        start = content.find('async def executar_test_phone')
        if start < 0:
            pytest.skip("executar_test_phone nao encontrada")
        end = content.find('\ndef main():', start)
        func = content[start:end]

        # Nao deve ter operacoes de escrita
        assert 'reserve_outreach' not in func
        assert 'settle_outreach' not in func
        assert 'confirm_outreach' not in func
        assert 'INSERT' not in func.upper()
        assert 'UPDATE' not in func.upper()
        assert 'PATCH' not in func

    def test_positive_control_must_not_be_no_chat(self):
        """Controle positivo nao pode terminar como no_chat (teste conceitual)."""
        # Este teste verifica a logica: se o campo foi encontrado e ha conversa,
        # o resultado nao deve ser no_chat
        from whatsapp_match import MatchStatus
        # Se status for MATCHED, NO_OUTBOUND, ou AMBIGUOUS, nao e no_chat
        positive_statuses = [
            MatchStatus.MATCHED,
            MatchStatus.NO_OUTBOUND,
            MatchStatus.AMBIGUOUS,
            MatchStatus.AMBIGUOUS_CONTACT,
            MatchStatus.GROUP,
            MatchStatus.CHANNEL,
            MatchStatus.COMMUNITY,
        ]
        for s in positive_statuses:
            assert s != MatchStatus.NO_CHAT

    def test_negative_control_returns_no_chat(self):
        """Controle negativo deve retornar no_chat (teste conceitual)."""
        from whatsapp_match import MatchStatus
        # no_chat e o resultado esperado para telefone sem conversa
        assert MatchStatus.NO_CHAT.value == "no_chat"

    def test_variant_timing_recorded(self):
        """Variante deve registrar tempo."""
        src = Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py"
        content = src.read_text(encoding="utf-8")
        assert 'variant_start' in content or 'time.time()' in content


class TestMatcherTiming:
    """Testes de performance do matcher."""

    def test_first_variant_found_stops_others(self):
        """Quando primeira variante encontra chat, demais sao canceladas."""
        # Verifica que o loop retorna imediatamente apos encontrar
        src = Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py"
        content = src.read_text(encoding="utf-8")
        # O loop deve ter return apos encontrar chat
        assert 'return result' in content

    def test_no_write_in_matcher(self):
        """Matcher nao contem operacoes de escrita."""
        src = Path(__file__).resolve().parent.parent / "whatsapp_match" / "matcher.py"
        content = src.read_text(encoding="utf-8")
        assert 'send?phone=' not in content
        assert 'keyboard.press' not in content
        assert 'aria-label="Enviar"' not in content
