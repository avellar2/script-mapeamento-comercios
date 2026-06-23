#!/usr/bin/env python3
"""Marcar leads como abordados/perdidos no Supabase"""
import os, json, urllib.request, ssl
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote

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
followup = (datetime.now() + timedelta(days=3)).isoformat()

# Leads enviados (1-11, excluindo os sem WhatsApp)
enviados = [
    "JCAR AUTO MECANICA E GNV",
    "Oficina Mecânica Duro Na Queda",
    "Auto Mecânica Brinquinho",
    "Kurupa car mecânica em geral",
    "Serralheria só a graça fabricação e manutenção",
    "Serralheria Valdir Santana",
    "Serralheria",
    "Edmilson Só Elétrica Peças Automotivas a casa do eletricista",
]

# Leads que NÃO estão no WhatsApp
sem_wpp = [
    "Oficina Do Trippa",
    "Heplon Serralheria",
    "Serralheria Central de Nilópolis",
]

def find_lead(nome):
    """Find lead by name using ilike"""
    nome_encoded = quote(nome)
    req = urllib.request.Request(
        f"{api_url}?nome=ilike.*{nome_encoded}*&select=id,nome",
        headers={**headers, "Prefer": "return=representation"}
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read().decode())
        return data[0] if data else None

def patch_lead(lead_id, body):
    """Update lead status"""
    req = urllib.request.Request(
        f"{api_url}?id=eq.{lead_id}",
        data=json.dumps(body).encode(),
        headers=headers,
        method="PATCH"
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        return r.status

# Marcar enviados como abordado
for nome in enviados:
    lead = find_lead(nome)
    if lead:
        patch_lead(lead["id"], {
            "status": "abordado",
            "ultimo_contato_em": now,
            "proximo_followup_em": followup
        })
        print(f"✅ {lead['nome']} → abordado")
    else:
        print(f"⚠️ {nome} não encontrado")

# Marcar sem WhatsApp como perdido
for nome in sem_wpp:
    lead = find_lead(nome)
    if lead:
        patch_lead(lead["id"], {
            "status": "perdido",
            "observacoes": "Sem WhatsApp (telefone fixo ou não localizado)",
            "ultimo_contato_em": now
        })
        print(f"❌ {lead['nome']} → perdido (sem WhatsApp)")
    else:
        print(f"⚠️ {nome} não encontrado")
