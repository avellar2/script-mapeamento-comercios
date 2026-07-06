# Padrão Upsert para Importação de Leads no Supabase

## Regras (aprendidas com erro)

1. **Usar `upsert`, não `insert`.** `table.insert(batch, on_conflict='telefone_normalizado')` NÃO funciona — o método correto é `table.upsert(batch, on_conflict='telefone_normalizado')`.
2. **Dedup dentro do CSV antes do upsert.** Mesmo telefone pode aparecer várias vezes (ex: categorias diferentes, corrupção do progresso.json). Remover duplicatas internas com `set(telefone_normalizado)` antes de enviar ao Supabase.
3. **Campos vazios de tipos numéricos.** `avaliacao` e `num_avaliacoes` vêm como string vazia `""` do CSV, mas o Supabase espera integer ou numeric. Converter para `None` (não `""` nem `0`).

## Template de script

```python
from supabase import create_client

supabase = create_client(url, key)

# 1. Buscar telefones existentes (com paginação)
existing = set()
offset = 0
while True:
    resp = supabase.table('leads').select('telefone_normalizado').range(offset, offset+999).execute()
    if not resp.data: break
    for r in resp.data:
        if r.get('telefone_normalizado'):
            existing.add(r['telefone_normalizado'])
    offset += 1000

# 2. Normalizar e dedup
def norm(p):
    d = ''.join(c for c in str(p) if c.isdigit())
    return d[2:] if d.startswith('55') and len(d) > 11 else d

novos = []
vistos = set()
for lead in csv_leads:
    tn = norm(lead.get('telefone', ''))
    if not tn or tn in existing or tn in vistos:
        continue
    vistos.add(tn)
    novos.append({
        'nome': lead['nome'],
        'telefone': lead.get('telefone', ''),
        'telefone_normalizado': tn,
        'avaliacao': lead.get('avaliacao', '').strip() or None,  # ← ESSENCIAL
        'num_avaliacoes': lead.get('num_avaliacoes', '').strip() or None,  # ← ESSENCIAL
        'origem': 'rio_premium' if 'rio' in regiao else 'baixada',
    })

# 3. Upsert em batch de 50
for i in range(0, len(novos), 50):
    batch = novos[i:i+50]
    supabase.table('leads').upsert(batch, on_conflict='telefone_normalizado').execute()
```

## Erros comuns e soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `invalid input syntax for type integer: ""` | `avaliacao` ou `num_avaliacoes` vazio | `.strip() or None` |
| `duplicate key value violates unique constraint` | Mesmo telefone aparece 2x no lote | Dedup interno antes do upsert |
| `Could not find the 'fonte' column` | Coluna `fonte` não existe na tabela | Remover do dict antes de inserir |
| Batch 100+ falha | Payload muito grande | Batch size = 50 |