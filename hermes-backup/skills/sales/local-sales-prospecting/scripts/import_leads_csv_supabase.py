#!/usr/bin/env python3
"""
Importar leads do CSV (leads_sem_site.csv) para o Supabase.
Filtra só leads com telefone ou WhatsApp.

Uso:
    python import_leads_csv_supabase.py

O script:
1. Lê output/playwright/leads_sem_site.csv
2. Filtra leads com telefone ou WhatsApp (descarta ~839 sem contato)
3. Normaliza telefones para +55XXXXXXXXXX
4. Atribui score por nicho (salão=80, restaurante=70, clínica=75, etc.)
5. Verifica duplicatas por telefone_normalizado antes de inserir
6. Importa com origem='baixada' e status='novo'

Resultado esperado:
- ~3.590 leads importados (dos 4.429 totais)
- Duplicatas são puladas silenciosamente
- Erros de rede (getaddrinfo failed) indicam problema de DNS/internet

Falhas comuns:
- [Errno 11001] getaddrinfo failed → DNS bloqueado ou sem internet
- SUPABASE_URL/SUPABASE_ANON_KEY não configurados → verificar .env
"""

import csv
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Carregar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

from supabase import create_client

CSV_PATH = Path(__file__).parent / "output" / "playwright" / "leads_sem_site.csv"

def normalizar_telefone(tel):
    """Normaliza telefone para formato +55XXXXXXXXXX"""
    if not tel:
        return ""
    numeros = "".join(c for c in str(tel) if c.isdigit())
    if numeros.startswith("55") and len(numeros) > 11:
        numeros = numeros[2:]
    if len(numeros) == 10 or len(numeros) == 11:
        return f"+55{numeros}"
    return ""

def main():
    if not CSV_PATH.exists():
        print(f"❌ CSV não encontrado: {CSV_PATH}")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL ou SUPABASE_ANON_KEY não configurados")
        sys.exit(1)

    supabase = create_client(url, key)

    leads_para_importar = []
    com_contato = 0
    sem_contato = 0
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            telefone = normalizar_telefone(row.get("telefone", ""))
            whatsapp = normalizar_telefone(row.get("whatsapp", ""))
            
            if not telefone and not whatsapp:
                sem_contato += 1
                continue
            
            com_contato += 1
            
            lead = {
                "nome": row.get("nome", "").strip(),
                "nicho": row.get("nicho", "").strip(),
                "cidade": row.get("cidade", "").strip(),
                "bairro": row.get("bairro", "").strip(),
                "telefone": telefone,
                "whatsapp": whatsapp,
                "instagram": row.get("instagram", "").strip(),
                "endereco": row.get("endereco", "").strip(),
                "tem_site": False,
                "origem": "baixada",
                "status": "novo",
                "score": 50,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            nicho_lower = lead["nicho"].lower()
            if any(x in nicho_lower for x in ["salão", "salao", "barbearia", "estetica", "estética", "beleza"]):
                lead["score"] = 80
            elif any(x in nicho_lower for x in ["restaurante", "pizzaria", "lanchonete", "comida"]):
                lead["score"] = 70
            elif any(x in nicho_lower for x in ["clínica", "clinica", "consultório", "consultorio", "médico", "medico"]):
                lead["score"] = 75
            
            leads_para_importar.append(lead)

    print(f"📊 Resumo do CSV:")
    print(f"   Total: {com_contato + sem_contato}")
    print(f"   Com contato: {com_contato}")
    print(f"   Sem contato: {sem_contato}")
    print(f"   Vão ser importados: {len(leads_para_importar)}")
    print()

    if not leads_para_importar:
        print("✅ Nenhum lead pra importar")
        return

    print("🔍 Verificando duplicatas e importando...")
    
    importados = 0
    duplicados = 0
    erros = 0

    for i, lead in enumerate(leads_para_importar, 1):
        telefone_para_checar = lead["telefone"] or lead["whatsapp"]
        
        if not telefone_para_checar:
            continue

        try:
            existente = supabase.table("leads").select("id").eq("telefone_normalizado", telefone_para_checar).execute()
            
            if existente.data:
                duplicados += 1
                continue
            
            supabase.table("leads").insert(lead).execute()
            importados += 1
            
            if i % 100 == 0:
                print(f"   ✅ {i}/{len(leads_para_importar)}...")
                
        except Exception as e:
            erros += 1
            if erros <= 5:
                print(f"   ⚠️ Erro: {e}")

    print()
    print("🎉 Concluído!")
    print(f"   Importados: {importados}")
    print(f"   Duplicados: {duplicados}")
    print(f"   Erros: {erros}")

if __name__ == "__main__":
    main()
