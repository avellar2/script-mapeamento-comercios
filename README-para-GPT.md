# Script Mapear Comércios - Sistema de Prospecção B2B

## O que é

Sistema completo de prospecção e venda de landing pages para comércios locais na **Baixada Fluminense, RJ**.

O funil funciona assim:

```
MAPEAR → PROSPECTAR → QUALIFICAR → ABORDAR → ENVIAR → TRACKAR
```

1. **Mapear**: Scrapear Google Maps em busca de comércios sem site
2. **Prospectar**: Gerar planilha qualificada com score e prioridade
3. **Qualificar**: Filtrar melhores leads e classificar por nicho
4. **Abordar**: Gerar links de WhatsApp com mensagem personalizada
5. **Enviar**: Enviar emails com templates + tracking de aberturas
6. **Trackar**: Acompanhar métricas no dashboard

---

## Estrutura do Projeto

```
script-mapear-comércios/
├── mapear_comercios.py          # Scraper Google Maps (Playwright)
├── prospectar_leads.py          # Qualificação e pontuação
├── campanha_diaria.py           # Gerador de planilha diária
├── processar_leads.py           # Processamento de leads
├── envio_emails_zoho.py         # Envio de emails via Zoho SMTP
├── buscar_emails_cnpj.py        # Busca emails via CNPJ
├── buscar_emails_playwright.py  # Captura emails com Playwright
├── capturar_emails.py           # Captura diversos emails
├── testar_sistema.py            # Teste do sistema completo
├── gerar_leads-quentes.py       # Gera leads quentes
├── gerar_painel_prospeccao.py   # Gera painel de prospecção
├── frontend/
│   ├── dashboard.html           # Dashboard de comércios
│   ├── dashboard-emails.html     # Dashboard de emails enviados
│   └── server.py                # Servidor local
├── output/
│   ├── playwright/              # Dados brutos do scraper
│   ├── prospeccao/              # Planilhas de prospecção
│   ├── campanhas/               # Campanhas diárias
│   └── painel/                  # Painel de prospecção web
└── templates/                   # Templates de email HTML

```

---

## Cada Script

### `mapear_comercios.py`
Scraping do Google Maps usando Playwright.

**O que faz:**
- Busca comércios em 12 cidades da Baixada Fluminense
- 39 categorias (restaurantes, barbearias, salões de beleza, etc.)
- Extrai: nome, endereço, telefone, WhatsApp, Instagram, email, avaliação, site
- Salva CSV completo e CSV só de leads sem site

**Cidades:** Duque de Caxias, Nova Iguaçu, São João de Meriti, Belford Roxo, Nilópolis, Mesquita, Queimados, Itaguaí, Seropédica, Paracambi, Japeri

**Uso:**
```bash
python mapear_comercios.py
```

**Saída:**
- `output/playwright/todos_comercios.csv` - Todos os comércios
- `output/playwright/leads_sem_site.csv` - Só os sem site
- `output/playwright/leads_sem_site.xlsx` - Versão Excel

---

### `prospectar_leads.py`
Qualificação e pontuação dos leads.

**O que faz:**
- Lê dados do CSV de mapeamento
- Calcula score (0-100) baseado em:
  - Sem site: +30
  - Tem telefone/WhatsApp: +20
  - Nota >= 4.0: +15
  - 20+ avaliações: +15
  - Tem Instagram: +10
  - Nicho bom para landing: +10
  - Franquia grande: -30
  - Site profissional: -20
- Classifica prioridade: Alta (70+), Média (40-69), Baixa (<40)
- Gera oferta sugerida por nicho (Página de Agendamento, Cardápio Digital, Mini Site)
- Gera mensagem de WhatsApp personalizada
- Gera link direto do WhatsApp

**Uso:**
```bash
python prospectar_leads.py
python prospectar_leads.py --arquivo caminho/do/arquivo.csv
python prospectar_leads.py --saida meu_arquivo.xlsx
```

**Saída:**
- `output/prospeccao/leads_prospeccao.xlsx` - Planilha completa
  - Aba "Leads": todos os leads com dados e métricas
  - Aba "Resumo": estatísticas por cidade, nicho e oferta

---

### `campanha_diaria.py`
Gerador de planilha para abordagem diária.

**O que faz:**
- Filtra leads de Alta prioridade com score >= 70
- Classifica por nicho (Estética, Barbearia, Comida-Cardápio, Serviços Locais)
- Gera mensagem de WhatsApp otimizada por nicho
- Cria links de WhatsApp diretos
- Adiciona follow-up recomendado (7 dias)

**Uso:**
```bash
python campanha_diaria.py
python campanha_diaria.py --top 30
python campanha_diaria.py --hoje
```

**Saída:**
- `output/campanhas/campanha_diaria_YYYY-MM-DD.xlsx`
- Abas: Top 50, Estética, Barbearia, Comida-Cardápio, Serviços Locais, Outros, Resumo

---

### `envio_emails_zoho.py`
Envio de emails em massa via Zoho SMTP.

**O que faz:**
- Lê leads do CSV
- Envia via Zoho SMTP (email profissional)
- Template HTML com tracking pixel
- Salva cada envio no Supabase com tracking ID
- Anexa o pixel de tracking para medir aberturas

**Uso:**
```bash
python envio_emails_zoho.py
```

