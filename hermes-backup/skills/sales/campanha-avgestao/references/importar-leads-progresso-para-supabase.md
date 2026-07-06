# Importar leads do progresso.json para o Supabase

## Contexto
O script `mapear_comercios.py` salva leads capturados em `output/avgestao/assistencias/progresso.json`.
Esses leads NÃO vão automaticamente pro Supabase — precisam ser importados manualmente via API REST.

## Colunas que existem na tabela `leads`
```
id, nome, telefone, whatsapp, telefone_normalizado, instagram, email,
categoria, nicho, cidade, bairro, endereco, tem_site, url_site,
avaliacao, num_avaliacoes, score, prioridade, oferta_sugerida,
mensagem_whatsapp, link_whatsapp, status, origem, ultimo_contato_em,
proximo_followup_em, observacoes, resposta_cliente, created_at,
updated_at, produto, grupo, subnicho, faz_assistencia,
score_avgestao, motivos_score, nome_curto
```

## Campos que NÃO existem (causam erro PGRST204)
- `link_maps` ❌
- `place_id` ❌

## Script de importação (Python)

```python
import json, re, os, urllib.request, ssl
from pathlib import Path

# Carregar progresso.json
with open('output/avgestao/assistencias/progresso.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
comercios = data.get('comercios', [])

def normalizar(tel):
    if not tel or tel == 'Rotas' or tel.startswith('http'):
        return ''
    nums = re.sub(r'[^0-9]', '', tel)
    if len(nums) == 10 and nums[:2] == '21': nums = '55' + nums
    elif len(nums) == 11 and nums[:2] == '21': nums = '55' + nums
    elif len(nums) == 8: nums = '5521' + nums
    elif len(nums) == 9 and nums[0] == '9': nums = '5521' + nums
    return nums

def eh_celular(r):
    wpp = r.get('whatsapp', '') or r.get('telefone', '')
    nums = normalizar(wpp)
    if not nums: return False
    if '5521' in nums:
        idx = nums.index('5521') + 4
        resto = nums[idx:]
        return len(resto) >= 9 and resto[0] == '9'
    return False

# Selecionar leads (excluir duplicatas, Eduardo Cell, números repetidos)
nomes_vistos = set()
selecionados = []
for c in comercios:
    if not eh_celular(c): continue
    nome = c['nome'].strip().lower()
    if nome in nomes_vistos: continue
    nomes_vistos.add(nome)
    if 'eduardo cell' in nome: continue
    wpp = c.get('whatsapp', '') or c.get('telefone', '')
    nums = normalizar(wpp)
    if nums == '5521964229894': continue  # número repetido (eletrodomésticos)
    nota = float(c.get('avaliacao', 0) or 0)
    selecionados.append((nota, c))

selecionados.sort(key=lambda x: -x[0])
top30 = [c for _, c in selecionados[:30]]

# Conectar Supabase
env_path = Path('.env')
# ... carregar SUPABASE_URL e SUPABASE_ANON_KEY ...

importados = 0
for c in top30:
    wpp = c.get('whatsapp', '') or c.get('telefone', '')
    nums = normalizar(wpp)
    
    # Verificar duplicata
    check = f'{url}/rest/v1/leads?telefone_normalizado=eq.{nums}&select=id'
    # ... se já existe, pular ...
    
    body = json.dumps({
        'nome': c['nome'],
        'categoria': c.get('categoria', ''),
        'cidade': c.get('cidade', ''),
        'bairro': c.get('bairro', ''),
        'endereco': c.get('endereco', ''),
        'telefone': c.get('telefone', '') or '',
        'whatsapp': c.get('whatsapp', '') or '',
        'telefone_normalizado': nums,
        'instagram': c.get('instagram', '') or '',
        'email': c.get('email', '') or '',
        'tem_site': bool(c.get('tem_site', False)),
        'url_site': c.get('url_site', '') or '',
        'avaliacao': float(c.get('avaliacao', 0) or 0),
        'num_avaliacoes': int(c.get('num_avaliacoes', 0) or 0),
        'subnicho': c.get('subnicho', '') or '',
        'origem': 'baixada',
        'status': 'novo',
        'produto': 'avgestao'  # IMPORTANTE: filtrar depois com &produto=eq.avgestao
    }).encode()
    
    req = urllib.request.Request(
        f'{url}/rest/v1/leads',
        data=body,
        headers={'apikey': key, 'Authorization': f'Bearer {key}',
                 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
    )
    resp = urllib.request.urlopen(req, context=ssl.create_default_context())
    importados += 1
```

## Verificação pós-importação
```python
params = urllib.parse.urlencode({
    'select': 'id,nome,telefone_normalizado,status,produto',
    'produto': 'eq.avgestao',
    'limit': 50
})
```
