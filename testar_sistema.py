#!/usr/bin/env python3
"""
Teste rápido do sistema de email + Supabase
"""
import os
import sys
from pathlib import Path

# Adiciona diretorio ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_env():
    """Testa variaveis de ambiente."""
    print("1. Testando variaveis de ambiente (.env)...")
    from dotenv import load_dotenv
    load_dotenv()

    checks = [
        ("ZOHO_SMTP_HOST", os.getenv("ZOHO_SMTP_HOST")),
        ("ZOHO_SMTP_USER", os.getenv("ZOHO_SMTP_USER")),
        ("ZOHO_SMTP_APP_PASSWORD", os.getenv("ZOHO_SMTP_APP_PASSWORD")),
        ("SUPABASE_URL", os.getenv("SUPABASE_URL")),
        ("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY")),
    ]

    for name, value in checks:
        if value:
            print(f"  ✓ {name}: {'*' * (len(value) - 2) + value[:2]}")
        else:
            print(f"  ✗ {name}: NAO DEFINIDO")
    print()

def test_supabase():
    """Testa conexao com Supabase."""
    print("2. Testando conexao Supabase...")
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            print("  ✗ SUPABASE_URL ou SUPABASE_ANON_KEY nao definidos")
            return

        client = create_client(url, key)

        # Testa listar tabelas
        result = client.table("emails_enviados").select("*").limit(1).execute()
        print(f"  ✓ Conexao OK")
        print(f"  ✓ Tabela emails_enviados acessivel")
        print()
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        print()

def test_templates():
    """Testa templates de email."""
    print("3. Testando templates...")
    templates_dir = Path(__file__).parent / "templates"
    templates = list(templates_dir.glob("*.html"))

    print(f"  ✓ {len(templates)} templates encontrados")

    # Verifica tracking pixel
    for tmpl in templates[:3]:  # Primeiros 3
        content = tmpl.read_text(encoding="utf-8")
        if "track?id=" in content:
            print(f"  ✓ {tmpl.name}: tracking pixel presente")
        else:
            print(f"  ✗ {tmpl.name}: tracking pixel AUSENTE")
    print()

def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("  TESTE DO SISTEMA - Email + Supabase")
    print("=" * 60)
    print()

    test_env()
    test_supabase()
    test_templates()

    print("=" * 60)
    print("  Teste concluido!")
    print("=" * 60)

if __name__ == "__main__":
    main()
