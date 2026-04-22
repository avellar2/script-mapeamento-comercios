# Organização do Projeto

## Quando Fazer
Depois que o `envio_emails_zoho.py` terminar de rodar.

---

## Estrutura Nova

```
output/
  playwright/                    ← 7.981 leads (nosso scraping)
    todos_comercios.csv          ← todos os leads
    leads_sem_site.csv           ← só os sem site (4.371)
    progresso_emails.json        ← emails capturados via CNPJ/site

  apify/                         ← 100 leads (Apify)
    leads_apify.csv              ← leads do processar_leads.py
    progresso_emails_cnpj.json   ← emails capturados via CNPJ/API

  envios/                        ← controle de envio
    progresso_envio.json         ← quem já recebeu email
```

---

## Arquivos pra Mover

| Arquivo Atual | Para |
|---|---|
| `output/todos_comercios.csv` | `output/playwright/todos_comercios.csv` |
| `output/leads_sem_site.csv` | `output/playwright/leads_sem_site.csv` |
| `output/leads_sem_site.xlsx` | `output/playwright/leads_sem_site.xlsx` |
| `output/progresso_emails.json` | `output/playwright/progresso_emails.json` |
| `output/leads_baixada_*.csv` | `output/apify/leads_apify.csv` |
| `output/leads_baixada_*.xlsx` | `output/apify/leads_apify.xlsx` |
| `output/progresso_emails_cnpj.json` | `output/apify/progresso_emails_cnpj.json` |
| `output/progresso_envio.json` | `output/envios/progresso_envio.json` |
| `output/progresso.json` | apagar (antigo) |

---

## Scripts pra Ajustar Caminhos

| Script | O que muda |
|---|---|
| `envio_emails_zoho.py` | `LEADS_FILE` → `output/playwright/todos_comercios.csv` |
| `envio_emails_zoho.py` | `EMAILS_FILE` → `output/playwright/progresso_emails.json` |
| `envio_emails_zoho.py` | `PROGRESS_FILE` → `output/envios/progresso_envio.json` |
| `buscar_emails_cnpj.py` | `CSV_FILE` → `output/apify/leads_apify.csv` |
| `buscar_emails_cnpj.py` | `PROGRESS_FILE` → `output/apify/progresso_emails_cnpj.json` |
| `capturar_emails.py` | caminhos de output → `output/playwright/` |
| `processar_leads.py` | `OUTPUT_DIR` → `output/apify/` |
| `buscar_leads_apify.py` | `OUTPUT_DIR` → `output/apify/` |

---

## HTMLs (podem ficar onde estão)

| Arquivo | Fica em |
|---|---|
| `output/leads_baixada.html` | `output/apify/leads_apify.html` |
| `frontend/dashboard.html` | não mexer |
| `frontend/dashboard-emails.html` | não mexer |
| `frontend/leads-quentes.html` | não mexer |

---

## Comandos pra Executar

```bash
# 1. Criar pastas
mkdir -p output/playwright output/apify output/envios

# 2. Mover arquivos (ajustar nomes com timestamp)
mv output/todos_comercios.csv output/playwright/
mv output/leads_sem_site.csv output/playwright/
mv output/leads_sem_site.xlsx output/playwright/
mv output/progresso_emails.json output/playwright/
mv output/leads_baixada_*.csv output/apify/leads_apify.csv
mv output/leads_baixada_*.xlsx output/apify/leads_apify.xlsx
mv output/progresso_emails_cnpj.json output/apify/
mv output/progresso_envio.json output/envios/
rm output/progresso.json
mv output/leads_baixada.html output/apify/leads_apify.html

# 3. Ajustar caminhos nos scripts (fazer via Claude)
```

---

## Comparação Playwright vs Apify

Métricas pra avaliar qual vale mais:

| Métrica | Playwright | Apify |
|---|---|---|
| Total de leads | 7.981 | 100 |
| Com email | 4.306 (54%) | 77 (77%) |
| Com telefone | ? | 99% |
| Nichos cobertos | 40 categorias | 3 nichos |
| Custo | grátis (só tempo) | ~$0.50/100 resultados |
| Tempo de coleta | ~horas | ~minutos |
| Taxa de resposta email | (preencher depois) | (preencher depois) |
