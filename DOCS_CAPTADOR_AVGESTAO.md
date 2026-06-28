# Captador AVGESTAO — Documentação

## Visão geral

O captador AVGESTAO mapeia comércios no Google Maps para prospecção do
sistema AVGESTAO (SaaS de orçamentos, ordens de serviço e portal do cliente).

Fluxo completo:

```
mapear (Google Maps) → prospectar (qualificar) → campanha (planilha de abordagem)
```

**NUNCA envia mensagens automaticamente.** As planilhas geradas contêm links
`wa.me` para envio manual.

## Dependências

- Python 3.12+
- Playwright (`pip install playwright && playwright install chromium`)
- openpyxl (`pip install openpyxl`)
- Supabase (opcional, `pip install supabase`)
- python-dotenv (`pip install python-dotenv`)

## Instalação

```bash
git clone <repo>
cd script-mapear-comércios
pip install -r requirements.txt
playwright install chromium
```

## Configuração do `.env`

Crie um arquivo `.env` na raiz:

```
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<sua-chave-anon>
```

O Supabase é opcional — sem ele, o dedup funciona apenas intra-run (entre
cidades do mesmo run).

## Aplicação manual da migration

```bash
# No SQL Editor do Supabase, execute:
# supabase/migration_avgestao.sql
```

A migration adiciona colunas: `produto`, `grupo`, `subnicho`, `msg_cat`,
`faz_assistencia`, `score_avgestao`, `motivos_score`, `nome_curto`,
`source_query`, `source_scope`, `run_id`, `captured_at`, `maps_url`.

## Comandos

### Para uma cidade

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --cidade "Nova Iguaçu, RJ" --max-por-consulta 10
```

### Para várias cidades

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" \
  --max-por-consulta 10 --max-total 100
```

### Para um estado

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo uf --uf RJ --max-por-consulta 10 --max-total 500
```

### Para vários estados

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo ufs --uf RJ SP MG --max-total 1000
```

### Para uma região

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo regiao --regiao sudeste --max-total 2000
```

Regiões IBGE válidas: `norte`, `nordeste`, `sudeste`, `sul`, `centro-oeste`.

### Para o Brasil

```bash
# Exige --max-total, --limite-cidades ou --confirmar-grande-execucao
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo brasil --max-total 5000
```

### Arquivo de cidades

```bash
# Arquivo com uma cidade por linha: "Nome da Cidade, UF"
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo arquivo --cidades-arquivo minhas_cidades.txt --max-total 300
```

### Dry-run (sem abrir navegador)

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo uf --uf RJ --max-total 300 --dry-run
```

O dry-run resolve as cidades, gera a fila e mostra a distribuição por
UF, região, grupo, subnicho e cidade — sem abrir o Google Maps.

### Somente gerar fila

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo uf --uf RJ --max-total 300 --somente-gerar-fila
```

Idêntico ao dry-run.

### Resume (retomar execução interrompida)

```bash
python mapear_comercios.py --produto avgestao \
  --resume --run-id run_20260628_120000_abc123
```

Retoma um run a partir do checkpoint. Tarefas concluídas NÃO são repetidas.
Se a configuração estrutural (grupos, subnichos, cidades) for diferente,
o resume aborta — é necessário um novo run.

### Teste pequeno

```bash
python mapear_comercios.py --produto avgestao --grupo assistencias \
  --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" \
  --max-por-consulta 3 --max-total 10
```

### Orquestrador (comando único)

```bash
python executar_campanha_avgestao.py \
  --grupo assistencias --escopo uf --uf RJ --max-total 300 --top 20
```

Executa mapear → prospectar → campanha em sequência, com o mesmo run_id.

```bash
# Apenas mapear
python executar_campanha_avgestao.py \
  --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-total 300

# Dry-run (para após gerar fila)
python executar_campanha_avgestao.py \
  --grupo assistencias --escopo uf --uf RJ --max-total 300 --dry-run

# Retomar run interrompido
python executar_campanha_avgestao.py --resume --run-id <RUN_ID>

