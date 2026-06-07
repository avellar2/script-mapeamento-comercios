# Plano Operacional Diário — Venda de Landing Pages

## Rotina Completa do Prospecador

> **Meta:** 10-20 leads abordados/dia → 3-8% conversão → 2-5 vendas/semana
> **Foco:** Baixada Fluminense — 11 cidades, 40 nichos, 4.372 leads sem site

---

## RESUMO RÁPIDO (Colar no mural)

| Hora | Ação | Script / Ferramenta |
|------|-------|---------------------|
| 08:30 | Gerar campanha do dia | `python gerar_painel_prospeccao.py` |
| 09:00 | Abordar leads no WhatsApp | Painel → clicar "Abrir WhatsApp" |
| 11:30 | Follow-up dos leads de 7 dias atrás | Filtrar "Follow-up" no painel |
| 13:00 | Verificar respostas e atualizar status | Painel → botões de status |
| 14:00 | Follow-up dos leads de 5 dias atrás | Filtrar "Follow-up" no painel |
| 15:00 | Enviar emails pros leads com email | `python envio_emails_zoho.py` |
| 16:00 | Atualizar campanha e revisar métricas | Painel → anotar no controle |
| 17:00 | Planejar leads do dia seguinte | Painel → filtrar "Alta prioridade" |

---

## 1. SCRIPTS QUE DEVO RODAR POR DIA

### Script principal (roda TODO DIA pela manhã)

```bash
python gerar_painel_prospeccao.py
```

**O que faz:**
- Lê `campanha_diaria.xlsx` ou `leads_prospeccao.xlsx`
- Filtra os 20 melhores leads do dia (score ≥ 70, prioridade Alta, sem site, com telefone)
- Gera o painel HTML em `output/painel/index.html`
- Salva status em `output/painel/status_leads.json`
- Ativa o servidor em `localhost:8000`

### Script semanal (roda 1x por semana, segunda-feira)

```bash
python mapear_comercios.py
```

**O que faz:**
- Raspa Google Maps com Playwright
- Atualiza `output/playwright/todos_comercios.csv`
- Atualiza `output/playwright/leads_sem_site.csv`
- **Tempo:** ~2-4h (11 cidades × 40 categorias)

### Script pós-mapeamento (roda depois do mapeamento)

```bash
python prospectar_leads.py
```

**O que faz:**
- Lê CSVs atualizados
- Calcula score de 0-100 para cada lead
- Gera `output/prospeccao/leads_prospeccao.xlsx`

### Script quinzenal (roda a cada 15 dias)

```bash
python campanha_diaria.py
```

**O que faz:**
- Refilha a campanha com leads novos
- Gera `output/campanhas/campanha_diaria.xlsx`
- Cria abas por nicho (Estética, Barbearia, Comida, etc.)

### Script de apoio (roda quando precisar captar emails)

```bash
python buscar_emails_playwright.py
```

**O que faz:**
- Busca emails via CNPJ no Google
- Atualiza `output/consolidado/base_emails_consolidada.csv`

### Script de envio de email (rota diária à tarde)

```bash
python envio_emails_zoho.py
```

**O que faz:**
- Envia emails personalizados por categoria via Zoho SMTP
- Registra tracking pixel no Supabase
- Limite: 250 emails/dia

---

## 2. ORDEM DE EXECUÇÃO

### Manhã (08:30 - 12:00)

```
1. python gerar_painel_prospeccao.py     → Gera o painel do dia
2. Abrir painel no navegador              → http://localhost:8000/index.html
3. Analisar os 20 leads do dia             → Ver score, nicho, WhatsApp
4. Abordar 10-20 leads via WhatsApp        → Um por um, mensagem personalizada
5. Marcar status "Mensagem enviada"        → No painel, após cada envio
```

### Tarde (13:00 - 17:00)

```
6. Verificar respostas do WhatsApp          → Marcar "Respondeu" ou "Interessado"
7. Follow-up dos leads de 7 dias atrás      → Filtrar "Follow-up" no painel
8. Enviar vídeos/demos pros interessados     → Marcar "Vídeo enviado"
9. Enviar propostas comerciais               → Marcar "Proposta enviada"
10. Rodar envio de email (se tiver lista)    → python envio_emails_zoho.py
11. Anotar métricas do dia                   → Quantos abordou, respondeu, fechou
```

### Sexta-feira (revisão semanal)

