# Supabase Leads Schema & Query Patterns

## Tabela: `leads`

Colunas:
- `id` (uuid) — PK
- `nome`, `telefone`, `whatsapp`, `telefone_normalizado`, `instagram`, `email`
- `categoria`, `nicho`, `cidade`, `bairro`, `endereco`
- `tem_site` (bool), `url_site`
- `avaliacao`, `num_avaliacoes`
- `score`, `prioridade`
- `oferta_sugerida`, `mensagem_whatsapp`, `link_whatsapp`
- `status` — valores: `novo`, `pronto_para_enviar`, `abordado`, `respondeu`, `follow_up`, `interessado`, `convertido`, `perdido`
- `origem` — valores: `importacao_planilha`, `playwright`, `whatsapp`
- `ultimo_contato_em`, `proximo_followup_em`
- `observacoes`, `resposta_cliente`
- `created_at`, `updated_at`

## Query Pattern (Python)

```python
import os
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

from supabase import create_client
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])

# Paginated fetch (supabase-py limits to 1000 per page)
def fetch_all(table, fields='*', page_size=1000):
    all_data = []
    offset = 0
    while True:
        r = sb.table(table).select(fields).range(offset, offset + page_size - 1).execute()
        if not r.data:
            break
        all_data.extend(r.data)
        offset += page_size
        if len(r.data) < page_size:
            break
    return all_data

# Count
r = sb.table('leads').select('id', count='exact').execute()
print(r.count)
```

## Status Counts (2025-06-05)

- Total: 3.355
- `pronto_para_enviar`: 1.635
- `novo`: 1.679
- `abordado`: 41

## Cidades no Supabase (2025-06-06)

São João de Meriti, Nilópolis, Duque de Caxias, Itaguaí, Nova Iguaçu, Mesquita, Japeri, Belford Roxo, Queimados, Seropédica, Paracambi, Guapimirim, Magé

### Distribuição por cidade (leads sem site)

| Cidade | Qtd |
|--------|-----|
| Mesquita | 346 |
| Belford Roxo | 346 |
| Queimados | 339 |
| Nilópolis | 336 |
| Duque de Caxias | 325 |
| São João de Meriti | 319 |
| Itaguaí | 317 |
| Japeri | 278 |
| Seropédica | 266 |
| Nova Iguaçu | 255 |
| Paracambi | 213 |
| Guapimirim | 8 |
| Magé | 7 |
| **Total** | **3.355** |

### Distribuição por nicho (top 15)

| Nicho | Qtd |
|-------|-----|
| Oficina mecânica | 140 |
| Material de construção | 119 |
| Padaria | 115 |
| Serralheria | 114 |
| Restaurante | 113 |
| Papelaria | 111 |
| Advogado | 109 |
| Pet shop | 108 |
| Barbearia | 106 |
| Loja de roupas | 105 |
| Dentista | 104 |
| Farmácia | 103 |
| Ótica | 101 |
| Salão de beleza | 97 |
| Eletricista | 97 |

## Comparação CSV vs Supabase (Deduplicação)

Ao receber um novo CSV do `mapear_comercios.py`, SEMPRE comparar com Supabase antes de importar. Metodologia:

```python
import csv
from supabase import create_client

# Carregar .env manualmente
with open('.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])

# Buscar TODOS os leads do Supabase (paginado)
def fetch_all(table, fields='*', page_size=1000):
    all_data = []
    offset = 0
    while True:
        r = sb.table(table).select(fields).range(offset, offset + page_size - 1).execute()
        if not r.data:
            break
        all_data.extend(r.data)
        if len(r.data) < page_size:
            break
        offset += page_size
    return all_data

all_sb = fetch_all('leads', 'nome,telefone,telefone_normalizado,cidade')

# Normalizar telefone: remover 55 do prefixo se existir
def normalize_phone(s):
    digits = ''.join(c for c in str(s) if c.isalnum())
    if digits.startswith('55') and len(digits) > 10:
        digits = digits[2:]  # 5521... -> 21...
    return digits

# Construir sets de lookup
sb_phones = {normalize_phone(l.get('telefone_normalizado') or l.get('telefone') or ''): l 
              for l in all_sb if normalize_phone(l.get('telefone_normalizado') or l.get('telefone'))}

# Ler CSV com encoding utf-8-sig (corrige BOM \ufeff na primeira coluna)
csv_leads = []
with open('output/playwright/todos_comercios.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_leads.append(row)

# Comparar
dup_phone = 0
for row in csv_leads:
    tel = normalize_phone(row.get('telefone', ''))
    if tel and tel in sb_phones:
        dup_phone += 1

novos = len(csv_leads) - dup_phone
print(f'Total CSV: {len(csv_leads)}, Duplicados: {dup_phone}, Novos: {novos}')
```

**Resultado típico (2025-06-06)**:
- CSV novo: 7.142 leads
- Duplicados por telefone: 1.041
- Novos (não estão no Supabase): ~5.794
- Com telefone: 6.189/7.142 (86.7%) → quase todos têm WhatsApp potencial

**Regra**: nunca assumir que CSV novo = leads novos. Sempre cruzar com Supabase primeiro.

## Importar CSV para Supabase

```bash
cd /c/projetos/script-mapear-comércios
python import_leads_to_supabase.py output/playwright/leads_sem_site.csv
```

Ou via Python direto (após carregar .env):
```python
# Verificar colunas do CSV
import pandas as pd
df = pd.read_csv('output/playwright/leads_sem_site.csv')
print(df.columns.tolist())
print(len(df))
```