"""
Trava de segurança contra execução acidental em produção.

Bloqueia testes de outreach se:
- ALLOW_OUTREACH_RPC_TESTS não está definido como '1'
- URL de Supabase de produção é detectada
- Banco de dados contém identificador de produção
- Ambiente contém leads reais

Nenhuma chave, senha ou connection string é exposta em logs.
"""

import os
import re
import sys

import psycopg2

# URLs de produção conhecidas (apenas o host mascarado em logs)
_PRODUCTION_PATTERNS = [
    "supabase.co",
    "aocyueoccollpvfaeifd",  # project ref mascarado
]

# Tabelas/colunas que indicam produção
_PRODUCTION_INDICATORS = {
    "leads_count_threshold": 100,  # Mais de 100 leads provavelmente é produção
}


def _mask_identifier(identifier: str) -> str:
    """Mascara identificador para logs seguros."""
    if not identifier:
        return "<empty>"
    if len(identifier) <= 6:
        return "***"
    return identifier[:3] + "***" + identifier[-3:]


def _is_production_url(url: str) -> bool:
    """Verifica se URL aponta para produção."""
    if not url:
        return False
    url_lower = url.lower()
    for pattern in _PRODUCTION_PATTERNS:
        if pattern in url_lower:
            return True
    return False


def _check_env_safety():
    """Verifica variáveis de ambiente contra produção."""
    # 1. Flag explícita obrigatória
    allow = os.environ.get("ALLOW_OUTREACH_RPC_TESTS", "")
    if allow != "1":
        raise EnvironmentError(
            "ALLOW_OUTREACH_RPC_TESTS=1 não definido. "
            "Testes de outreach RPC bloqueados por segurança."
        )

    # 2. URL de produção
    supabase_url = os.environ.get("SUPABASE_URL", "")
    if _is_production_url(supabase_url):
        host = supabase_url.split("//")[-1].split("/")[0] if "//" in supabase_url else supabase_url
        raise EnvironmentError(
            f"SUPABASE_URL aponta para produção (host: {_mask_identifier(host)}). "
            "Testes bloqueados. Use SUPABASE_TEST_URL ou TEST_DATABASE_URL."
        )

    # 3. Verificar SUPABASE_TEST_URL se existir
    test_url = os.environ.get("SUPABASE_TEST_URL", "")
    if test_url and _is_production_url(test_url):
        raise EnvironmentError(
            "SUPABASE_TEST_URL aponta para produção. Testes bloqueados."
        )


def check_db_safety(dsn: str = None):
    """
    Verifica se o banco de dados é seguro para testes.

    Args:
        dsn: Connection string. Se None, usa TEST_DATABASE_URL ou default local.

    Raises:
        EnvironmentError: Se banco parece ser de produção.
    """
    if dsn is None:
        dsn = os.environ.get("TEST_DATABASE_URL",
                            "host=localhost port=5433 dbname=avgestao_outreach_test user=postgres")

    # Verificar se é banco local
    if "supabase.co" in dsn.lower():
        host = dsn.split("//")[-1].split("/")[0] if "//" in dsn else "unknown"
        raise EnvironmentError(
            f"DSN aponta para Supabase (host: {_mask_identifier(host)}). "
            "Use banco local ou explicitamente marcado como teste."
        )

    try:
        conn = psycopg2.connect(dsn)
        try:
            cur = conn.cursor()

            # Verificar se banco contém leads reais (muitos registros)
            cur.execute("SELECT COUNT(*) FROM public.leads")
            count = cur.fetchone()[0]
            if count > _PRODUCTION_INDICATORS["leads_count_threshold"]:
                raise EnvironmentError(
                    f"Banco contém {count} leads (limite: {_PRODUCTION_INDICATORS['leads_count_threshold']}). "
                    "Possível banco de produção. Testes bloqueados."
                )

            # Verificar se há leads com status 'abordado' (indica produção)
            cur.execute("SELECT COUNT(*) FROM public.leads WHERE status = 'abordado'")
            abordados = cur.fetchone()[0]
            if abordados > 10:
                raise EnvironmentError(
                    f"Banco contém {abordados} leads abordados. "
                    "Possível banco de produção. Testes bloqueados."
                )
        finally:
            conn.close()
    except psycopg2.OperationalError as e:
        # Se não conseguir conectar, não é erro de segurança
        pass


def assert_safe_environment():
    """
    Verifica completa de segurança. Chamada no início dos testes.

    Raises:
        EnvironmentError: Se ambiente não é seguro.
    """
    _check_env_safety()

    # Verificar banco se usando PostgreSQL local
    db_url = os.environ.get("TEST_DATABASE_URL", "")
    if db_url or not os.environ.get("SUPABASE_URL"):
        check_db_safety(db_url or None)


# Auto-verificação quando importado por testes de outreach (não pelo próprio teste de safety)
if "pytest" in sys.modules:
    # Não auto-verificar se estamos rodando os testes da própria safety
    _is_safety_test = any("test_outreach_safety" in str(m) for m in sys.modules.values())
    if not _is_safety_test:
        try:
            assert_safe_environment()
        except EnvironmentError as e:
            import pytest
            pytest.skip(str(e), allow_module_level=True)