```
12. python mapear_comercios.py              → Atualiza base de leads
13. python prospectar_leads.py              → Recalcula scores
14. python campanha_diaria.py               → Nova campanha para semana seguinte
15. Revisar métricas da semana              → Taxa de resposta, conversão por nicho
```

---

## 3. ARQUIVOS DE SAÍDA QUE DEVO ANALISAR

### Arquivos principais (analisar diariamente)

| Arquivo | O que contém | Quando olhar |
|---------|-------------|-------------|
| `output/painel/index.html` | Painel visual com leads do dia | Toda manhã |
| `output/painel/status_leads.json` | Status de cada lead | Durante o dia |
| `output/painel/prospeccao.db` | Banco SQLite com métricas | Verificar KPIs |

### Arquivos de referência (olhar semanalmente)

| Arquivo | O que contém | Quando olhar |
|---------|-------------|-------------|
| `output/prospeccao/leads_prospeccao.xlsx` | Base completa de leads | Toda segunda |
| `output/campanhas/campanha_diaria.xlsx` | Top 50 + abas por nicho | Toda segunda |
| `output/playwright/leads_sem_site.csv` | 4.372 leads crus do Maps | Quando recarregar |
| `output/consolidado/base_emails_consolidada.csv` | Leads com email | Antes de enviar emails |

---

## 4. COMO ESCOLHER OS MELHORES LEADS

### Critério de score (0 a 100 pontos)

| Critério | Pontos |
|---------|--------|
| Não tem site | +30 |
| Tem telefone ou WhatsApp | +20 |
| Nota ≥ 4.0 no Google | +15 |
| Mais de 20 avaliações | +15 |
| Tem Instagram | +10 |
| Nicho bom pra landing page | +10 |
| É franquia grande | -30 |
| Tem site profissional | -20 |

### Ordem de prioridade para abordar

**1º** Score ≥ 85 → **Abordar HOJE, é quente**
- Não tem site + tem WhatsApp + nota alta + nicho bom
- Ex: Barbearia com 4.5 estrelas, 50 avaliações, sem site, com WhatsApp

**2º** Score 70-84 → **Abordar esta semana**
- Não tem site + tem telefone + nicho bom
- Ex: Restaurante com 4.0 estrelas, sem site, telefone fixo

**3º** Score 40-69 → **Abordar se sobrar tempo**
- Tem alguma coisa mas não é ideal
- Ex: Loja com site ruim, sem WhatsApp

**4º** Score < 40 → **Não abordar**
- Franquia, tem site profissional, ou nicho ruim

### Melhores nichos para vender landing page

| Nicho | Oferta ideal | Conversão esperada |
|-------|-------------|-------------------|
| Estética / Salão | Página de Agendamento | 8-12% |
| Barbearia | Página de Agendamento | 7-10% |
| Restaurante / Pizzaria | Cardápio Digital | 6-9% |
| Dentista / Clínica | Mini Site Profissional | 5-8% |
| Advogado / Contador | Mini Site Profissional | 4-7% |
| Eletricista / Encanador | Mini Site Vendedor | 3-6% |
| Igreja / Evento | Página de Evento | 3-5% |

### Cidades com mais potencial (priorizar)

1. **Duque de Caxias** — Maior cidade, mais leads
2. **Nova Iguaçu** — 2º maior mercado
3. **São João de Meriti** — Alta densidade comercial
4. **Belford Roxo** — Bom mercado emergente
5. **Nilópolis / Mesquita** — Menos concorrência digital

---

## 5. COMO MONTAR AS MENSAGENS DE WHATSAPP

### O painel já gera a mensagem automaticamente!

Cada lead recebe uma mensagem personalizada por nicho. Mas você pode **melhorar** antes de enviar:

### Template base (já gerado automaticamente)

> Oi, tudo bem? Vi a [NOME] no Google e percebi que vocês têm boas avaliações. Notei que uma página simples com [BENEFÍCIO DO NICHO] e botão direto para WhatsApp poderia [DOR QUE RESOLVE]. Eu montei uma prévia visual de como uma página assim poderia ficar. Posso te mandar?

### Adaptações por situação

**Se o lead tem nota alta (4.5+):**
> Vi que vocês têm **4.8 estrelas no Google** — isso mostra que o trabalho é bom. Falta só um site organizado pra quem te procura no Google encontrar tudo fácil.

**Se o lead tem muitas avaliações (50+):**
> Com **50+ avaliações** no Google, imagine se todo mundo que procura achasse um site com cardápio, localização e botão de pedido direto no WhatsApp.

