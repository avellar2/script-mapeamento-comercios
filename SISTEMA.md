# Sistema de Prospecção B2B — Mapeamento de Comércios

Sistema completo de geração e abordagem de leads B2B para venda de landing pages, mini sites e cardápios digitais (produto **AVGESTÃO**) para comércios locais da **Baixada Fluminense, RJ** e região Premium do Rio de Janeiro.

---

## Visão Geral

O sistema automatiza o funil completo de prospecção B2B:

```
MAPEAR → QUALIFICAR → IMPORTAR → ABORDAR (WhatsApp) → ENVIAR (EMAIL) → TRACKAR
```

| Etapa | O que faz | Script principal |
|-------|-----------|------------------|
| 1. Mapear | Raspa Google Maps em 11 cidades × 40+ categorias | `mapear_comercios.py` |
| 2. Qualificar | Pontua leads (0-100), gera oferta e mensagem por nicho | `prospectar_leads.py` |
| 3. Importar | Envia leads qualificados para o Supabase | `import_leads_to_supabase.py` |
| 4. Abordar | Envio automático de WhatsApp Business com mensagens por nicho | `enviar_auto_avgestao.py` |
| 5. Enviar email | Campanhas via Zoho SMTP com tracking pixel | `envio_emails_zoho.py` |
| 6. Trackar | Dashboard com aberturas, status e KPIs | `frontend/dashboard-emails.html` |

---

## Funcionalidades Principais

### 1. Mapeamento de Comércios (`mapear_comercios.py`)
Scraping do Google Maps com **Playwright** (sem API key).

- **11 cidades** da Baixada Fluminense: Duque de Caxias, Nova Iguaçu, São João de Meriti, Belford Roxo, Nilópolis, Mesquita, Queimados, Itaguaí, Seropédica, Paracambi, Japeri
- **40+ categorias**: restaurante, barbearia, salão de beleza, estética, padaria, pizzaria, lanchonete, confeitaria, oficina mecânica, eletricista, encanador, pintor, serralheria, marcenaria, vidraçaria, material de construção, loja de móveis, loja de celulares, ótica, academia, pilates, dentista, pet shop, etc.
- **Dados coletados**: nome, endereço, bairro, cidade, telefone, WhatsApp, Instagram, email, site, nota Google, número de avaliações, link do Maps
- **Resume automático**: salva progresso em `progresso.json` para retomar do ponto de parada
- **Anti-duplicação**: ignora comércios já coletados (mesmo nome + cidade)
- **Pausas aleatórias** (2-5s) para evitar bloqueio

**Saídas:**
- `output/playwright/todos_comercios.csv` — todos os comércios
- `output/playwright/leads_sem_site.csv` — apenas leads sem site (foco comercial)

### 2. Qualificação de Leads (`prospectar_leads.py`)
Lê o CSV do mapeamento e gera planilha Excel qualificada.

**Sistema de pontuação (0-100):**
| Critério | Pontos |
|----------|--------|
| Não tem site | +30 |
| Tem telefone ou WhatsApp | +20 |
| Nota ≥ 4.0 no Google | +15 |
| 20+ avaliações | +15 |
| Tem Instagram | +10 |
| Nicho bom para landing page | +10 |
| É franquia grande | -30 |
| Tem site profissional | -20 |

**Prioridades:**
- 🟢 **Alta** (score ≥ 70) — abordar primeiro
- 🟡 **Média** (40-69) — abordar depois
- 🔴 **Baixa** (< 40) — baixa prioridade

**Ofertas sugeridas por nicho:**
| Nicho | Produto |
|-------|---------|
| Barbearia, Salão, Estética | Página de Agendamento |
| Restaurante, Pizzaria, Lanchonete, Padaria | Cardápio Digital |
| Igreja, Evento | Página de Evento |
| Advogado, Contador, Eletricista | Mini Site Profissional |
| Outros | Mini Site Vendedor |

**Saídas:**
- `output/prospeccao/leads_prospeccao.xlsx`
  - Aba **Leads**: todos os leads ordenados por score, com cor por prioridade
  - Aba **Resumo**: estatísticas por cidade, nicho e oferta

### 3. Campanha Diária (`campanha_diaria.py`)
Gera planilha filtrada para abordagem do dia.

**Filtros automáticos:**
- Prioridade Alta
- Score ≥ 70
- Tem telefone ou WhatsApp
- Sem site profissional
- Nicho bom para landing page

