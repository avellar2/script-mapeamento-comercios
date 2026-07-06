# Templates de Mensagem, Schema do Banco e Instruções de Importação

## Templates por Nicho (mensagens melhoradas — curtas, humanas, consultivas)

### Estética / Salão de Beleza (sem nota alta)
> Oi, tudo bem? Vi o [Nome] no Google e pensei comigo: um salão com esse trabalho merece uma página bonita com agendamento direto pelo WhatsApp. Posso te mostrar como ficaria? É rapidinho.

### Estética / Salão (com nota alta ≥ 4.5 e 20+ avaliações)
> Oi! Vi o [Nome] no Google, viu? [nota] estrelas com [qtd] avaliações, isso é muito bom. Queria te mostrar rapidinho como fica uma página de agendamento pro seu salão — com WhatsApp direto, serviços e localização. Posso mandar uma prévia?

### Barbearia (com nota alta)
> Oi! Vi a [Nome] no Google — [nota] estrelas, [qtd] avaliações. Cara, imagine só o cliente te achando no Google e agendando o corte direto pelo WhatsApp, sem precisar ligar. Posso te mandar como ficaria a página?

### Barbearia (geral)
> Oi, tudo bem? Vi a [Nome] e pensei: uma página de agendamento com os cortes, horário e WhatsApp direto facilitaria muito pro cliente. Quer ver como ficaria?

### Comida / Cardápio (com nota alta)
> Oi! Com [nota] estrelas e [qtd] avaliações, o [Nome] já é destaque na região. Imagine o cliente abrindo um cardápio digital bonitão e pedindo direto pelo WhatsApp. Posso te mostrar como fica?

### Comida / Restaurante (geral)
> Oi, tudo bem? Vi o [Nome] no Google. Um cardápio digital com as fotos dos pratos e o botão de pedido direto no WhatsApp faz o cliente pedir sem ficar perguntando tudo. Quer ver como ficaria?

### Dentista / Clínica Médica
> Olá, tudo bem? Vi a [Nome] e notei que uma página profissional com os tratamentos, fotos da clínica e agendamento pelo WhatsApp transmitiria mais confiança pra quem procura. Posso mostrar como ficaria?

### Advocacia
> Olá! Vi o escritório e pensei: uma página institucional organizada com as áreas de atuação e WhatsApp direto transmite mais credibilidade pra quem está buscando orientação. Posso te mandar uma prévia?

### Serviços Técnicos
> Oi, tudo bem? Vi o [Nome] no Google. Quando alguém precisa de um serviço com urgência, quer encontrar rápido — serviços, região atendida e botão de orçamento no WhatsApp. Posso te mostrar como ficaria uma página assim?

### Geral (fallback)
> Oi, tudo bem? Vi o [Nome] no Google e percebi que uma página simples com informações claras e WhatsApp direto facilitaria pra quem te procura. Quer ver como ficaria?

## Follow-up — Mensagens por Dia

### Dia 2-3 (leve)
> Oi! Tentei te contatar sobre o [Nome]. Sem pressa, mas se tiver curiosidade pra ver como ficaria uma página digital, é só me chamar. 👋

### Dia 7 (com valor)
> Oi [Nome]! Vi que [insight sobre o nicho — ex: "5 de cada 10 clientes pesquisam no Google antes de agendar"]. Posso te mostrar como ficaria uma página pro [Nome]? Só 2 minutinhos 😊

### Dia 14 (última tentativa)
> Oi! Última tentativa rs. Posso montar uma prévia da página do [Nome] sem compromisso. Se não for o momento, tudo bem. Abraço!

## Schema do Banco — Supabase (FONT OFICIAL)

### Tabela `leads`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | uuid | PK automático |
| nome | text | Nome do negócio |
| telefone | text | Telefone bruto |
| whatsapp | text | WhatsApp bruto |
| telefone_normalizado | text | Telefone formato 5521XXXXXXXXX (dedup key) |
| instagram | text | Instagram do negócio |
| email | text | Email de contato |
| categoria | text | Categoria/nicho |
| nicho | text | Nicho (sinônimo de categoria) |
| cidade | text | Cidade |
| bairro | text | Bairro |
| endereco | text | Endereço completo |
| tem_site | boolean | Tem site próprio? |
| url_site | text | URL do site |
| avaliacao | float | Nota Google |
| num_avaliacoes | integer | Qtd avaliações Google |
| score | integer | Score de prioridade |
| prioridade | text | Prioridade textual |
| oferta_sugerida | text | Oferta recomendada |
| mensagem_whatsapp | text | Mensagem gerada |
| link_whatsapp | text | Link wa.me gerado |
| status | text | Funil: novo/abordado/respondes/follow_up/interessado/convertido/perdido |
| origem | text | Origem do lead |
| ultimo_contato_em | timestamp | Último contato |
| proximo_followup_em | timestamp | Próximo follow-up |
| observacoes | text | Observações gerais |
| criado_em | timestamp | Data de criação |

