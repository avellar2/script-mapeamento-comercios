# Mapeador de Comércios - Baixada Fluminense, RJ

Sistema completo de geração de leads B2B para venda de landing pages, mini sites e cardápios digitais. Mapeia comércios locais, qualifica leads com pontuação inteligente e gera planilha pronta para abordagem pelo WhatsApp.

## Visão Geral

O projeto automatiza todo o funil de prospecção:

1. **Mapeamento** — Raspa o Google Maps com Playwright em 11 cidades x 40+ categorias, coletando telefone, WhatsApp, Instagram, nota, avaliações e mais
2. **Captura de emails** — Busca emails via consulta de CNPJ em sites públicos + web scraping
3. **Prospecção** — Pontua leads de 0 a 100, classifica prioridade, sugere oferta e gera mensagem personalizada de WhatsApp
4. **Templates** — Gera emails HTML personalizados por categoria com copy de dor/upsell
5. **Envio** — Dispara emails via SMTP do Zoho Mail com controle de volume e horário
6. **Tracking** — Tracking pixel (1x1 PNG) via Supabase Edge Function registra aberturas
7. **Dashboard** — Frontend com KPIs, gráficos e tabela paginada dos envios

## Estrutura do Projeto

```
.
├── mapear_comercios.py          # Scraping Google Maps com Playwright
├── prospectar_leads.py          # Pontuação, prioridade e planilha de prospecção
├── campanha_diaria.py           # 🔥 NOVO - Campanha diária de abordagem WhatsApp
├── buscar_emails_playwright.py  # Busca emails via CNPJ no Google + APIs
├── buscar_emails_cnpj.py        # Busca emails usando sites de consulta CNPJ
├── capturar_emails.py           # Captura email CNPJ + email comercial
├── buscar_leads_apify.py        # Alternativa: busca leads via Apify Actor
├── processar_leads.py           # Processa leads do Apify -> CSV/XLSX
├── gerar_templates.py           # Gera 40+ templates HTML por categoria
├── envio_emails_zoho.py         # Envia campanhas via Zoho Mail SMTP
├── testar_sistema.py            # Teste geral (env, Supabase, templates)
├── testar_templates.py          # Teste dos templates gerados
├── teste_email_supabase.py      # Teste de integração email + Supabase
├── executar.bat                 # Setup + execução com 1 clique (Windows)
├── requirements.txt             # Dependências Python
├── supabase_schema.sql          # Schema do banco Supabase
├── supabase_edge_function_track.ts  # Edge Function de tracking pixel
│
├── templates/                   # 41 templates HTML de email por categoria
├── frontend/                    # Dashboards HTML + servidor local
│
├── output/                      # Dados gerados
│   ├── playwright/              # Resultados do scraping Playwright
│   │   ├── todos_comercios.csv
│   │   └── leads_sem_site.csv
│   ├── apify/                   # Resultados do Apify
│   ├── envios/                  # Logs e progresso de envios
│   ├── consolidado/             # Base consolidada de emails
│   ├── prospeccao/              # Planilhas de prospecção
│   │   └── leads_prospeccao.xlsx
│   └── campanhas/               # 🔥 NOVO - Campanhas diárias
│       └── campanha_diaria.xlsx
│
├── docs/                        # Documentação e planejamento
└── .env                         # Credenciais (Zoho SMTP, Supabase)
```

## Instalação

### Windows (recomendado)

```bat
executar.bat
```

Instala dependências, baixa Chromium e executa o mapeamento.

### Manual

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Dependências adicionais (para envio de emails):

```bash
pip install supabase python-dotenv
```

## Uso

### 1. Mapear comércios

```bash
python mapear_comercios.py
```

Busca comércios no Google Maps e coleta:
- Nome, endereço, bairro, cidade
- Telefone, WhatsApp, Instagram
- Site (se tem e URL)
- Nota no Google, quantidade de avaliações
- Link do Google Maps

Gera `output/playwright/todos_comercios.csv` e `output/playwright/leads_sem_site.csv`.

### 2. Gerar planilha de prospecção

```bash
python prospectar_leads.py
```

Lê os dados coletados e gera uma planilha Excel com:

| Coluna | Descrição |
|---|---|
| Prioridade | Alta (≥70), Média (40-69), Baixa (<40) |
| Score | Pontuação de 0 a 100 |
| Nome | Nome do comércio |
| Nicho | Categoria do comércio |
| Cidade | Cidade |
| Bairro | Bairro extraído do endereço |
| Telefone | Telefone |
| WhatsApp | WhatsApp (se disponível) |
| Instagram | Instagram (se disponível) |
| Site | Se tem site |
| URL Site | URL do site |
| Nota | Nota no Google |
| Avaliações | Quantidade de avaliações |
| Endereço | Endereço completo |
| Link Maps | Link do Google Maps |
| Oferta Sugerida | Produto ideal para o lead |
| Motivo Prioridade | Por que o lead é bom ou ruim |
| Mensagem WhatsApp | Texto personalizado para abordagem |
| Link WhatsApp | Link wa.me clicável com mensagem |
| Email | Email encontrado |

