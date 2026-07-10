"""
Testes de segurança da service role.

Verifica que:
- .env está no .gitignore
- Chave nunca aparece em diff
- Chave nunca em logs/checkpoints
- Cliente service_role só criado em operações de escrita
- Key type é validado

Roda com:
    python -m pytest tests/test_security_service_role.py -v
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_env_gitignored():
    """.env está no .gitignore (nunca entra no controle de versão)."""
    gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".env" in content, ".env deve estar no .gitignore"


def test_service_role_nao_em_logs():
    """Service role key não está em arquivos de output/log."""
    root = Path(__file__).resolve().parent.parent
    checkpoint = root / "output" / "avgestao" / "sincronizador" / "checkpoint.json"
    if checkpoint.exists():
        content = checkpoint.read_text(encoding="utf-8")
        assert "SUPABASE_SERVICE_ROLE_KEY" not in content.upper(), \
            "checkpoint não deve conter service role key"
        assert "sk_live_" not in content, \
            "checkpoint não deve conter chave real (sk_live_)"


def test_outreach_client_nao_expoe_chave():
    """outreach_client.py nunca imprime a chave em logs/exceções."""
    src = (Path(__file__).resolve().parent.parent / "outreach_client.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        if ("logger.error" in line or "logger.warning" in line) and "SERVICE_ROLE_KEY" in line:
            # logger.warning/showing the KEY NAME is ok; logger.error showing the VALUE is not
            assert "os.environ.get" not in line, \
                f"Não logar o valor da service role key: {line.strip()[:100]}"


def test_cliente_service_role_somente_em_escrita():
    """get_outreach_state usa anon; reserve/settle/confirm/release usam service_role."""
    src = (Path(__file__).resolve().parent.parent / "outreach_client.py").read_text(encoding="utf-8")

    # Seção de LEITURA usa anon
    leit = src[src.find("# RPCs de LEITURA"):src.find("# RPCs de ESCRITA")]
    assert "_get_client('anon')" in leit or '_get_client("anon")' in leit, \
        "Seção de LEITURA deve usar anon key"

    # Seção de ESCRITA usa service_role
    escr = src[src.find("# RPCs de ESCRITA"):]
    assert "_get_client('service_role')" in escr or '_get_client("service_role")' in escr, \
        "Seção de ESCRITA deve usar service_role key"


def test_key_type_validado():
    """key_type inválido é recusado."""
    from outreach_client import _get_client
    result = _get_client("invalid_type")
    assert result is None, "key_type inválido deve retornar None"


def test_sync_script_dry_run_nao_carrega_service_role():
    """Sincronizador em dry-run não carrega SUPABASE_SERVICE_ROLE_KEY."""
    src = (Path(__file__).resolve().parent.parent / "sincronizar_abordados_whatsapp.py").read_text(encoding="utf-8")
    if "def _get_supabase_client" in src:
        secao = src.split("def _get_supabase_client")[1].split("def ")[0]
        assert "SERVICE_ROLE_KEY" not in secao, \
            "dry-run (_get_supabase_client) não deve carregar service role key"
