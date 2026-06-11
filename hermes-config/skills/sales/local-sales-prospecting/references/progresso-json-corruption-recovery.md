# Recuperação de progresso.json Corrompido

**Problema:** Quando 2 ou mais processos `mapear_comercios.py` rodam simultaneamente, ambos escrevem no mesmo `progresso.json`, resultando em `JSONDecodeError: Extra data`.

**Sintoma:**
```
json.decoder.JSONDecodeError: Extra data: line 135328 column 2 (char 9525936)
```

## Recuperação via Python (raw_decode)

Use `json.JSONDecoder().raw_decode()` para extrair o PRIMEIRO objeto JSON válido:

```python
import json

with open('output/rio_premium/playwright/progresso.json', 'r') as f:
    content = f.read()

decoder = json.JSONDecoder()
pos = 0
objects = []
while pos < len(content):
    content = content[pos:].lstrip()
    if not content:
        break
    try:
        obj, end = decoder.raw_decode(content)
        objects.append(obj)
        pos = end
    except:
        break

# O primeiro objeto é o principal
if objects:
    data = objects[0]
    comercios = data.get('comercios', [])
    # Extrair e gerar CSVs
```

## Gerar CSVs a partir do objeto recuperado

```python
import csv
from pathlib import Path

out = Path('output/rio_premium/playwright')
fieldnames = ['nome','telefone','whatsapp','instagram','email','categoria',
              'cidade','bairro','endereco','tem_site','url_site',
              'avaliacao','num_avaliacoes']

# Todos
with open(out / 'todos_comercios.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    w.writerows(comercios)

# Só sem site
sem_site = [c for c in comercios if not c.get('tem_site')]
with open(out / 'leads_sem_site.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    w.writerows(sem_site)
```

## Prevenção

- NUNCA rodar 2 mapeadores simultaneamente na mesma região
- Se o Chrome ficar órfão (processo morreu mas janela ficou), matar TODOS os Pythons mapeadores ANTES de reiniciar
- Usar `kill -9 <pids>` em vez de `taskkill` no git-bash