### Tabela `lead_interactions`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | uuid | PK |
| lead_id | uuid | FK para leads |
| tipo | text | Tipo da interação (primeira_abordagem, importacao, etc.) |
| canal | text | Canal (whatsapp, email, planilha) |
| mensagem | text | Mensagem enviada |
| observacao | text | Observação |

### Tabela `campaigns`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | uuid | PK |
| nome | text | Nome da campanha |
| data | date | Data |
| quantidade_leads | integer | Qtd leads |
| observacao | text | Info adicional |

### View `vw_leads_para_abordar`
Leads com status `novo` ou `pronto_para_enviar` — estes são os que devem ser abordados.

## Status Canônicos e Proteção

| Status | Pode ser abordado? | Pode regredir? |
|--------|-------------------|----------------|
| novo | ✅ Sim | — |
| pronto_para_enviar | ✅ Sim | Pode voltar para novo |
| abordado | ❌ Não | Não regredir |
| respondeu | ❌ Não | Não regredir |
| follow_up | ❌ Não | Não regredir |
| interessado | ❌ Não | Não regredir |
| convertido | ❌ Não | NUNCA regredir |
| perdido | ❌ Não | NUNCA regredir |

## Extração de Primeiro Nome para Saudação

Ao gerar mensagens WhatsApp, usar o **primeiro nome da pessoa** (não o nome do negócio). Regras:

1. **Dicionário de nomes conhecidos** — nomes compostos/ambíguos que exigem mapeamento manual:
   - "Centro de beleza Clarice Mendonça" → "Clarice"
   - "Estética Andressa Santos" → "Andressa"
   - "Espaço Estética, Saúde e Bem-Estar RM" → "RM"
   - "Clínica Médica Roseira" → "Roseira"
   - "Clínica Dr. João da Luz" → "Dr. João"
   - "Studio Pilates Raquel Corrêa" → "Raquel"
   - "Clear Dent - Odontopediatria..." → "Clear Dent"
   - "Odonto Best Nilópolis" → "Odonto Best"

2. **Prefixos a remover** (em ordem de tamanho, do maior pro menor):
   - Centro de beleza, Centro de, Centro, Espaço, Studio de, Studio, Salão de, Salão, Clínica de, Clínica, Policlínica, Padaria e Confeitaria, Padaria e, Padaria

3. **Palavras proibidas como primeiro nome** (nunca usar como saudação):
   - Artigos/preposições: de, do, da, dos, das, e, em, no, na
   - Genéricas: estética, beleza, pilates, barber, barbearia, clínica, centro

4. **Fallback**: se não encontrar nome próprio, usar saudação sem nome ("Oi, tudo bem?")

## Scripts de Importação — Comandos

### Extrair histórico do WhatsApp
```bash
cd /c/projetos/script-mapear-comércios
/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe extrair_historico_whatsapp.py --limite 200
```
- Abre Chromium com Playwright — precisa escanear QR Code na primeira vez
- Perfil salvo em `.whatsapp_profile/`
- Output: `output/whatsapp/historico_whatsapp.csv`
- **NÃO importa automaticamente** — precisa de autorização

### Importar histórico para o Supabase
```bash
/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe importar_historico_whatsapp.py --arquivo output/whatsapp/historico_whatsapp.csv
```
- Lê CSV com colunas: telefone, status, observacao
- Marca leads existentes como `abordado`
- Cria leads mínimos para telefones não encontrados
- NUNCA regredir status `convertido` ou `perdido`

### Importar planilha para o Supabase
```bash
/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe import_leads_to_supabase.py
```
- Lê `output/campanhas/campanha_diaria.xlsx` ou `output/prospeccao/leads_prospeccao.xlsx`
- Deduplica por `telefone_normalizado`
- Preserva status protegidos (abordado, respondeu, etc.)

### Preparar campanha diária
```bash
/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe preparar_campanha.py
```
- Busca leads com status `novo` e `tem_site=false` no Supabase
- Score composto = score_base + (prioridade_nicho × 5) + (prioridade_cidade × 3)
- Diversifica: máx 2 por nicho, máx 5 por cidade
- Gera mensagens curtas e humanas específicas por nicho
- Extrai primeiro nome da pessoa (não do negócio)
- Gera links wa.me com mensagem pré-preenchida
- Output: `output/painel/campanha_YYYY-MM-DD.json` e `.txt`
- **NÃO altera status** — apenas prepara a lista para revisão manual

### Marcar lead como enviado (individual)
```bash
/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe marcar_lead_enviado.py --telefone 21999999999 --mensagem "mensagem enviada"
```
- Busca lead por telefone normalizado
- Marca como `abordado` + follow-up em 7 dias
- Cria interação no Supabase

## Schema do Banco — SQLite (painel local)

Tabela `leads` no `output/painel/prospeccao.db` — mesma estrutura mas com campos adicionais:
- `lead_id` (PK), `rodada`, `mensagem_whatsapp`, `link_whatsapp`, `followup_mensagem`, `numero_formatado`, `resposta_cliente`, `proximo_followup`

**Nota**: SQLite é apenas para o painel local. Supabase é a fonte oficial.