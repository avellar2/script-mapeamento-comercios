#!/usr/bin/env python3
"""Importar leads_sem_site.csv do Rio Premium para o Supabase."""
import csv, os, sys
from pathlib import Path

# Carregar .env
env_path = Path('.env')
for line in env_path.read_text().splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1)
        v = v.strip('\'"')
        os.environ[k] = v

from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_ANON_KEY')
if not url or not key:
    print('SUPABASE_URL ou SUPABASE_ANON_KEY nao encontrados')
    sys.exit(1)

supabase = create_client(url, key)

csv_path = 'output/rio_premium/playwright/leads_sem_site.csv'
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    leads = list(reader)

print(f'Total leads sem site: {len(leads)}')

# Buscar telefones existentes no Supabase
print('Buscando telefones existentes no Supabase...')
existing = set()
offset = 0
page_size = 1000
while True:
    resp = supabase.table('leads').select('telefone_normalizado').range(offset, offset + page_size - 1).execute()
    if not resp.data:
        break
    for r in resp.data:
        if r.get('telefone_normalizado'):
            existing.add(r['telefone_normalizado'])
    if len(resp.data) < page_size:
        break
    offset += page_size

print(f'Telefones ja no Supabase: {len(existing)}')

def normalize_phone(p):
    if not p:
        return ''
    digits = ''.join(c for c in str(p) if c.isdigit())
    if digits.startswith('55') and len(digits) > 11:
        digits = digits[2:]
    return digits

# Preparar inserts
novos = []
duplicados = 0
sem_telefone = 0
for lead in leads:
    nome = lead.get('nome', '').strip()
    fone_raw = lead.get('telefone', '').strip()
    if not nome:
        continue
    fone_norm = normalize_phone(fone_raw)
    if not fone_norm:
        sem_telefone += 1
        continue
    if fone_norm in existing:
        duplicados += 1
        continue

    whatsapp_raw = lead.get('whatsapp', '').strip()
    whatsapp_norm = normalize_phone(whatsapp_raw) if whatsapp_raw else fone_norm

    novos.append({
        'nome': nome,
        'telefone': fone_raw,
        'telefone_normalizado': fone_norm,
        'whatsapp': whatsapp_raw,
        'categoria': lead.get('categoria', '').strip(),
        'cidade': lead.get('cidade', '').strip(),
        'bairro': lead.get('bairro', '').strip(),
        'endereco': lead.get('endereco', '').strip(),
        'instagram': lead.get('instagram', '').strip(),
        'email': lead.get('email', '').strip(),
        'avaliacao': lead.get('avaliacao', '').strip() or None,
        'num_avaliacoes': lead.get('num_avaliacoes', '').strip() or None,
        'tem_site': False,
        'status': 'novo',
        'origem': 'rio_premium',
    })

# Remover duplicatas dentro do proprio CSV (mesmo telefone_normalizado)
vistos = set()
novos_dedup = []
for lead in novos:
    tn = lead['telefone_normalizado']
    if tn not in vistos:
        vistos.add(tn)
        novos_dedup.append(lead)

print(f'Duplicatas dentro do CSV: {len(novos) - len(novos_dedup)}')
novos = novos_dedup

print(f'\nNovos para importar (dedup final): {len(novos)}')

# Batch upsert - ignorar duplicatas por telefone_normalizado
batch_size = 50
importados = 0
for i in range(0, len(novos), batch_size):
    batch = novos[i:i+batch_size]
    try:
        supabase.table('leads').upsert(batch, on_conflict='telefone_normalizado').execute()
        importados += len(batch)
        print(f'  {importados}/{len(novos)} importados...')
    except Exception as e:
        # Tentar um por um
        for lead in batch:
            try:
                supabase.table('leads').upsert(lead, on_conflict='telefone_normalizado').execute()
                importados += 1
            except:
                pass
        print(f'  ~{importados}/{len(novos)} (lote {i} parcial)...')

print(f'\nTotal importado: {importados}')