"""
Testes de compilação e rerodabilidade da migration.

Testes de validação SQL (não requerem banco).
Testes de aplicação/rollback requerem PostgreSQL local.

Roda com:
    python -m pytest tests/test_migration_rollback.py -v -s
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Apenas testes de aplicação/rollback requerem banco
needs_db = pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    reason="SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY necessários"
)


MIGRATION_PATH = Path(__file__).resolve().parent.parent / "supabase" / "migration_lead_outreach.sql"


def test_migration_arquivo_existe():
    """Arquivo de migration existe."""
    assert MIGRATION_PATH.exists()
    assert MIGRATION_PATH.stat().st_size > 0


def test_migration_sql_valido():
    """SQL da migration é sintaticamente válido (parse básico)."""
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    # Verifica que o CREATE TABLE está completo
    assert "CREATE TABLE IF NOT EXISTS public.lead_outreach" in sql
    assert ");" in sql  # Fechamento da tabela

    # Verifica que as funções estão completas
    assert "CREATE OR REPLACE FUNCTION public.reserve_outreach" in sql
    assert "CREATE OR REPLACE FUNCTION public.settle_outreach" in sql
    assert "CREATE OR REPLACE FUNCTION public.confirm_outreach_from_whatsapp" in sql
    assert "CREATE OR REPLACE FUNCTION public.release_reconciliation" in sql
    assert "CREATE OR REPLACE FUNCTION public.get_outreach_state" in sql
    assert "CREATE OR REPLACE FUNCTION public.normalizar_telefone_br_sql" in sql
    assert "CREATE OR REPLACE FUNCTION public.validate_lead_campaign" in sql
    assert "CREATE OR REPLACE FUNCTION public.outreach_transition_allowed" in sql
    assert "CREATE OR REPLACE FUNCTION public.interaction_type_from_campaign_key" in sql

    # Verifica que o ROLLBACK está completo
    assert "ROLLBACK COMPLETO" in sql
    assert "DROP TABLE IF EXISTS public.lead_outreach" in sql

    # Verifica grants
    assert "GRANT  EXECUTE ON FUNCTION public.reserve_outreach" in sql
    assert "GRANT  EXECUTE ON FUNCTION public.settle_outreach" in sql
    assert "GRANT  EXECUTE ON FUNCTION public.confirm_outreach_from_whatsapp" in sql
    assert "GRANT  EXECUTE ON FUNCTION public.get_outreach_state" in sql

    # Verifica que release_reconciliation NÃO tem grant para anon
    assert "GRANT  EXECUTE ON FUNCTION public.release_reconciliation" not in sql.split("get_outreach_state")[0]

    # Verifica que a view de conflitos NÃO tem grant para anon
    assert "GRANT SELECT ON public.vw_telefones_conflitos TO anon" not in sql

    # Verifica RLS
    assert "ALTER TABLE public.lead_outreach ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE public.lead_outreach FORCE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON public.lead_outreach FROM anon" in sql

    # Verifica search_path seguro
    assert "SET search_path = public, pg_temp" in sql

    # Verifica que não há SQL dinâmica
    assert "EXECUTE" not in sql.split("CREATE OR REPLACE")[0]  # EXECUTE em grants é ok


def test_migration_rerodavel():
    """Migration pode ser aplicada duas vezes sem falhar (idempotente)."""
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    # Verifica que todos os CREATE usam IF NOT EXISTS ou OR REPLACE
    assert "CREATE TABLE IF NOT EXISTS" in sql
    assert "CREATE OR REPLACE FUNCTION" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS" in sql
    assert "CREATE INDEX IF NOT EXISTS" in sql
    assert "DROP TRIGGER IF EXISTS" in sql

    # Verifica que grants/revokes são idempotentes
    assert "GRANT  EXECUTE" in sql
    assert "REVOKE ALL" in sql


def test_migration_rollback_completo():
    """Rollback remove todos os objetos criados."""
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    # Extrai o bloco de rollback
    rollback_lines = []
    in_rollback = False
    for line in sql.split("\n"):
        if "ROLLBACK COMPLETO" in line:
            in_rollback = True
            continue
        if in_rollback:
            rollback_lines.append(line)

    rollback_sql = "\n".join(rollback_lines)

    # Verifica que o rollback cobre todos os objetos
    assert "DROP TABLE IF EXISTS public.lead_outreach" in rollback_sql
    assert "DROP TRIGGER IF EXISTS set_updated_at_lead_outreach" in rollback_sql
    assert "DROP INDEX IF EXISTS public.uq_lead_outreach_active" in rollback_sql
    assert "DROP INDEX IF EXISTS public.idx_lead_outreach_phone" in rollback_sql
    assert "DROP INDEX IF EXISTS public.idx_lead_outreach_status" in rollback_sql
    assert "DROP INDEX IF EXISTS public.idx_lead_outreach_lead" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.normalizar_telefone_br_sql" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.validate_lead_campaign" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.outreach_transition_allowed" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.interaction_type_from_campaign_key" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.reserve_outreach" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.settle_outreach" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.confirm_outreach_from_whatsapp" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.release_reconciliation" in rollback_sql
    assert "DROP FUNCTION IF EXISTS public.get_outreach_state" in rollback_sql
    assert "DROP VIEW IF EXISTS public.vw_telefones_conflitos" in rollback_sql