# Run com ID próprio
python executar_campanha_avgestao.py \
  --run-id meu_run_001 --grupo assistencias --escopo uf --uf RJ --max-total 300
```

## Estrutura da pasta do run

```
output/avgestao/runs/<run_id>/
├── config.json          # Configuração do run (cidades, grupos, limites, hash)
├── fila.json            # Fila de tarefas com status
├── checkpoint.json      # Estado atual (índice da fila, contadores)
├── leads_parciais.csv   # Leads capturados (CSV, COLUNAS_CSV_GEO)
├── leads_parciais.xlsx  # Leads capturados (Excel)
├── resumo.json          # Resumo final (tarefas, leads, status)
├── erros.jsonl          # Erros registrados (JSONL)
└── leads_<grupo>_<escopo>_<run_id>.xlsx  # XLSX geográfico final (29 colunas)
```

## Significado dos status da fila

| Status | Significado |
|--------|-------------|
| `pendente` | Tarefa ainda não executada |
| `concluida` | Tarefa concluída com sucesso |
| `ignorada_limite` | Tarefa ignorada por limite (max-total, max-por-cidade, etc.) |
| `erro` | Tarefa falhou (todas as tentativas esgotadas) |
| `interrompida` | Execução interrompida (Ctrl+C ou CAPTCHA) |

## Tratamento de CAPTCHA

Se o Google Maps exibir CAPTCHA, a execução é interrompida automaticamente.
O estado é salvo no checkpoint. O próximo resume continuará das tarefas pendentes.

Mensagem exibida:
```
🛑 CAPTCHA detectado — execução interrompida e estado salvo.
```

## Interrupção com Ctrl+C

Pressionar Ctrl+C interrompe a execução e salva o estado. O resume continua
das tarefas pendentes.

```
⏹ Execução interrompida — estado salvo.
```

## Limites

| Flag | Descrição |
|------|-----------|
| `--max-total` | Limite total de leads únicos no run |
| `--max-por-cidade` | Limite de leads únicos por cidade |
| `--max-por-subnicho` | Limite de leads únicos por subnicho |
| `--max-por-consulta` | Máximo de resultados por consulta ao Google Maps |
| `--limite-cidades` | Limita o número de cidades processadas |

Quando um limite é atingido, as tarefas restantes são marcadas como
`ignorada_limite` (nunca como erro).

## Grupos disponíveis

| Grupo | Subnichos |
|-------|-----------|
| `assistencias` | Celular, computadores, impressoras, eletrodomésticos, eletrônicos |
| `refrigeracao` | Refrigeração, climatização, ar-condicionado, geladeiras |
| `automotivo` | Oficina mecânica, autoelétrica, motos, centro automotivo, injeção eletrônica |
| `sob_medida` | Vidraçaria, marcenaria, móveis planejados, serralheria, portões |
| `servicos_externos` | Energia solar, segurança eletrônica, câmeras, dedetização, piscinas, predial |

## Solução de erros comuns

**Playwright não encontrado:**
```bash
pip install playwright
playwright install chromium
```

**Chromium não compatível com o perfil:**
O captador usa `channel="chrome"` (Chrome instalado no sistema).
Se falhar, tenta o Chromium bundled do Playwright como fallback.

**Supabase não configurado:**
O captador funciona sem Supabase — o dedup é feito apenas entre as cidades
do mesmo run. Para comparar com leads já existentes na base, configure o `.env`.

**Run inexistente no resume:**
Verifique o `--run-id`. Runs ficam em `output/avgestao/runs/<run_id>/`.
Liste runs existentes com `ls output/avgestao/runs/`.

**Configuração estrutural divergente no resume:**
O resume exige que grupos, subnichos e cidades sejam idênticos ao run
original. Para alterar a configuração, inicie um novo run.

**Timeout ao carregar o Google Maps:**
O script tem 3 níveis de retry: carregamento inicial, scroll no painel,
e navegação entre resultados. Se persistir, o erro é registrado e a
próxima tarefa é executada.
