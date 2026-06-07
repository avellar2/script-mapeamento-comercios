import os, csv, re, sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load .env
env_path = Path(r'C:\projetos\script-mapear-comércios\.env')
load_dotenv(env_path)

# Force read .env manually as fallback
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, val = line.partition('=')
            os.environ.setdefault(key.strip(), val.strip())

url = os.environ.get('SUPABASE_URL', '')
key = os.environ.get('SUPABASE_ANON_KEY', '')
print(f'URL: {url[:40]}...')
print(f'Key: {key[:30]}...')

sb = create_client(url, key)

# Buscar todos os telefones do Supabase
all_phones = set()
offset = 0
batch_size = 500

while True:
    batch = sb.table('leads').select('telefone,telefone_normalizado,whatsapp').range(offset, offset + batch_size - 1).execute()
    if not batch.data:
        break
    for r in batch.data:
        t = r.get('telefone_normalizado') or r.get('telefone') or ''
        w = r.get('whatsapp') or ''
        if t: all_phones.add(re.sub(r'\D', '', t))
        if w: all_phones.add(re.sub(r'\D', '', w))
    offset += batch_size
    if len(batch.data) < batch_size:
        break

print(f'Telefones unicos no Supabase: {len(all_phones)}')

# Ler leads_sem_site.csv
csv_path = Path(r'C:\projetos\script-mapear-comércios\output\playwright\leads_sem_site.csv')
with open(csv_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    csv_leads = list(reader)

print(f'Leads no CSV sem site: {len(csv_leads)}')

# Cruzar por telefone
ja_existe = 0
novos = 0
for r in csv_leads:
    tel = re.sub(r'\D', '', r.get('telefone','') or '')
    wpp = re.sub(r'\D', '', r.get('whatsapp','') or '')
    if tel in all_phones or wpp in all_phones:
        ja_existe += 1
    else:
        novos += 1

print(f'\n=== RESULTADO ===')
print(f'Ja no Supabase: {ja_existe}')
print(f'Novos (para importar): {novos}')