**Abas:**
| Aba | Conteúdo |
|-----|----------|
| Top 50 | 50 melhores leads por score |
| Estética | Salões, clínicas, manicure |
| Barbearia | Barbearias e salões masculinos |
| Comida-Cardápio | Restaurantes, pizzarias, lanchonetes |
| Serviços Locais | Assistência técnica, eletricista, encanador |
| Outros | Demais nichos |
| Resumo | Estatísticas por nicho e oferta |

**Colunas extras:** Ação Recomendada, Tipo de Material (demo), Status, Data Abordagem, Data Follow-up (7 dias), Observações.

**Saída:** `output/campanhas/campanha_diaria_YYYY-MM-DD.xlsx`

### 4. Busca de Emails (`buscar_emails_playwright.py`, `buscar_emails_cnpj.py`, `capturar_emails.py`)
Busca emails comerciais via:
- Consulta de CNPJ em sites públicos
- Web scraping com Playwright
- APIs de consulta

### 5. Importação para Supabase (`import_leads_to_supabase.py`)
Sobe leads qualificados da planilha Excel para a tabela `leads` no Supabase (fonte da verdade para status e histórico).

- Deduplicação por `telefone_normalizado`
- Importa também histórico WhatsApp via `importar_historico_whatsapp.py`
- Marca lead como enviado via `marcar_lead_enviado.py`

### 6. Envio Automático WhatsApp Business (`enviar_auto_avgestao.py`) ⭐
**Script principal de abordagem automática.**

- Abre o Chrome **já logado** no WhatsApp Business (perfil isolado em `.whatsapp_business_profile`)
- **Lock de instância única** via PID file (`.enviar_auto.pid`) — aborta se já houver outra instância rodando
- Usa **Chrome instalado** (`channel="chrome"`) para evitar incompatibilidade de versão
- Navegador **único** mantido aberto durante toda a sessão (não abre/fecha a cada lead)
- `headless=False` — navegador visível de propósito

**Configuração de envio:**
| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `ENVIAR_HOJE` | 30 | Mensagens por sessão |
| `INTERVALO_SEG` | 420 | 7 min entre cada envio |
| `BLOCO_TAMANHO` | 10 | Tamanho do bloco |
| `PAUSA_BLOCO_SEG` | 3600 | 1h de pausa entre blocos |

**Busca unificada de leads (nicho OU categoria):**
A query no Supabase usa `or=(categoria.ilike.*{cat}*,nicho.ilike.*{cat}*)` para capturar leads onde a informação esteja em qualquer um dos dois campos (muitos leads têm `nicho` vazio mas `categoria` preenchida, e vice-versa). Deduplicação por `id` para evitar repetidos.

**Mensagens por nicho (9 funções dedicadas):**
| Função | Nichos cobertos |
|--------|-----------------|
| `msg_oficina` | Oficina mecânica |
| `msg_producao` | Serralheria, marcenaria |
| `msg_prestador` | Eletricista, pintor, encanador, fallback |
| `msg_assistencia` | Loja de celulares |
| `msg_material_construcao` | Material de construção |
| `msg_moveis` | Loja de móveis |
| `msg_vidracaria` | Vidraçaria |
| `msg_cardapio` | Restaurante, pizzaria, lanchonete, confeitaria, padaria |
| `msg_otica` | Ótica |

A função `_escolher_msg(lead)` pega `categoria` (prioridade) ou `nicho`, normaliza, tenta match exato no `CAT_MAP`, depois match por substring, e fallback `msg_prestador`.

**Fluxo por lead:**
1. Valida se é celular (DDD 21 com 9º dígito) — se for fixo, marca como `perdido` e pula
2. Escolhe mensagem via `_escolher_msg(lead)`
3. Abre `https://web.whatsapp.com/send?phone={tel}&text={msg}`
4. Se aparecer QR Code, espera até 4 min pelo escaneamento (avisa o Vanderson)
5. Detecta número inválido → marca como `perdido`
6. Aguarda campo de texto, clica em Enviar ou pressiona Enter
7. Marca lead como `abordado` no Supabase com `proximo_followup_em` em 3 dias

### 7. Envio de Emails (`envio_emails_zoho.py`)
Campanhas de email via **Zoho Mail SMTP**.

- **41 templates HTML** por categoria em `templates/` com copy de dor + upsell
- **Tracking pixel** (1x1 PNG invisível) com ID único por envio
- Salva cada envio no Supabase (tabela `emails_enviados`)
- Controle de volume e horário (9h-18h, seg-sex)
- Pausas aleatórias entre envios
- Resume automático em `output/envios/progresso_envio.json`

