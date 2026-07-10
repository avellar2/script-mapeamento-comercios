"""
Testes da trava de segurança contra execução em produção.

Roda com:
    python -m pytest tests/test_outreach_safety.py -v
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from outreach_safety import (
    _mask_identifier,
    _is_production_url,
    _check_env_safety,
    check_db_safety,
)


class TestMaskIdentifier:
    def test_maska_identificador_longo(self):
        assert _mask_identifier("abcdefghijklmnop") == "abc***nop"

    def test_maska_identificador_curto(self):
        assert _mask_identifier("abc") == "***"

    def test_maska_vazio(self):
        assert _mask_identifier("") == "<empty>"

    def test_maska_none(self):
        assert _mask_identifier(None) == "<empty>"


class TestIsProductionUrl:
    def test_supabase_producao(self):
        assert _is_production_url("https://xyzxyzxyz.supabase.co") is True

    def test_supabase_producao_ref(self):
        assert _is_production_url("https://aocyueoccollpvfaeifd.supabase.co") is True

    def test_localhost_seguro(self):
        assert _is_production_url("http://localhost:5433") is False

    def test_vazio(self):
        assert _is_production_url("") is False

    def test_none(self):
        assert _is_production_url(None) is False


class TestCheckEnvSafety:
    def test_sem_flag_bloqueia(self):
        """Sem ALLOW_OUTREACH_RPC_TESTS=1, bloqueia."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError, match="ALLOW_OUTREACH_RPC_TESTS"):
                _check_env_safety()

    def test_flag_errada_bloqueia(self):
        """Flag com valor errado bloqueia."""
        with patch.dict(os.environ, {"ALLOW_OUTREACH_RPC_TESTS": "yes"}, clear=True):
            with pytest.raises(EnvironmentError, match="ALLOW_OUTREACH_RPC_TESTS"):
                _check_env_safety()

    def test_flag_correta_supabase_producao_bloqueia(self):
        """Flag correta mas URL de produção bloqueia."""
        env = {
            "ALLOW_OUTREACH_RPC_TESTS": "1",
            "SUPABASE_URL": "https://xyz.supabase.co",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvironmentError, match="produção"):
                _check_env_safety()

    def test_flag_correta_localhost_ok(self):
        """Flag correta com localhost passa."""
        env = {
            "ALLOW_OUTREACH_RPC_TESTS": "1",
            "SUPABASE_URL": "",
        }
        with patch.dict(os.environ, env, clear=True):
            _check_env_safety()  # Não deve levantar exceção

    def test_test_url_producao_bloqueia(self):
        """SUPABASE_TEST_URL apontando para produção bloqueia."""
        env = {
            "ALLOW_OUTREACH_RPC_TESTS": "1",
            "SUPABASE_URL": "",
            "SUPABASE_TEST_URL": "https://xyz.supabase.co",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvironmentError, match="SUPABASE_TEST_URL"):
                _check_env_safety()


class TestCheckDbSafety:
    def test_db_supabase_bloqueia(self):
        """DSN apontando para Supabase bloqueia."""
        with pytest.raises(EnvironmentError, match="Supabase"):
            check_db_safety("host=xyz.supabase.co dbname=postgres")

    def test_db_muitos_leads_bloqueia(self):
        """Banco com muitos leads bloqueia."""
        import psycopg2
        from unittest.mock import MagicMock

        # Mock da conexão para simular muitos leads
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [500]

        with patch("outreach_safety.psycopg2.connect", return_value=mock_conn):
            # Forçar re-import para teste
            from outreach_safety import check_db_safety as cbs
            with pytest.raises(EnvironmentError, match="500 leads"):
                cbs("host=localhost port=5433 dbname=test user=postgres")
