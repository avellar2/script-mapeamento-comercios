#!/usr/bin/env python3
"""Marcar leads como abordados/perdidos no Supabase (via lead_outreach)."""
import os, json, urllib.request, ssl, sys
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from sender_int import (
    normalizar_telefone_lead,
    obter_campaign_key,
    marcar_lead_direto,
    get_supabase_client,
)

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
api_url = f"{url}/rest/v1/leads"
ctx = ssl.create_default_context()
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

now = datetime.now().isoformat()

# Leads enviados (com telefone, NÃO por nome)
# Cada lead: {"nome": "...", "telefone": "..."}
enviados = [
    {"nome": "JCAR AUTO MECANICA E GNV", "telefone": ""},
    {"nome": "Oficina Mecânica Duro Na Queda", "telefone": ""},
    {"nome": "Auto Mecânica Brinquinho", "telefone": ""},
    {"nome": "Kurupa car mecânica em geral", "telefone": ""},
    {"nome": "Serralheria só a graça fabricação e manutenção", "telefone": ""},
    {"nome": "Serralheria Valdir Santana", "telefone": ""},
    {"nome": "Serralheria", "telefone": ""},
    {"nome": "Edmilson Só Elétrica Peças Automotivas a casa do eletricista", "telefone": ""},
]

# Leads que NÃO estão no WhatsApp
sem_wpp = [
    {"nome": "Oficina Do Trippa", "telefone": ""},
    {"nome": "Heplon Serralheria", "telefone": ""},
    {"nome": "Serralheria Central de Nilópolis", "telefone": ""},
]

def buscar_lead_por_telefone(telefone: str):
    """Busca lead por telefone_normalizado."""
    if not telefone:
        return None
    from utils.phone_utils import normalizar_telefone_br
    tel_norm = normalizar_telefone_br(telefone)
    if not tel_norm:
        return None
    req = urllib.request.Request(
        f"{api_url}?telefone_normalizado=eq.{tel_norm}&select=id,nome,telefone_normalizado,produto,grupo",
        headers={**headers, "Prefer": "return=representation"}
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read().decode())
        return data[0] if data else None

def buscar_lead_por_nome(nome: str):
    """Fallback: busca lead por nome (quando não há telefone)."""
    nome_encoded = quote(nome)
    req = urllib.request.Request(
        f"{api_url}?nome=ilike.*{nome_encoded}*&select=id,nome,telefone,telefone_normalizado,produto,grupo",
        headers={**headers, "Prefer": "return=representation"}
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read().decode())
        return data[0] if data else None

# Marcar enviados como abordado (via lead_outreach)
for item in enviados:
    lead = None
    if item["telefone"]:
        lead = buscar_lead_por_telefone(item["telefone"])
    if not lead:
        lead = buscar_lead_por_nome(item["nome"])
    if lead:
        campaign_key = obter_campaign_key(lead)
        result = marcar_lead_direto(
            lead["id"],
            lead.get("telefone_normalizado", ""),
            campaign_key,
            "abordado",
            now,
        )
        outcome = result.get("outcome", "erro") if result else "erro"
        print(f"{'✅' if outcome in ('settled','already_sent','already_confirmed') else '⚠️'} {lead['nome']} → {outcome}")
    else:
        print(f"⚠️ {item['nome']} não encontrado")

# Marcar sem WhatsApp como perdido
for item in sem_wpp:
    lead = None
    if item["telefone"]:
        lead = buscar_lead_por_telefone(item["telefone"])
    if not lead:
        lead = buscar_lead_por_nome(item["nome"])
    if lead:
        # Perdido: marca direto no lead (sem lead_outreach, pois não houve tentativa de envio)
        body = json.dumps({
            "status": "perdido",
            "observacoes": "Sem WhatsApp (telefone fixo ou não localizado)",
            "ultimo_contato_em": now
        }).encode()
        req = urllib.request.Request(
            f"{api_url}?id=eq.{lead['id']}",
            data=body, headers=headers, method="PATCH"
        )
        with urllib.request.urlopen(req, context=ctx) as r:
            pass
        print(f"❌ {lead['nome']} → perdido (sem WhatsApp)")
    else:
        print(f"⚠️ {item['nome']} não encontrado")