**Se olead tem WhatsApp disponível:**
> Posso mandar uma prévia visual por aqui mesmo?

**Se NÃO tem WhatsApp (apenas telefone):**
> Posso te ligar rapidinho pra mostrar como ficaria?

### Sequência de mensagens (NÃO mande tudo de uma vez!)

#### Mensagem 1 — Abordagem (DIA 1)
A mensagem gerada automaticamente pelo painel. Clica "Abrir WhatsApp" e envia.

#### Mensagem 2 — Follow-up leve (DIA 3, se não respondeu)
> Oi! Tentei te contatar sobre a página digital pra [NOME]. Se pausa, sem problema. Se tiver curiosidade, é só me chamar.

#### Mensagem 3 — Follow-up com valor (DIA 7, ainda sem resposta)
> Oi! Vi que [NOME] tem boas avaliações no Google. Posso montar uma prévia visual de uma página profissional em 1 dia, sem compromisso. Quer ver como ficaria?

#### Mensagem 4 — Última tentativa (DIA 14)
> Última tentativa! Posso montar uma prévia da página digital da [NOME] gratuitamente. É só dizer sim. Se não for o momento, sem problema algum. Abraço!

### Regras de ouro

- ✅ **1 mensagem por vez** — nunca mande as 4 de uma vez
- ✅ **Personalize o nome** — não manda mensagem genérica
- ✅ **Use o nome do negócio** — mostra que pesquisou
- ✅ **Seja breve** — 3-4 linhas máximo
- ❌ **NUNCA mande link no primeiro contato** — o WhatsApp marca como spam
- ❌ **NUNCA mande PDF antes do lead pedir** — assusta
- ❌ **NÃO mande mais de 3 follow-ups** — depois disso, marca como perdido

---

## 6. COMO ACOMPANHAR FOLLOW-UP

### Sistema de janelas de follow-up

| Status do lead | Quando abordar de novo | Ação |
|---------------|----------------------|------|
| Mensagem enviada, sem resposta | Após 7 dias | Follow-up leve |
| Respondeu, mas parou | Após 7 dias | Perguntar se viu a mensagem |
| Vídeo enviado | Após 3 dias | Perguntar se gostou |
| Proposta enviada | Após 5 dias | Follow-up na proposta |
| Não respondeu após 3 tentativas | Arquivar | Marcar como "Perdido" |

### Como usar o painel para follow-up

1. **Filtrar por "Follow-up"** — Mostra todos que precisam de acompanhamento
2. **Olhar a coluna "Data Follow-up"** — Verifica se já passou a data
3. **Verificar a coluna "Observações"** — Anotar o que foi falado
4. **Clicar "Abrir WhatsApp"** — Envia a mensagem de follow-up

### Formato de anotação (coluna Observações)

```
DD/MM: ABordou, disse que ia ver | DD/MM: Follow-up, não respondeu | DD/MM: Proposta enviada R$3.500
```

### Controle semanal (planilha ou caderno)

| Métrica | Dia 1 | Dia 2 | Dia 3 | Dia 4 | Dia 5 | Total |
|---------|-------|-------|-------|-------|-------|-------|
| Leads abordados | | | | | | |
| Responderam | | | | | | |
| Interessados | | | | | | |
| Propostas enviadas | | | | | | |
| Vendas fechadas | | | | | | |
| Taxa de resposta | | | | | | |

---

## 7. COMO REGISTRAR STATUS DOS LEADS

### Status disponíveis no painel (NESTA ORDEM)

| Status | Quando marcar | O que significa |
|--------|-------------|----------------|
| **novo** | Lead apareceu no painel | Ainda não foi abordado |
| **abordar hoje** | Você decidiu abordar hoje | Prioridade de hoje |
| **mensagem enviada** | Enviou o WhatsApp | Primeiro contato feito |
| **respondeu** | Lead respondeu | Conversa iniciada |
| **vídeo enviado** | Enviou prévia/demo | Mostrou o produto |
| **interessado** | Lead demonstrou interesse | Quase lá |
| **proposta enviada** | Mandou proposta comercial | Aguardando decisão |
| **fechado** | Venda concluída! 🎉 | Parabéns! |
| **perdido** | Lead não fechou | Registro pra aprendizado |
| **follow-up** | Precisa de acompanhamento | Lembrete |
| **não abordar** | Lead não vale a pena | Remover da lista |

