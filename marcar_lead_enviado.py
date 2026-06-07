#!/usr/bin/env python3
"""
Marcar um lead como abordado no Supabase.

Atualiza o status para 'abordado', preenche ultimo_contato_em com agora,
define proximo_followup_em para daqui 7 dias, e cria uma interação.

Uso:
    python marcar_lead_enviado.py --telefone 21999999999
    python marcar_lead_enviado.py --telefone 5521999999999 --mensagem "Oi, vi seu salão no Google..."
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path=None):
        env_path = Path(path) if path else Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

sys.path.insert(0, str(Path(__file__).parent))
from utils.phone_utils import normalizar_telefone_br


def main():
    parser = argparse.ArgumentParser(description="Marcar lead como abordado no Supabase")
    parser.add_argument("--telefone", required=True, help="Telefone do lead (qualquer formato)")
    parser.add_argument("--mensagem", default="", help="Mensagem enviada ao lead")
    args = parser.parse_args()

    if not HAS_SUPABASE:
        print("❌ Pacote 'supabase' não instalado. Instale com: pip install supabase")
        sys.exit(1)

    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL e SUPABASE_ANON_KEY não encontrados no .env")
        sys.exit(1)

    # Normalizar telefone
    tel_norm = normalizar_telefone_br(args.telefone)
    if not tel_norm:
        print(f"❌ Telefone inválido: {args.telefone}")
        print("   Formatos aceitos: 21999999999, (21) 99999-9999, 5521999999999")
        sys.exit(1)

    try:
        sb = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"❌ Erro ao conectar ao Supabase: {e}")
        sys.exit(1)

    # Buscar lead
    result = sb.table("leads").select("id,nome,status,telefone,telefone_normalizado").eq("telefone_normalizado", tel_norm).execute()

    if not result.data:
        print(f"❌ Lead não encontrado com telefone: {tel_norm}")
        print("   Use --telefone com o número completo (com DDD ou código do país).")
        sys.exit(1)

    lead = result.data[0]
    lead_id = lead["id"]
    nome = lead["nome"]
    status_anterior = lead["status"]

    # Status que não devem ser regredidos
    if status_anterior in ("convertido", "perdido"):
        print(f"⚠️  Lead '{nome}' já está com status '{status_anterior}'. Não é possível regredir.")
        print(f"   Telefone: {tel_norm}")
        sys.exit(1)

    # Atualizar lead
    agora = datetime.utcnow().isoformat()
    followup = (datetime.utcnow() + timedelta(days=7)).isoformat()

    update_data = {
        "status": "abordado",
        "ultimo_contato_em": agora,
        "proximo_followup_em": followup,
    }

    sb.table("leads").update(update_data).eq("id", lead_id).execute()

    # Criar interação
    interaction = {
        "lead_id": lead_id,
        "tipo": "primeira_abordagem",
        "canal": "whatsapp",
        "mensagem": args.mensagem or "",
        "observacao": f"Status alterado de '{status_anterior}' para 'abordado'",
    }
    sb.table("lead_interactions").insert(interaction).execute()

    # Resumo
    print("=" * 50)
    print("✅ Lead marcado como enviado!")
    print("=" * 50)
    print(f"  Nome:        {nome}")
    print(f"  Telefone:    {tel_norm}")
    print(f"  Status:      {status_anterior} → abordado")
    print(f"  Contato em:  {agora[:19]}")
    print(f"  Follow-up:   {followup[:19]} (7 dias)")
    if args.mensagem:
        print(f"  Mensagem:    {args.mensagem[:80]}...")
    print("=" * 50)

    return 1


if __name__ == "__main__":
    main()