### 8. Tracking de Aberturas (`supabase_edge_function_track.ts`)
Edge Function no Supabase que:
- Recebe requisição do pixel com `?id=XXX`
- Marca `email_aberto=true`, `data_abertura=now()`, incrementa `qtd_aberturas`
- Retorna o PNG 1x1 transparente imediatamente (não bloqueia)
- **Taxa esperada:** 60-80% (Gmail app bloqueia imagens por padrão)

### 9. Dashboard Frontend (`frontend/`)
Dois dashboards:

**`dashboard.html`** — Comércios mapeados
- Total de comércios, com/sem site, cidades cobertas
- Filtros: nome, cidade, categoria, presença de site
- Cards interativos com hover
- Design responsivo (tema Data Editorial, laranja/âmbar sobre fundo escuro)

**`dashboard-emails.html`** — Envios de email (deployado na Vercel)
- Total de emails enviados
- Taxa de abertura
- Gráficos por categoria
- Filtros: cidade, categoria, status
- Tabela completa com status de cada email

**Servidor local:** `python frontend/server.py` → http://localhost:8000/dashboard.html
**Versão standalone:** `frontend/gerar-standalone.bat` (embute dados no HTML, não precisa de servidor)

### 10. Painel de Prospecção (`gerar_painel_prospeccao.py`, `gerar_relatorio_regional.py`)
Gera painéis web e relatórios regionais para acompanhamento visual da operação.

### 11. Scripts Auxiliares
| Script | Função |
|--------|--------|
| `abrir_whatsapp.py` | Abre WhatsApp Business isolado para uso manual |
| `buscar_leads_apify.py` | Alternativa: busca leads via Apify Actor |
| `processar_leads.py` | Processa leads do Apify → CSV/XLSX |
| `cruzar_leads.py` | Cruza bases de leads (deduplicação avançada) |
| `gerar_lista_diaria.py` | Gera lista diária de abordagem |
| `gerar_templates.py` | Gera 41 templates HTML por categoria |
| `preparar_campanha.py` | Prepara campanha de email |
| `marcar_enviados.py` | Marca leads como enviados no Supabase |
| `extrair_historico_whatsapp.py` | Extrai histórico de conversas do WhatsApp |
| `importar_historico_whatsapp.py` | Importa histórico WhatsApp para o Supabase |
| `import_leads_csv_supabase.py` | Importa leads de CSV para o Supabase |
| `importar_csv_playwright.py` | Importa CSV via Playwright |
| `importar_rio_premium.py` | Importa leads da região Premium do Rio |
| `testar_sistema.py` | Teste geral (env, Supabase, templates) |
| `testar_templates.py` | Teste dos templates gerados |
| `mostrar_msg.py` | Mostra mensagens que serão enviadas |
| `check_model.py` | Verifica modelo LLM em uso |

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3 |
| Scraping | Playwright (Chromium/Chrome) |
| Planilhas | openpyxl |
| Banco de dados | Supabase (PostgreSQL) |
| Email SMTP | Zoho Mail |
| Tracking | Supabase Edge Functions (Deno/TypeScript) |
| Dashboards | HTML + CSS + JS (vanilla) |
| Deploy dashboard | Vercel |
| WhatsApp | Playwright + Chrome (channel=chrome) |

---

## Banco de Dados (Supabase)

### Tabela `leads` (fonte da verdade)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID PK | Identificador único |
| `nome` | TEXT | Nome do comércio |
| `telefone` | TEXT | Telefone bruto |
| `telefone_normalizado` | TEXT UNIQUE | Telefone normalizado (dedup) |
| `whatsapp` | TEXT | WhatsApp separado (quando disponível) |
| `email` | TEXT | Email comercial |
| `categoria` | TEXT | Categoria principal (ex: restaurante) |
| `nicho` | TEXT | Nicho (pode estar vazio em alguns leads) |
| `cidade`, `bairro`, `endereco` | TEXT | Localização |
| `tem_site`, `url_site` | BOOL/TEXT | Presença de site |
| `avaliacao`, `num_avaliacoes` | NUMERIC/INT | Métricas Google |
| `score` | INT | Pontuação 0-100 |
| `prioridade` | TEXT | Alta/Média/Baixa |
| `oferta_sugerida` | TEXT | Produto ideal |
| `mensagem_whatsapp` | TEXT | Mensagem personalizada |
| `link_whatsapp` | TEXT | Link wa.me |
| `status` | TEXT | novo, pronto_para_enviar, abordado, respondeu, follow_up, interessado, convertido, perdido |
| `origem` | TEXT | Origem do lead |
| `ultimo_contato_em` | TIMESTAMPTZ | Última abordagem |
| `proximo_followup_em` | TIMESTAMPTZ | Próximo follow-up |
| `observacoes`, `resposta_cliente` | TEXT | Anotações |
| `created_at`, `updated_at` | TIMESTAMPTZ | Timestamps (trigger automático) |