### Fluxo visual do funil

```
NOVO → ABORDAR HOJE → MENSAGEM ENVIADA → RESPONDEU → VÍDEO ENVIADO
                                                              ↓
                                              INTERESSADO → PROPOSTA ENVIADA
                                                              ↓
                                              FECHADO ✅  ou  PERDIDO ❌

Em qualquer etapa (sem resposta por 7 dias):
→ FOLLOW-UP → MENSAGEM ENVIADA → ( volta pro funil )
```

### Regras de atualização

- **Atualize IMEDIATAMENTE após cada interação** — não deixe pra depois
- **Sempre anote algo em Observações** — "disse que ia ver", "pediu proposta", "orçamento apertado"
- **Marque "Perdido" se:**
  - Não respondeu após 3 follow-ups
  - Disse que não quer
  - Número inválido/empresarial
- **Nunca delete leads** — marcar como "Perdido" mantém o histórico

---

## 8. O QUE FAZER QUANDO O CLIENTE RESPONDE

### Cenário 1: "Interessado, quero ver como fica"

**1.** Marcar status → **"Interessado"**
**2.** Enviar prévia visual:
   - Se for estética/barbearia → Vídeo curto da demo
   - Se for restaurante → Print/video do cardápio digital
   - Se for serviço → Print do mini site profissional
**3.** Perguntar:
   > "Quer que eu adapte com o nome e as cores do seu negócio? É rapidinho, em 1 dia tá pronto."

### Cenário 2: "Quanto custa?"

**1.** Marcar status → **"Interessado"**
**2.** Responder com a proposta:

> **Landing Page Profissional — R$ 3.500**
> - Página completa com suas informações
> - Botão de WhatsApp/Agendamento
> - Responsiva (celular e computador)
> - Hospedagem inclusa 1 ano
> - SEO básico para aparecer no Google
> - Entrega em 2-3 dias úteis
>
> **Manutenção mensal: R$ 400/mês** (hospedagem, suporte, atualizações)
>
> **Garantia de 30 dias** — se não gostar, devolvo o dinheiro.

**3.** Marcar status → **"Proposta enviada"**
**4.** Anotar valor e data em Observações

### Cenário 3: "Tá caro"

**1.** NÃO baixe o preço imediatamente
**2.** Responda com valor:

> "Entendo! Pensa assim: R$ 3.500 é menos de 1 aluno de mensalidade pagando o ano todo. E a página traz clientes todo mês pelo Google e WhatsApp. Posso fazer R$ 2.800 na primeira e a manutenção a gente vê depois. Quer tentar?"

**3.** Alternativas:
- **Mini Site simples (1 página): R$ 1.800**
- **Cardápio Digital: R$ 1.500**
- **Página de Agendamento: R$ 1.800**

### Cenário 4: "Preciso pensar"

**1.** Não insista. Responda:
> "Claro, sem problema! Fico à disposição. Qualquer dúvida é só me chamar."

**2.** Marcar status → **"Follow-up"**
**3.** Anotar data em Observações
**4.** Retornar em 5-7 dias com algo de valor:
> "Oi! Lembrei de você. Vi que [NOME] tem [X avaliações] no Google — imagine se cada pessoa que procura achasse um site bonitão. Posso te mostrar rapidinho como ficaria?"

### Cenário 5: "Tenho um sobrinho que faz"

**1.** Responda com diferencial:
> "Legal! Mas pensa assim: eu entrego em 2 dias, com suporte via WhatsApp, botão de agendamento integrado, e aparece no Google. Se alguma coisa quebrar, você me chama e resolvo na hora. Quer ver uma prévia pra comparar?"

### Cenário 6: "Como sei que funciona?"

**1.** Mostre resultados:
> "Eu trabalho com negócios da Baixada. Uma landing page bem feita aparece no Google quando alguém procura '[serviço] em [cidade]'. E com o botão de WhatsApp direto, quem entra já pode te chamar. Quer ver um exemplo que fiz?"

**2.** Enviar link ou print de LPs já feitas

### Cenário 7: "Fechou!" 🎉

**1.** Marcar status → **"Fechado"**
**2.** Anotar valor e data em Observações
**3.** Criar a landing page em 2-3 dias
**4.** Entregar com instruções
**5.** Pedir depoimento após 30 dias

---

## CHECKLIST DIÁRIO

### ☀️ Manhã (08:30)

