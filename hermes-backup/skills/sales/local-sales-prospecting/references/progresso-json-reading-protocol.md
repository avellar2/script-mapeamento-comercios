# Leitura do progresso.json do Mapeamento Rio Premium / Baixada

## Problema

O `progresso.json` pode ter **5-8 MB** (7.000+ comércios). Comandos como:
```python
python -c "import json; d=json.load(open('progresso.json')); ..."
```
causam timeout no Hermes (mais de 10s para processar o JSON inteiro).

## Solução: grep + search_files

Em vez de carregar o JSON inteiro, usar `search_files` com padrões regex:

```bash
# Total de comércios (contar linhas "nome:")
search_files pattern='"nome":' path=output/rio_premium/playwright/progresso.json output_mode=count

# Total sem site
search_files pattern='"tem_site": false' path=output/rio_premium/playwright/progresso.json output_mode=count

# Tarefas concluídas (contar vírgulas dentro de categorias_prontas)
search_files pattern='"categorias_prontas"' path=output/rio_premium/playwright/progresso.json output_mode=content

# Em andamento (ler bloco específico com read_file offset=... limit=10)
grep -n "categorias_em_andamento" output/rio_premium/playwright/progresso.json
read_file path=output/rio_premium/playwright/progresso.json offset={linha+1} limit=10
```

## Estrutura do JSON

```json
{
  "categorias_prontas": [
    "Barra da Tijuca - Rio de Janeiro, RJ::clínica de estética",
    "Barra da Tijuca - Rio de Janeiro, RJ::dentista",
    ...
  ],
  "categorias_em_andamento": {
    "Méier - Rio de Janeiro, RJ::micropigmentação": {
      "indice": 20,
      "total": 60
    }
  },
  "comercios": [
    {
      "nome": "...",
      "telefone": "...",
      "cidade": "Barra da Tijuca - Rio de Janeiro, RJ",
      "categoria": "clínica de estética",
      "tem_site": false,
      ...
    },
    ...
  ]
}
```

## Métricas rápidas (grep)

```bash
# Progresso geral
echo "Tarefas: $(grep -oP '(?<="categorias_prontases": )\[[^\]]*' output/rio_premium/playwright/progresso.json | tr ',' '\n' | wc -l)"

# Categorias em andamento
grep -oP '"categorias_em_andamento": \{"[^}]+' output/rio_premium/playwright/progresso.json

# Total leads coletados
grep -c '"nome":' output/rio_premium/playwright/progresso.json

# Total sem site (leads úteis)
grep -c '"tem_site": false' output/rio_premium/playwright/progresso.json

# Por bairro (contar ocorrências de cidade)
grep -oP '"cidade": "[^"]+' output/rio_premium/playwright/progresso.json | sort | uniq -c | sort -rn
```

## Script Python rápido (sem timeout, só grep + Python leve)

```bash
cd /c/projetos/script-mapear-comércios
total=$(grep -c '"nome":' output/rio_premium/playwright/progresso.json)
sem_site=$(grep -c '"tem_site": false' output/rio_premium/playwright/progresso.json)
echo "Coletados: $total | Sem site: $sem_site"
```