**Variáveis de ambiente (.env):**
```
ZOHO_EMAIL=seu@email.com
ZOHO_APP_PASSWORD=senha_de_app
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=chave_anon
```

---

### `frontend/dashboard-emails.html`
Dashboard para acompanhar emails enviados.

**O que mostra:**
- Total de emails enviados
- Taxa de abertura
- Gráficos por categoria
- Filtros: cidade, categoria, status
- Tabela completa com status de cada email

**Acesso:** Deployado no Vercel ou local via Python server

---

## O Funil Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MAPEAR                                                    │
│    mapear_comercios.py → output/playwright/leads_sem_site.csv │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PROSPECTAR                                                │
│    prospectar_leads.py → output/prospeccao/leads_prospeccao.xlsx│
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CAMPANHA DIÁRIA                                           │
│    campanha_diaria.py → output/campanhas/campanha_diaria.xlsx  │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ABORDAR                                                   │
│    Links de WhatsApp direto → Abordar cliente                 │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. ENVIAR EMAIL                                               │
│    envio_emails_zoho.py → Zoho SMTP + Supabase               │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. TRACKAR                                                   │
│    dashboard-emails.html → Métricas de abertura              │
└─────────────────────────────────────────────────────────────┘
```

---

## O que é vendido

O produto final são **landing pages profissionais** para negócios locais:

| Nicho | Produto |
|-------|---------|
| Barbearia | Página de Agendamento |
| Salão de Beleza | Página de Agendamento |
| Estética | Página de Agendamento |
| Restaurante | Cardápio Digital |
| Pizzaria | Cardápio Digital |
| Lanchonete | Cardápio Digital |
| Igreja | Página de Evento |
| Advogado | Mini Site Profissional |
| Eletricista | Mini Site Profissional |
| E outros... | Mini Site Vendedor |

---

## Tecnologias

- **Python 3** - Scripts principais
- **Playwright** - Web scraping do Google Maps
- **openpyxl** - Geração de planilhas Excel
- **Zoho SMTP** - Envio de emails
- **Supabase** - Banco de dados e tracking
- **HTML/CSS/JS** - Dashboards

---

## Como começar

### 1. Instalar dependências
```bash
pip install playwright openpyxl python-dotenv supabase
playwright install chromium
```

### 2. Executar o funil
```bash
# Passo 1: Mapear comércios
python mapear_comercios.py

# Passo 2: Qualificar leads
python prospectar_leads.py

# Passo 3: Gerar campanha diária
python campanha_diaria.py

# Passo 4: Abordar via WhatsApp (links gerados na planilha)
```

### 3. Dashboard local
```bash
cd frontend
python server.py
# Abre http://localhost:8000/dashboard.html
```

---

## Estrutura de Dados

### CSV de mapeamento (mapear_comercios.py)
| Campo | Descrição |
|-------|-----------|
| nome | Nome do estabelecimento |
| endereco | Endereço completo |
| telefone | Telefone |
| whatsapp | WhatsApp (quando disponível) |
| instagram | Perfil do Instagram |
| email | Email (quando disponível) |
| categoria | Tipo de comércio |
| tem_site | Boolean |
| url_site | URL do site |
| avaliacao | Nota no Google (0-5) |
| num_avaliacoes | Quantidade de avaliações |
| cidade | Cidade |
| bairro | Bairro |
| link_maps | Link do Google Maps |

### Excel de prospecção (prospectar_leads.py)
| Campo | Descrição |
|-------|-----------|
| Prioridade | Alta / Média / Baixa |
| Score | Pontuação (0-100) |
| Nome | Nome do negócio |
| Nicho | Categoria |
| Cidade | Cidade |
| Telefone | Telefone |
| WhatsApp | WhatsApp |
| Site | Sim/Não |
| URL Site | Link do site |
| Nota | Avaliação Google |
| Oferta Sugerida | Produto a oferecer |
| Mensagem WhatsApp | Mensagem personalizada |
| Link WhatsApp | Link direto |

---

## Métricas de Score

O score (0-100) é calculado assim:

| Critério | Pontuação |
|----------|-----------|
| Não tem site | +30 |
| Tem telefone ou WhatsApp | +20 |
| Nota >= 4.0 no Google | +15 |
| 20+ avaliações | +15 |
| Tem Instagram | +10 |
| Nicho bom para landing page | +10 |
| Franquia grande | -30 |
| Já tem site profissional | -20 |

---

## Status dos Leads

| Status | Significado |
|--------|-------------|
| novo | Lead recém-importado |
| abordado | Já entrou em contato |
| interessado | Demonstrou interesse |
| convertido | Virou cliente |
| perdido | Não houve interesse |

---

## FAQ

**P: Precisa de API key do Google?**
R: Não. O scraper usa Playwright para navegar no Google Maps diretamente.

**P: Quantos leads posso mapear por vez?**
R: O script busca 20 resultados por categoria/cidade, com pausas entre requisições para evitar bloqueios.

**P: Posso adicionar novas categorias?**
R: Sim. Edite a lista `CATEGORIAS` no `mapear_comercios.py`.

**P: O script respeita a LGPD?**
R: O script coleta apenas dados públicos do Google Maps (nome, endereço, telefone). Use com responsabilidade.

---

## Autor

Vanderson Avellar - Prospecção B2B na Baixada Fluminense, RJ