- [ ] Rodar `python gerar_painel_prospeccao.py`
- [ ] Abrir `http://localhost:8000/index.html`
- [ ] Verificar leads do dia (score, nicho, WhatsApp)
- [ ] Filtrar "Alta prioridade" ou "Com WhatsApp"
- [ ] Selecionar 10-20 leads para abordar
- [ ] Para cada lead:
  - [ ] Clicar "Abrir WhatsApp"
  - [ ] Personalizar mensagem (trocar nome se necessário)
  - [ ] Enviar no WhatsApp
  - [ ] Marcar "Mensagem enviada" no painel
  - [ ] Anotar data em Observações

### 🌤️ Tarde (13:00)

- [ ] Verificar respostas do WhatsApp
- [ ] Marcar "Respondeu" / "Interessado" / "Perdido"
- [ ] Filtrar "Follow-up" no painel
- [ ] Abordar leads com follow-up vencido
- [ ] Enviar vídeos/demos pros interessados
- [ ] Enviar propostas comerciais
- [ ] Rodar `python envio_emails_zoho.py` (se tiver lista de emails)

### 🌙 Final do dia (17:00)

- [ ] Contar quantos leads abordados hoje
- [ ] Contar quantos responderam
- [ ] Contar quantos fecharam
- [ ] Anotar métricas na planilha semanal
- [ ] Verificar leads "abordar hoje" que ficou no painel
- [ ] Planejar nichos/cidades do dia seguinte

---

## CHECKLIST SEMANAL (Segunda-feira)

- [ ] Rodar `python mapear_comercios.py` (atualiza base)
- [ ] Rodar `python prospectar_leads.py` (recalcula scores)
- [ ] Rodar `python campanha_diaria.py` (nova campanha)
- [ ] Rodar `python buscar_emails_playwright.py` (busca emails)
- [ ] Rodar `python gerar_painel_prospeccao.py` (atualiza painel)
- [ ] Revisar métricas da semana:
  - [ ] Taxa de resposta (responderam / abordados)
  - [ ] Taxa de conversão (fechados / abordados)
  - [ ] Melhor nicho (maior taxa de resposta)
  - [ ] Melhor cidade (maior taxa de resposta)
  - [ ] Melhor horário de envio
- [ ] Ajustar mensagens com base no que funcionou
- [ ] Remover leads "não abordar" da lista

---

## METAS E NÚMEROS ESPERADOS

### Funil de conversão esperado

| Etapa | Taxa | Para 20 leads/dia |
|-------|------|-------------------|
| Leads abordados | 100% | 20 |
| Responderam | 15-25% | 3-5 |
| Interessados | 8-12% | 2-3 |
| Propostas enviadas | 5-8% | 1-2 |
| Vendas fechadas | 3-5% | 1 |

### Faturamento esperado

| Cenário | Vendas/mês | Faturamento (R$) |
|---------|-----------|-----------------|
| Conservador | 4-8 | R$ 14.000 - R$ 28.000 |
| Realista | 8-15 | R$ 28.000 - R$ 52.500 |
| Otimista | 15-25 | R$ 52.500 - R$ 87.500 |

*Considerando: R$ 3.500/setup + R$ 400/mês manutenção*

### Preços de referência

| Produto | Preço setup | Manutenção/mês |
|---------|------------|----------------|
| Landing Page Completa | R$ 3.500 | R$ 400 |
| Mini Site Profissional | R$ 2.800 | R$ 300 |
| Cardápio Digital | R$ 1.500 | R$ 200 |
| Página de Agendamento | R$ 1.800 | R$ 250 |
| Página de Evento | R$ 2.000 | R$ 250 |

---

## DICAS FINAIS

1. **Nunca mande link no primeiro contato** — o WhatsApp marca como spam
2. **Sempre personalize** — use o nome do negócio
3. **Máximo 20 abordagens/dia** — acima disso parece robô
4. **Melhor horário:** 9h-11h e 14h-16h (horário comercial)
5. **Melhores dias:** Terça a quinta (segunda é caótico, sexta já pensa no fds)
6. **Não desista antes de 3 follow-ups** — 80% das vendas acontecem depois do 5º contato
7. **Registre TUDO** — cada observação, cada data, cada promessa
8. **Foque nos nichos que mais convertem** — estética, barbearia e comida são os tops
9. **Use o painel todo dia** — se deixar acumular, perde o ritmo
10. **Comemore cada venda** — mesmo a primeira! 🎉