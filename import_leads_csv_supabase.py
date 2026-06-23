#!/usr/bin/env python3
"""
Importar leads do CSV para Supabase via REST API direta.
Mais rápido e com melhor controle de timeout.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import ssl

# Carregar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

CSV_PATH = Path(__file__).parent / "output" / "playwright" / "leads_sem_site.csv"
BATCH_SIZE = 100

def normalizar_telefone(tel):
    if not tel:
        return ""
    numeros = "".join(c for c in str(tel) if c.isdigit())
    if numeros.startswith("55") and len(numeros) > 11:
        numeros = numeros[2:]
    if len(numeros) in (10, 11):
        return f"+55{numeros}"
    return ""

def calcular_score(nicho):
    nicho_lower = nicho.lower() if nicho else ""
    if any(x in nicho_lower for x in ["salão", "salao", "barbearia", "estetica", "estética", "beleza", "cabelo"]):
        return 80
    elif any(x in nicho_lower for x in ["restaurante", "pizzaria", "lanchonete", "comida", "bar"]):
        return 70
    elif any(x in nicho_lower for x in ["clínica", "clinica", "consultório", "consultorio", "médico", "medico", "dentista"]):
        return 75
    elif any(x in nicho_lower for x in ["academia", "pilates", "personal", "crossfit"]):
        return 75
    elif any(x in nicho_lower for x in ["advogado", "advocacia", "escritório", "escritorio"]):
        return 65
    return 50

def supabase_request(url, key, method="GET", data=None):
    """Faz requisição direta ao Supabase REST API"""
    ctx = ssl.create_default_context()
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL ou SUPABASE_ANON_KEY não configurados")
        sys.exit(1)

    api_url = f"{url}/rest/v1/leads"

    # --- PASSO 1: Carregar telefones existentes ---
    print("🔍 Carregando telefones existentes do Supabase...")
    telefones_existentes = set()
    page = 0
    
    while True:
        range_start = page * 1000
        range_end = (page + 1) * 1000 - 1
        select_url = f"{api_url}?select=telefone_normalizado&limit=1000&offset={range_start}"
        
        status, body = supabase_request(select_url, key)
        if status != 200:
            print(f"   ⚠️ Erro ao carregar página {page}: {status}")
            break
        
        data = json.loads(body)
        if not data:
            break
        
        for r in data:
            if r.get("telefone_normalizado"):
                telefones_existentes.add(r["telefone_normalizado"])
        
        page += 1
        if len(data) < 1000:
            break

    print(f"   {len(telefones_existentes)} telefones únicos no Supabase")

    # --- PASSO 2: Ler CSV e preparar leads ---
    print("📖 Lendo CSV...")
    leads_novos = []
    total_com_contato = 0
    sem_contato = 0
    ja_existem = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            telefone = normalizar_telefone(row.get("telefone", ""))
            whatsapp = normalizar_telefone(row.get("whatsapp", ""))
            
            if not telefone and not whatsapp:
                sem_contato += 1
                continue
            
            total_com_contato += 1
            tel_check = telefone or whatsapp
            if tel_check in telefones_existentes:
                ja_existem += 1
                continue
            
            nicho = row.get("nicho", "").strip()
            score = calcular_score(nicho)
            
            lead = {
                "nome": row.get("nome", "").strip() or "Sem nome",
                "nicho": nicho,
                "cidade": row.get("cidade", "").strip(),
                "bairro": row.get("bairro", "").strip(),
                "telefone": telefone,
                "whatsapp": whatsapp,
                "telefone_normalizado": tel_check,
                "instagram": row.get("instagram", "").strip(),
                "endereco": row.get("endereco", "").strip(),
                "tem_site": False,
                "origem": "baixada",
                "status": "novo",
                "score": score,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            leads_novos.append(lead)

    print(f"\n📊 Resumo:")
    print(f"   Total linhas CSV: {total_com_contato + sem_contato}")
    print(f"   Com contato: {total_com_contato}")
    print(f"   Sem contato (descartados): {sem_contato}")
    print(f"   Já existem no Supabase: {ja_existem}")
    print(f"   **Novos pra importar: {len(leads_novos)}**")

    if not leads_novos:
        print("\n✅ Nada pra importar!")
        return

    # --- PASSO 3: Importar em lote ---
    print(f"\n📦 Importando {len(leads_novos)} leads em lotes de {BATCH_SIZE}...")
    importados = 0
    erros = 0
    inicio = time.time()

    for i in range(0, len(leads_novos), BATCH_SIZE):
        batch = leads_novos[i:i+BATCH_SIZE]
        
        status, body = supabase_request(api_url, key, method="POST", data=batch)
        
        if status in (200, 201):
            importados += len(batch)
        else:
            # Tentar um por um
            for lead in batch:
                s, b = supabase_request(api_url, key, method="POST", data=lead)
                if s in (200, 201):
                    importados += 1
                else:
                    erros += 1
                    if erros <= 3:
                        print(f"   ⚠️ Erro: {lead['nome']} - status {s}")
        
        decorrido = time.time() - inicio
        ritmo = importados / decorrido if decorrido > 0 else 0
        print(f"   ✅ Lote {i//BATCH_SIZE + 1}/{(len(leads_novos)-1)//BATCH_SIZE + 1}: {importados}/{len(leads_novos)} ({ritmo:.0f} leads/s)")

    total = time.time() - inicio
    print(f"\n🎉 Importação concluída em {total:.0f}s!")
    print(f"   Importados: {importados}")
    print(f"   Erros: {erros}")

if __name__ == "__main__":
    main()