**Opções:**

```bash
# Usar arquivo específico
python prospectar_leads.py --arquivo output/playwright/leads_sem_site.csv

# Nome do arquivo de saída
python prospectar_leads.py --saida meus_leads.xlsx
```

O script busca automaticamente os dados na ordem:
1. `output/consolidado/base_emails_consolidada.csv`
2. `output/consolidado/base_emails_pronta_contato_refinada.csv`
3. `output/playwright/todos_comercios.csv`

### 3. Interpretar a planilha

A planilha tem duas abas:

**Aba Leads** — Todos os leads ordenados por score (maior primeiro), com filtros ativos.

Cores por prioridade:
- 🟢 Verde = Alta (score ≥ 70) — Abordar primeiro
- 🟡 Amarelo = Média (score 40-69) — Abordar depois
- 🔴 Vermelho = Baixa (score < 40) — Baixa prioridade

**Aba Resumo** — Estatísticas gerais, por cidade, por nicho e por oferta sugerida.

### 4. Sistema de Pontuação

| Critério | Pontos |
|---|---|
| Não tem site | +30 |
| Tem telefone ou WhatsApp | +20 |
| Nota ≥ 4.0 no Google | +15 |
| Mais de 20 avaliações | +15 |
| Tem Instagram | +10 |
| Nicho bom para landing page | +10 |
| É franquia grande | -30 |
| Tem site profissional | -20 |

Score máximo: 100. Score mínimo: 0.

### 5. Oferta sugerida por nicho

| Nicho | Oferta |
|---|---|
| Barbearia, Salão de Beleza, Estética, Manicure | Página de Agendamento |
| Restaurante, Pizzaria, Marmitaria, Açaí, Lanchonete | Cardápio Digital |
| Igreja, Evento | Página de Evento |
| Advogado, Contador, Eletricista, Autônomo | Mini Site Profissional |
| Outros | Mini Site Vendedor |

### 6. Mensagem de WhatsApp

Cada lead recebe uma mensagem personalizada. Exemplo:

> Oi, tudo bem? Vi a Barbearia Corte das Estrelas no Google e percebi que vocês têm boas avaliações (4.5 estrelas) mas ainda não encontrei uma página simples com serviços, fotos, localização e botão direto para WhatsApp. Quando o cliente precisa procurar muito essas informações, ele pode acabar chamando outro lugar. Eu crio páginas de agendamento profissionais para negócios locais. Posso te mandar uma prévia visual de como ficaria?

A coluna **Link WhatsApp** contém um link `wa.me` clicável com a mensagem já preenchida — basta clicar para abrir o WhatsApp.

### 7. Gerar campanha diária

```bash
python campanha_diaria.py
```

Lê `output/prospeccao/leads_prospeccao.xlsx` e gera uma planilha filtrada com os melhores leads para abordar no dia.

**Filtros automáticos:**
- Prioridade Alta
- Score ≥ 70
- Tem telefone ou WhatsApp
- Sem site profissional
- Nicho bom para landing page

**Abas da planilha:**

| Aba | Conteúdo |
|---|---|
| Top 50 | Os 50 melhores leads ordenados por score |
| Estética | Salões, clínicas, manicure, sobrancelha |
| Barbearia | Barbearias e salões masculinos |
| Comida-Cardápio | Restaurantes, pizzarias, lanchonetes |
| Serviços Locais | Assistência técnica, eletricista, encanador |
| Outros | Demais nichos |
| Resumo | Estatísticas por nicho, oferta e tipo de material |

**Colunas extras por lead:**

| Coluna | Descrição |
|---|---|
| Ação Recomendada | O que fazer com o lead |
| Tipo de Material | Vídeo/print de demo para enviar |
| Status | novo / contatado / respondido / agendado / fechado / perdido |
| Data Abordagem | Preencher quando abordar |
| Data Follow-up | 2 dias depois da data atual |
| Observações | Anotações livres |

**Ação recomendada por prioridade:**
- Alta sem site → "Criar prévia visual e abordar pelo WhatsApp"
- Alta com site ruim → "Oferecer melhoria da página atual"
- Média → "Enviar modelo do nicho e testar interesse"
- Baixa → "Não abordar agora"

