#!/usr/bin/env python3
"""
Marcar um lead como abordado no Supabase (via lead_outreach).

Usa reserve_outreach + settle_outreach em vez de PATCH direto em leads.

Uso:
    python marcar_lead_enviado.py --telefone 21999999999
    python marcar_lead_enviado.py --telefone 5521999999999 --mensagem "Oi, vi seu salão no Google..."
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sender_int import (
    normalizar_telefone_lead,
    obter_campaign_key,
    marcar_lead_direto,
    get_supabase_client,
)
from utils.phone_utils import normalizar_telefone_br


def main():
    parser = argparse.ArgumentParser(description="Marcar lead como abordado no Supabase")
    parser.add_argument("--telefone", required=True, help="Telefone do lead (qualquer formato)")
    parser.add_argument("--mensagem", default="", help="Mensagem enviada ao lead")
    args = parser.parse_args()

    # Normalizar telefone
    tel_norm = normalizar_telefone_br(args.telefone)
    if not tel_norm:
        print(f"❌ Telefone inválido: {args.telefone}")
        print("   Formatos aceitos: 21999999999, (21) 99999-9999, 5521999999999")
        sys.exit(1)

    # Buscar lead pelo telefone normalizado
    client = get_supabase_client("anon")
    if not client:
        sys.exit(1)

    result = client.table("leads").select("id,nome,status,telefone,telefone_normalizado,produto,grupo").eq("telefone_normalizado", tel_norm).execute()

    if not result.data:
        print(f"❌ Lead não encontrado com telefone: {tel_norm}")
        sys.exit(1)

    lead = result.data[0]
    lead_id = lead["id"]
    nome = lead["nome"]
    status_anterior = lead["status"]

    # Status que não devem ser regredidos
    if status_anterior in ("convertido", "perdido"):
        print(f"⚠️  Lead '{nome}' já está com status '{status_anterior}'. Não é possível regredir.")
        sys.exit(1)

    # Marca via lead_outreach (reserve + settle)
    campaign_key = obter_campaign_key(lead)
    agora = datetime.now(timezone.utc).isoformat()

    result = marcar_lead_direto(
        lead_id,
        tel_norm,
        campaign_key,
        "abordado",
        agora,
    )

    if not result:
        print("❌ Erro ao conectar ao Supabase (service role necessária)")
        sys.exit(1)

    outcome = result.get("outcome", "erro")

    if outcome in ("settled", "already_sent", "already_confirmed"):
        print("=" * 50)
        print(f"{'✅' if outcome == 'settled' else '⚠️'} Lead marcado como enviado!")
        print("=" * 50)
        print(f"  Nome:        {nome}")
        print(f"  Telefone:    {tel_norm}")
        print(f"  Status:      {status_anterior} → abordado")
        print(f"  Outcome:     {outcome}")
        print("=" * 50)
        return 0
    else:
        print(f"❌ Falha ao marcar lead: {outcome}")
        print(f"   Detalhes: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()