### Tabela `lead_interactions` (audit trail)
Histórico de todas as interações: `importacao`, `primeira_abordagem`, `follow_up`, `resposta_cliente`, `proposta_enviada`, `convertido`, `perdido`.

### Tabela `campaigns`
Registro de cada importação/campanha (nome, data, nicho, cidade, quantidade).

### Tabela `emails_enviados`
Cada envio de email com `tracking_id` único, `email_aberto`, `data_abertura`, `qtd_aberturas`.

### Tabela `stats_diarias`
Estatísticas agregadas por dia (enviados, abertos, taxa de abertura).

### Views
- `vw_leads_para_abordar` — leads com status `novo` ou `pronto_para_enviar`, ordenados por score
- `vw_followups_hoje` — follow-ups pendentes até hoje
- `vw_leads_resumo_status` — resumo por status
- `vw_stats_gerais` — totais e taxa de abertura
- `vw_por_categoria` — quebra por categoria
- `vw_reenvio_sugerido` — emails não abertos há 7+ dias

### RLS (Row Level Security)
- `leads`, `lead_interactions`, `campaigns`: SELECT/INSERT/UPDATE para anon (sem DELETE — proteção contra exclusão acidental)

---

## Status dos Leads

| Status | Significado |
|--------|-------------|
| `novo` | Lead recém-importado, ainda não abordado |
| `pronto_para_enviar` | Pronto para abordagem automática |
| `abordado` | Primeira mensagem enviada |
| `respondeu` | Cliente respondeu |
| `follow_up` | Segunda abordagem |
| `interessado` | Demonstrou interesse |
| `convertido` | Virou cliente |
| `perdido` | Não fechou / telefone fixo / número inválido |

---

## Variáveis de Ambiente (`.env`)

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

---

## URLs Importantes

- **Dashboard de emails (Vercel):** https://frontend-j67aarixx-vandersonavellar1997-1683s-projects.vercel.app
- **Supabase Dashboard:** https://supabase.com/dashboard/project/ivqaccppqcchqshaplao
- **Tracking pixel:** https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id=XXX

---

## Rotina Diária Recomendada

1. **Mapear** (se necessário): `python mapear_comercios.py`
2. **Qualificar**: `python prospectar_leads.py`
3. **Gerar campanha**: `python campanha_diaria.py`
4. **Importar para Supabase**: `python import_leads_to_supabase.py`
5. **Envio automático WhatsApp**: `python enviar_auto_avgestao.py`
   - Se aparecer QR Code, escanear no celular
   - 30 mensagens/dia com 7 min de intervalo + 1h de pausa a cada 10
6. **Acompanhar dashboard**: Vercel ou local
7. **Follow-up**: 3 dias após abordagem, conferir `vw_followups_hoje`

---

## Convenções do Projeto

- **Lock de instância única** em scripts de envio (`.enviar_auto.pid`) — nunca rodar duas instâncias ao mesmo tempo
- **Perfil Chrome isolado** em `.whatsapp_business_profile/` (separado do Chrome pessoal)
- **Navegador visível** (`headless=False`) — proposital para acompanhamento
- **Não alterar** `ENVIAR_HOJE`, `INTERVALO_SEG`, `BLOCO_TAMANHO`, `PAUSA_BLOCO_SEG` sem ordem explícita
- **Supabase é a fonte da verdade** — sempre consultar antes de abordar para não duplicar
- **Deduplicação** por `telefone_normalizado` (UNIQUE no banco)
- **Commits**: nunca incluir menção a Claude/Anthropic/"Co-Authored-By: Claude"

---

## Autor

Vanderson Avellar — Prospecção B2B na Baixada Fluminense, RJ.
Produto: **AVGESTÃO** (landing pages, mini sites, cardápios digitais, ordem de serviço).