**Tipo de material por nicho:**
- Estética → Vídeo curto da demo de estética
- Barbearia → Vídeo curto da demo de barbearia
- Comida → Vídeo curto do cardápio digital
- Assistência técnica → Print ou vídeo de mini site profissional
- Igreja/Evento → Print ou vídeo de página para evento
- Outros → Print do mini site vendedor

**Mensagens WhatsApp por nicho:**

As mensagens são diferentes para cada tipo de nicho:
- Estética: foca em agendamento
- Barbearia: foca em agendamento de corte
- Comida: foca em cardápio digital e pedido pelo WhatsApp
- Assistência técnica: foca em orçamento pelo WhatsApp
- Igreja/Evento: foca em página para divulgar evento e inscrição

**Opções:**

```bash
# Usar arquivo específico
python campanha_diaria.py --arquivo output/prospeccao/meus_leads.xlsx

# Quantidade de leads no Top 50 (padrão: 50)
python campanha_diaria.py --top 30

# Marcar data de hoje na coluna Data Abordagem
python campanha_diaria.py --hoje
```

Output: `output/campanhas/campanha_diaria.xlsx` e `output/campanhas/campanha_diaria_YYYY-MM-DD.xlsx`

### 8. Rotina diária de abordagem

Recomenda-se abordar **10 leads por dia** seguindo este processo:

1. Execute `python campanha_diaria.py` para gerar a planilha do dia
2. Abra `output/campanhas/campanha_diaria.xlsx`
3. Vá para a aba **Top 50** (ou a aba do nicho que prefere)
4. Selecione 10 leads para abordar
5. Para cada lead:
   - Clique no **Link WhatsApp** na coluna correspondente
   - O WhatsApp abre com a mensagem já preenchida
   - Envie a mensagem personalizada
   - Anote a data na coluna **Data Abordagem**
   - Altere o **Status** de "novo" para "contatado"
6. Dois dias depois (data na coluna **Data Follow-up**):
   - Se respondeu → marcar Status como "respondido"
   - Se não respondeu → mandar follow-up e marcar Status como "follow-up"
7. Quando fechar → marcar Status como "fechado"

**Status disponíveis:**

| Status | Significado |
|---|---|
| novo | Ainda não abordado |
| contatado | Mensagem enviada |
| respondido | Respondeu à mensagem |
| follow-up | Segunda abordagem |
| agendado | Reunião/call agendado |
| fechado | Venda concluída |
| perdido | Não fechou |

### 9. Atualizar status manualmente

O status dos leads é atualizado diretamente no Excel. Basta abrir `campanha_diaria.xlsx` e alterar a coluna **Status** conforme o andamento. Não é necessário rodar o script novamente para atualizar status.

Se quiser gerar uma nova campanha com leads atualizados, rode `prospectar_leads.py` novamente primeiro (para atualizar os scores e mensagens) e depois `campanha_diaria.py`.

### 10. Enviar campanha de email

### 7. Buscar emails por CNPJ

```bash
python buscar_emails_playwright.py
```

### 11. Enviar campanha de email

```bash
python envio_emails_zoho.py
```

## Cidades Cobertas

11 cidades da Baixada Fluminense: Duque de Caxias, Nova Iguaçu, São João de Meriti, Belford Roxo, Nilópolis, Mesquita, Queimados, Itaguaí, Seropédica, Paracambi, Japeri.

## 40 Categorias

Restaurante, Salão de Beleza, Barbearia, Clínica Médica, Oficina Mecânica, Pet Shop, Loja de Roupas, Padaria, Pizzaria, Bar, Farmácia, Dentista, Advogado, Contador, Imobiliária, Academia, Lanchonete, Supermercado, Material de Construção, Auto Escola, Lavanderia, Floricultura, Ótica, Joalheria, Clínica Veterinária, Estética, Loja de Celulares, Loja de Móveis, Papelaria, Loja de Bicicleta, Confeitaria, Serralheria, Vidraçaria, Pintor, Eletricista, Encanador, Marcenaria, Escola de Idiomas, Curso Pré-Vestibular, Estúdio de Pilates.

## Troubleshooting

**Playwright falha:** Roda `python -m playwright install chromium` novamente. Verifica se o antivírus está bloqueando.

**Script não encontra dados:** Executa `mapear_comercios.py` primeiro para gerar os CSVs.

**Excel não abre:** Instala `openpyxl` com `pip install openpyxl`.

**WhatsApp link não funciona:** Verifica se o telefone está no formato correto (código do país + DDD + número).

## Variáveis de Ambiente (.env)

```env
# Zoho Mail SMTP
ZOHO_SMTP_HOST=smtppro.zoho.com
ZOHO_SMTP_PORT=465
ZOHO_SMTP_USER=contato@seudominio.com
ZOHO_SMTP_APP_PASSWORD=sua_app_password

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_anon_key
```