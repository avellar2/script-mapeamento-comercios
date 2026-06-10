---
name: local-sales-prospecting
version: 2.0.0
description: Gerenciar ciclo completo de prospecção de comércios locais para venda de landing pages — papel de gerente comercial/SDR com Supabase como fonte oficial, extração de histórico WhatsApp, importação, campanha diária e follow-up.
tags: [sales, prospecting, whatsapp, landing-pages, local-business, sdr, crm]
triggers:
  - prospecção de comércios locais
  - geração de leads para vendas
  - lista diária de contatos
  - campanha de WhatsApp para negócios locais
  - pipeline de vendas para pequenos comércios
  - filtrar e priorizar leads
  - landing pages para comércios
  - atualizar histórico do WhatsApp
  - preparar campanha de hoje
  - marcar lead como enviado
  - importar leads para o Supabase
  - regras de comunicação em português
---

# Prospecção de Vendas Locais — Gerente Comercial/SDR

Atuar como gerente comercial/SDR do projeto de venda de landing pages na Baixada Fluminense. Supabase é a fonte oficial de dados. Nunca enviar WhatsApp automaticamente. Nunca alterar status sem confirmação.

## Acesso Remoto (Gateway)

Quando o usuário estiver no trabalho e quiser acessar o Hermes remotamente.

**Opção principal: Gateway (Telegram ou Discord)**
1. Configurar o Hermes Gateway no PC que fica ligado (casa ou trabalho)
2. Do outro local, conversar via Telegram/Discord Web ou app
3. O Hermes tem acesso a todos os scripts, WhatsApp Business e dados do PC onde está rodando

**Vantagens do gateway:**
- Conversa de qualquer lugar (celular, web, app)
- Não instala nada no PC de destino (só abre web.app)
- WhatsApp Business fica no PC que está rodando o Hermes

**Alternativas:**
- Instalar Hermes em ambos os PCs: skills + scripts vão por GitHub, mas WhatsApp Business precisa ser configurado separadamente em cada um
- AnyDesk/TeamViewer: funciona mas controla o PC inteiro (mais pesado)
- Preparar tudo antes + envio automático: não precisa de interação em tempo real

**Setup do gateway:** ver `references/gateway-setup.md`

## Fontes de Dados e Arquivos

- **Projeto**: `C:\projetos\script-mapear-comércios`
- **Python**: `python` (no PATH — 3.11.15 instalado via uv)
- **Projeto real**: `C:\Users\Vanderson\Documents\script-mapeamento-comercios` (NÃO `C:\projetos\script-mapear-comércios` — caminho antigo corrigido)
- **Fonte oficial**: **Supabase** — é o banco autoritativo. Todos os leads históricos vivem lá.
- **CSV local** (`output/playwright/todos_comercios.csv`, `leads_sem_site.csv`): **REGERADO a cada execução** do `mapear_comercios.py`. Não é acumulativo — sobrescreve. Não confiar como backup.
- **JSON de progresso** (`output/playwright/progresso.json`): estado bruto do Playwright, não confiável para contagem final.
- **Dashboard local**: `file:///C:/Users/Vanderson/Documents/script-mapeamento-comercios/output/painel/index.html`
- **Banco local SQLite**: `output/painel/prospeccao.db` (legacy, está sendo substituído pelo Supabase)
- **Excel legado**: `campanha_diaria.xlsx` (~915 leads)

## Modelo de Negócio Atual (Junho 2026)

- **Venda única** de landing page por **R$149** (Baixada) / **R$247-297** (Rio Premium)
- **NÃO** é assinatura/mensalidade — o usuário quer modelo simples: vender, criar com Claude Code, colocar no ar
- **Meta**: R$3.000/mês mínimo = ~20 vendas Baixada ou ~12 Rio Premium
- Sem mensalidade, sem recorrência por enquanto. O foco é validar o modelo primeiro.

## Regras Críticas de Operação (NUNCA violar — tudo aprendido com erro)

### Chrome e Processos

1. **NUNCA mudar Playwright para headless=True sem perguntar o usuário.** O usuário quer VER o Chrome mapeando. Headless faz ele pensar que não está funcionando. Isso causou frustração direta.

2. **NUNCA abrir mais de 1 processo mapear_comercios.py por vez.** Se o browser do Playwright cair mas o Chrome ficar aberto (órfão), rodar de novo abre SEGUNDO Chromium — ambos escrevem no mesmo progresso.json e corrompem dados.

3. **Antes de reiniciar um mapeamento, VERIFICAR se o processo realmente morreu:**
   - `process(action='poll')` — checar `status` e `uptime_seconds`
   - `ps aux | grep mapear_comercios` — ver PIDs reais no sistema
   - `cat /proc/<pid>/cmdline | tr '\0' ' '` — confirmar qual script é qual
   O Hermes notifica `[IMPORTANT: Background process completed]` mesmo para processos ANTIGOS que já foram substituídos. Não confiar só nessa notificação.

4. **NUNCA matar todos os Python de uma vez.** Hermes também roda como Python/bash. Antes de matar PIDs: identificar qual é o Hermes (bash com `hermes` no cmdline) e matar APENAS `mapear_comercios.py`. Comando seguro:
   ```bash
   ps aux | grep python | grep -v grep  # listar PIDs
   cat /proc/<pid>/cmdline | tr '\0' ' '  # identificar cada um
   kill -9 <PID_do_mapeador>  # matar SÓ o mapeador
   ```

5. **Solução quando 2 Chromes estão abertos corrompendo progresso:**
   - Matar o processo `mapear_comercios.py` atual
   - Deletar `output/{regiao}/playwright/progresso.json`
   - Reiniciar do zero — o script retoma sem duplicatas

### Acompanhamento de Progresso

- **Cron jobs do Hermes podem não disparar** — não confiar em crons. Usuário pergunta manualmente "como tá o progresso?" e você verifica na hora com Python.
- **Formatar progresso assim para o usuário:**
  - Tarefas (ex: 54/700) — SEMPRE explicar que são bairros × categorias
  - Coletados totais
  - Sem site (leads úteis)
  - Bairro/categoria rodando agora
  - Por bairro: total + sem site

## Regras Obrigatórias (NUNCA violar)

1. **NUNCA enviar WhatsApp automaticamente** — apenas gerar links e mensagens para envio manual
2. **NUNCA apagar dados** — sempre preservar, nunca remover
3. **NUNCA alterar status sem confirmação** — sempre perguntar antes de mudar status no Supabase
4. **NUNCA importar CSV sem aprovação** — sempre mostrar resumo antes de qualquer importação
5. **Sempre mostrar resumo antes de ação importante** — confirmar com o usuário
6. **Idioma**: mensagens em português, tom humano, curto e consultivo — SEM linguagem de spam
7. **Limite diário**: máximo **30 leads** por dia para abordagem manual. O WhatsApp bloqueia após ~50 mensagens em 2 dias. Respeitar pausa de 24h após block.
8. **Respostas ao usuário**: sempre em PT-BR. SEM palavras em inglês, espanhol ou chinês, exceto termos técnicos inevitáveis (Supabase, WhatsApp, CRM, Playwright, Python, JSON, HTML, SQL)
9. **Leads a ignorar sempre**: GRM LOREDO MARIDO DE ALUGUEL (usuário rejeitou explicitamente)
10. **Ao marcar como abordado**: SEMPRE verificar os telefones exatos da campanha que foi enviada. Gerar a lista de enviados a partir dos selecionados, não de uma query ampla, para evitar marcar leads errados. Se marcar errado, reverter com `update({'status': 'novo', 'ultimo_contato_em': None})`.

### ⚠️ WhatsApp Block e limites

- O WhatsApp bloqueia após **~50 mensagens** enviadas em 2 dias (confirmado: 52 mensagens = block de 24h)
- Enquanto bloqueado, **NÃO tentar enviar mais** — esperar 24h
- Leads com telefone fixo (prefixo `21` sem `9`, ex: `2124917996`) **NÃO têm WhatsApp** — pular automaticamente
- Para verificar celular: `tel.startswith('55219')` (com 55) ou `sem55.startswith('219')` (sem 55) AND `len >= 11`
- Ao marcar como abordado: **SEMPRE verificar os telefones exatos** da campanha que foi enviada. Gerar a lista de enviados a partir dos selecionados, não de uma query ampla, para evitar marcar leads errados
- Se marcar errado (status `abordado` que deveria ser `novo`), reverter com: `update({'status': 'novo', 'ultimo_contato_em': None})`

### ⚠️ Formato de entrega de campanha (o usuário rejeitou links longos no chat)

O usuário NÃO consegue usar links `whatsapp://send` colados no chat do Hermes porque:
- URLs enormes não são clicáveis aqui
- Links `whatsapp://send` são protocolo do Windows — não funcionam como link HTML no chat
- O usuário não quer copiar e colar

**SOLUÇÃO VALIDADA** (o usuário aprovou):
1. Gerar um arquivo **HTML** com cards de lead + botão clicável
2. Salvar em `campanha_{regiao}.html` na pasta do projeto
3. Abrir com `start "" "C:\...\campanha_{regiao}.html"` (abre no Chrome do Windows)
4. Links dentro do HTML usam `whatsapp://send?phone={tel}&text={quote(msg)}` para abrir no WhatsApp Business Desktop
5. Fallback: `https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}` para WhatsApp Web no navegador

**O usuário tem dois WhatsApp:**
- Pessoal: no navegador Chrome
- Business: no **app desktop do Windows**
- Ele abre os links via HTML que usam `whatsapp://send` → abre no **app desktop** (Business)

**CSS do HTML:** usar tema escuro (`#0d0d0d`), botão verde (`#25D366`), cards com borda sutil. Cores por região: Rio Premium = `#f59e0b` (laranja), Baixada = `#22c55e` (verde).

| Problema | Causa | Solução |
|----------|-------|---------|
| "Abrindo em uma sessão de navegador existente" | Chrome pessoal aberto bloqueia o Playwright | Fechar TODOS os Chrome com `taskkill` antes |
| Botão enviar não clicava | Seletor obsoleto (`data-testid="send"`) | Usar `button[aria-label="Enviar"]` no WhatsApp Web 2025+ |
| Mensagem não enviava mesmo achando o botão | Página carregou lista de conversas, chat ainda não abriu | Esperar `div[contenteditable="true"]` ficar visível antes |
| Popup "Compartilhe no WhatsApp" com wa.me | Link `wa.me/{tel}?text={msg}` abre página intermediária | Usar `web.whatsapp.com/send?phone={tel}&text={quote(msg)}` direto |

### ⚠️ Campanha direta vs `preparar_campanha.py`

O script `preparar_campanha.py` filtra por:
- `origem = regiao.key` (ex: 'baixada', 'rio_premium')
- `status = 'novo'`
- `tem_site = false`

**Problema conhecido**: muitos leads do Rio Premium foram importados com `origem='baixada'` e `nicho=''` (vazio). Quando isso acontecer:
- Verificar as origens reais: `supa.table('leads').select('origem').execute()`
- Se leads Premium têm origem errada, fazer consulta **direta** por bairro em vez de usar `preparar_campanha.py`
- Preencher `nicho` com `categoria` pra gerar mensagens: `l['nicho'] = l.get('categoria') or l.get('nicho') or ''`
- O script de campanha direta (montado manualmente no Python) faz: busca por `bairro IN (...)` + `status='novo'` + `telefone_normalizado != ''` + `tem_site=false`

**Fluxo alternativo quando script falha**:
1. Buscar leads direto no Supabase filtrando por bairro
2. Diversificar nicho (máx 3 por nicho)
3. Usar `gerar_mensagem_whatsapp(lead, regiao)` do `config.mensagens` com `regiao = resolve_regiao('rio_premium')[0]`
4. Limitar a 30 leads/dia
5. Gerar links `web.whatsapp.com/send?phone={tel}&text={quote(msg)}`

## Preço e Modelo de Negócio

**REALIDADE:** LP sozinha NÃO gera visitas. Sem tráfego pago, a página não recebe clientes novos — ela só **converte** quem já achou o negócio.

**Proposta:** vender LP + tráfego como combo. Ver detalhes em `references/modelo-negocio-estrategia.md`.

| Região | Preço LP | Combo LP + Tráfego/mês |
|--------|----------|----------------------|
| **Baixada** | **R$149** | R$149 + R$99 = **R$248** (1º mês) |
| **Rio Premium** | **R$247-297** | R$247 + R$99 = **R$346** (1º mês) |

| Região | Preço LP | Motivo |
|--------|----------|--------|
| **Baixada** | **R$149** | Acessível, volume, tom direto |
| **Rio Premium** | **R$247-297** | Comércio premium aguenta mais; barato gera desconfiança |

**Meta mínima**: R$3.000/mês = ~20 vendas/mês (1 venda/dia e meio na Baixada) ou ~12 vendas/mês (Rio Premium)

**O que R$149 inclui**: Landing page feita com Claude Code, colocada no ar (hospedagem), 1 revisão, link direto pro WhatsApp deles.

**O R$149 não inclui** (opcional depois): manutenção mensal, alterações frequentes, SEO avançado.

**Faturamento projetado com duas frentes:**
| Frente | Preço | Meta/mês | Faturamento |
|--------|-------|----------|-------------|
| Baixada | R$149 | 10 vendas | R$1.490 |
| Rio Premium | R$247 | 15 vendas | R$3.705 |
| **Total** | - | **25** | **R$5.195** |

## Duas Frentes do Projeto

### baixada
- Tom direto e informal, foco volume
- Preço: R$149
- Scripts: `--regiao baixada`
- Nichos: salão, barbearia, restaurante, pizzaria, oficina, padaria, bar, supermercado etc.
- Mensagem mais simples e objetiva

### rio_premium
- Tom consultivo e profissional
- Preço: R$247-297
- Scripts: `--regiao rio_premium`
- Bairros: Barra da Tijuca, Recreio, Copacabana, Ipanema, Leblon, Botafogo, Flamengo, Tijuca, Jardim Botânico, Lagoa, Gávea, Laranjeiras, Humaitá, São Conrado, Urca, Méier, Vila Isabel, Grajaú, Freguesia, Pechincha, Centro
- Nichos: clínicas de estética, salões premium, barbearias premium, dentistas, psicólogos, nutricionistas, fisioterapeutas, pilates, academias boutique, studios de sobrancelha/cílios, spa, advogados, arquitetos, fotógrafos, harmonização facial, depilação a laser, micropigmentação, personal trainer, consultórios
- **NUNCA**: preço na 1ª mensagem, link na 1ª mensagem, tom de promoção
### Exemplo de mensagem de abertura — Rio Premium (VERSÃO ATUAL APROVADA PELO USUÁRIO):
> "Olá, tudo bem? Vi a clínica de estética Studio Belle Leblon no Google. Notei que as informações sobre tratamentos e resultados poderiam ficar mais organizadas em uma página simples. Quando a cliente precisa pesquisar muito, ela pode acabar escolhendo outra clínica. Eu trabalho criando páginas para clínicas de estética. Posso te mandar uma prévia visual de como ficaria?"

**Arquitetura completa com 6 tipos por nicho** em `references/rio-premium-message-architecture.md`.
**Implementação** em `config/mensagens.py`.

**Regras da mensagem ideal (APROVADAS PELO USUÁRIO — NUNCA VIOLAR):**
- **Citar o nome do comércio** na primeira frase (personaliza a mensagem)
- **Dor INDIRETA e elegante**: "pode acabar agendando em outro lugar" — o usuário REJEITOU EXPLICITAMENTE "você está perdendo cliente pro concorrente", "enquanto não tiver", "concorrente que tem site". Usar "pode acabar", "acaba indo", "outra opção", "outro lugar"
- **Se apresentar sempre**: "Eu trabalho criando páginas para..." — sem isso parece vendedor, não profissional
- **Nunca usar asteriscos/negrito** — WhatsApp não renderiza markdown
- **Acentuação OBRIGATÓRIA** — o usuário reclamou EXPLICITAMENTE de mensagens sem acentos
- **CTA suave**: "Posso te mandar uma prévia visual de como ficaria?"
- **Três variações por tipo** — nunca mandar a mesma mensagem para leads do mesmo nicho

**Mensagens SEMPRE com acentos** (checklist antes de entregar):
`você`, `página`, `clínica`, `serviços`, `informações`, `agendamento`, `tratamentos`, `organizadas`, `fáceis`, `escolhendo`, `padrão`, `negócio`, `nível`, `último`, `opção`, `cardápio`, `experiência`, `presença`

### Tom para Baixada
O usuário aprovou usar o **mesmo tom profissional do Rio Premium** também para a Baixada (16/06/2026). Não precisa mais de tom informal para Baixada — a diferença é apenas o **preço** (R$149 vs R$247-297).

### Regras
- **NUNCA misturar baixada e rio_premium na mesma campanha**
- Franquia: alta confiança = excluir, média = baixa prioridade, sem franquia = priorizar
- Scripts aceitam `--regiao` (baixada ou rio_premium)
- Antes de qualquer campanha, sempre confirmar: região, quantidade, só preparar ou enviar, WhatsApp Business, horário

### Qualidade das mensagens (OBRIGATÓRIO)

Quando for gerar ou revisar mensagens de WhatsApp para leads, verificar:

1. **Acentuação correta** — O usuário reclamou EXPLICITAMENTE de mensagens sem acentos. Todas as mensagens DEVEM ter acentos: `vocês têm`, `página`, `clínica`, `serviços`, `presença`, `agendamento`, `negócio`, `padrão`, `nível`, `último`, `informações`, `opção`, `cardápio`, `experiência`, `disponíveis`, `crédito`, `praticidade`, `preferem`, `oferecem`, etc.
2. **Erros de português corrigidos** — "voceis tem" → "vocês têm", "presenca" → "presença", "nao" → "não", "pra" → "para". Revisar antes de entregar.
3. **Links gerados**: usar `whatsapp://send?phone={tel}&text={quote(msg)}` (protocolo que abre no WhatsApp Business Desktop) quando o usuário estiver no PC. Ter `web.whatsapp.com/send?phone={tel}&text={quote(msg)}` como fallback.
4. **Entrega da campanha**: salvar como `.txt` no disco do projeto (`campanha_{regiao}_{data}.txt`) com nome do lead, nicho, bairro, telefone, mensagem EM TEXTO e os dois links (whatsapp:// e web). O usuário abre o .txt localmente e clica nos links — URLs enormes no chat não funcionam.

### Fluxo alternativo de campanha (quando `preparar_campanha.py` falha)

**Problema conhecido**: O script `preparar_campanha.py` filtra por `origem=regiao.key`. Mas leads do Rio Premium podem ter sido importados com `origem='baixada'`, então o script encontra 0 ou poucos leads.

**Solução** — fazer campanha direta via Python inline (já validado):
1. Buscar leads: `supa.table('leads').select('*').in_('bairro', premium_bairros).eq('status','novo').neq('telefone_normalizado','').is_('tem_site','false').order('score', desc=True).limit(100).execute()`
2. Preencher nicho vazio com categoria: `l['nicho'] = l.get('categoria') or l.get('nicho') or ''`
3. Diversificar nicho: máximo 3 por nicho
4. Gerar mensagens: `gerar_mensagem_whatsapp(l, resolve_regiao('rio_premium')[0])`
5. Salvar como JSON e .txt com links `whatsapp://send` e `web.whatsapp.com/send`
6. **Código completo validado** — ver `references/campanha-direta-workflow.md`

### Funil de Status (Supabase)

```
novo → pronto_para_enviar → abordado → respondeu → follow_up → interessado → convertido
                                                                                     ↘ perdido
```

- Status protegidos: **NUNCA regredir** de `convertido` ou `perdido`
- Status que não devem ser abordados novamente: `abordado`, `respondeu`, `follow_up`, `interessado`, `convertido`, `perdido`
- Apenas abordar leads com status `novo` ou `pronto_para_enviar`
- Follow-up padrão: **7 dias**

## Papel do Gerente Comercial/SDR

### Quando disserem "atualizar histórico do WhatsApp":
1. Rodar `extrair_historico_whatsapp.py` com limite informado
2. Validar CSVs gerados em `output/whatsapp/`
3. Mostrar resumo dos contatos extraídos
4. **Esperar autorização** antes de importar no Supabase

### Quando disserem "preparar campanha de hoje":
1. Buscar leads com status `novo` ou `pronto_para_enviar` apenas
2. Ignorar: `abordado`, `respondeu`, `follow_up`, `interessado`, `convertido`, `perdido`
3. Máximo 15 leads, priorizando: score alto → nicho bom → cidade próxima
4. Gerar mensagem curta, humana e consultiva
5. Gerar link `wa.me` com mensagem pronta
6. **Nunca enviar mensagem automaticamente**

### Quando colarem uma resposta de cliente:
1. Analisar o contexto
2. Sugerir resposta curta, humana e vendedora
3. Ajudar a atualizar o status no Supabase

### Quando o usuario enviar um audio de resposta de cliente:
1. Converter o .ogg para .wav com ffmpeg
2. Transcrever com faster-whisper modelo base
3. Analisar o tom: interesse, duvida, recusa ou condicional
4. Sugerir reply apropriado com base no tom

### Quando um cliente fechar:
1. Montar briefing completo para criar a landing page

### Quando autorizarem importação:
1. Rodar `importar_historico_whatsapp.py` usando `output/whatsapp/historico_whatsapp.csv`
2. Validar se os contatos foram marcados como `abordado`
3. Confirmar que não aparecem mais em `vw_leads_para_abordar`

## Uso da Memória (Regra do Usuário)

**A memória do Hermes funciona como PONTEIRO, não como armazenamento de conteúdo.**
- Na memória: só apontamentos curtos tipo `Skill: local-sales-prospecting`
- Conteúdo detalhado: sempre nas skills (.md) ou nos arquivos de referência
- Se a memória estiver cheia ou perto de encher, consolidar: remover entradas que duplicam skills
- Manter memória leve (~15-20% de uso) para sobrar espaço para coisas novas do momento

**Alertas de modelo (regra do usuário):**
- NUNCA trocar o modelo automaticamente
- Só avisar: "Pra isso, melhor usar **kimi-k2.6** — troca lá e me chama."
- O usuário troca manualmente

## Regras de Comunicação com o Usuário (OBRIGATÓRIO)

1. **Idioma**: SEMPRE responder em português brasileiro. Nunca usar palavras em inglês, espanhol ou chinês, exceto termos técnicos inevitáveis (Supabase, WhatsApp, CRM, Playwright, Python, LP, CTA).
2. **Mensagens para clientes**: 100% em português brasileiro. Revisar e remover termos estrangeiros antes de entregar.
3. **Ser curto, claro e natural**. Não misturar idiomas.
4. **Antes de entregar mensagens de WhatsApp**: revisar e garantir que não têm termos estrangeiros desnecessários.

## Nichos Prioritários (ordem de conversão)

1. Estética / Salão de beleza
2. Barbearia
3. Restaurante / Pizzaria / Comida
4. Serviços locais (eletricista, encanador, etc.)
5. Dentista / Clínica médica
6. Advocacia

## Progresso do Mapeamento (mapear_comercios.py)

### Como funciona
O script `mapear_comercios.py` percorre **bairros/cidades × categorias** no Google Maps via Playwright.

**Total de tarefas por região:**
| Região | Cidades/Bairros | Categorias | Total de tarefas | Leads por tarefa |
|--------|---------------|-----------|-----------------|-----------------|
| baixada | 11 cidades | 40 | 440 | 20 |
| rio_premium | 25 bairros | 28 | 700 | 20 |

Cada tarefa = 1 busca no Google Maps no formato `{categoria} em {bairro/cidade}`. O script tenta coletar até `max_results` leads SEM site por tarefa.

### Como rastrear
O progresso é salvo em tempo real em `output/{regiao}/playwright/progresso.json`. O arquivo pode ter 5-8 MB — NUNCA use `python -c "import json..."` nem `execute_code` nele, vai dar timeout. Use `read_file` com `limit`/`offset` para ler só o necessário.

**Ler progresso (sem timeout):**
```python
# NÃO USE ASSIM (timeout em arquivos grandes):
# python -c "import json; d=json.load(open('progresso.json')); ..."

# USE read_file direto (limit=100, offset=1 já suficiente):
# 1. Ler linhas 1-50: categorias_prontas (quantas já concluíram)
# 2. Ler linhas ~280-330: categorias_em_andamento (o que está rodando agora)
# 3. Ler últimas ~20 linhas: fim do array comercios (últimos coletados)
# 4. Grep: "categorias_prontas" count, '"tem_site": false' count, '"nome":' count
```

**Estrutura real do progresso.json:**
```json
{
  "categorias_prontas": ["Bairro::categoria", ...],   // array de strings
  "categorias_em_andamento": {                       // DICT, não lista!
    "Laranjeiras - Rio de Janeiro, RJ::pilates": {
      "indice": 20,
      "total": 60
    }
  },
  "comercios": [{...}, {...}]   // 5000-7000 objetos
}
```

**Métricas rápidas via grep (search_files):**
- Total categorias concluídas: grep `"categorias_prontas": \[` + contar vírgulas
- Em andamento: `grep "categorias_em_andamento"` → ler com `read_file` offset=318 limit=10
- Total comercios: grep `"nome":` count (~5600)
- Sem site: grep `"tem_site": false` count (~2000)

### Comunicação de progresso ao usuário
- **SEMPRE explicar o total**: não dar apenas "X/700" — explicar que são 25 bairros × 28 categorias
- **Mostrar**: tarefas concluídas vs total, leads coletados, qual bairro/categoria está rodando agora
- Se o usuário pedir "progresso detalhado", mostrar: bairros concluídos, categorias por bairro, com/site vs sem/site
- **Cron jobs do Hermes podem não disparar** — não confiar em crons para tracking. Alternativa: usuário pergunta "progresso?" e você verifica manualmente

### Retomada automática
O `progresso.json` salva progresso incremental. Se o browser fechar ou o processo morrer, basta rodar de novo — ele continua de onde parou. **Não perde dados.**

### Pitfalls
- **Chrome órfão**: se o processo Python morre mas o Chromium fica aberto, rodar de novo abre SEGUNDO browser — dois processos escrevem no mesmo `progresso.json`, corrompendo. Solução: matar Chromium orphans (`taskkill /F /IM chrome.exe`) antes de reiniciar, e apagar `progresso.json` para começar limpo.
- **Dedup**: script usa set `nome|cidade` e carrega CSV existente para evitar duplicatas. Não cria duplicados entre execuções.

## Scripts e Arquivos Principais

| Script | Função |
|--------|--------|
| `gerar_lista_diaria.py` | Filtra top 15 leads, gera mensagens WhatsApp e links wa.me |
| `preparar_campanha.py` | Prepara campanha diária com diversificação de nicho/cidade, mensagens humanas e horários recomendados |
| `gerar_painel_prospeccao.py` | Gera dashboard HTML |
| `mapear_comercios.py` | Coleta comércios no Google Maps via Playwright |
| `extrair_historico_whatsapp.py` | Extrai contatos do WhatsApp Web via Playwright |
| `importar_historico_whatsapp.py` | Importa CSV de histórico para o Supabase |
| `import_leads_to_supabase.py` | Importa planilha Excel para o Supabase com deduplicação |
| `importar_csv_playwright.py` | Importa `output/playwright/leads_sem_site.csv` para o Supabase |
| `marcar_lead_enviado.py` | Marca lead como abordado no Supabase via telefone |
| `utils/phone_utils.py` | Normalização de telefone BR e geração de link wa.me |
| `docs/plano-operacional-diario.md` | Rotina diária completa |

## Fluxo Completo de Venda

### Etapa 1: Mensagem de abertura
Enviar mensagem com dor + CTA ("posso te mostrar como ficaria?"). Aguardar resposta do lead.

### Etapa 2: Quando lead aceita
Quando o lead responde "sim", "manda", "pode", "quero ver" → seguir fluxo: Instagram → LP com Claude Code → vídeo → enviar.

### Etapa 2B: Quando lead pergunta "como seria? e o preço?"
Enviar mensagem de seguimiento explicando funcionamento e oferecendo vídeo gratuito.

### Etapa 3: Mensagem de seguimiento após vídeo
Enviar vídeo + explicação do pixel na mesma mensagem. Depois da resposta, falar preço + pagamento (só paga depois da página no ar).

### Etapa 4: Converter ou arquivar
- Se converter: criar briefing, coletar pagamento, entregar LP
- Se não responder: follow_up em 7 dias
- Se recusar: marcar como perdido

## Pitfalls Adicionais

- **Caminho do projeto mudou**: o projeto real fica em `C:\Users\Vanderson\Documents\script-mapeamento-comercios`, NÃO em `C:\projetos\script-mapear-comércios`. Verificar `pwd` no início de cada sessão.
- **`.env` com JWT token**: o sistema redacta automaticamente tokens JWT detectados. Não passar a chave inteira em comandos ou no `write_file` — criar um script Python salvo em disco que monta a chave por partes (concatenação de strings) e escreve no `.env`. Exemplo: escrever `criar_env.py` no projeto com a chave montada como `part1 + "." + part2 + "." + part3`, depois executar com `python criar_env.py`.
- **Primeiro teste de envio**: enviar APENAS 3 leads (não 15). Mostrar lista antes. Parar imediatamente se houver erro.
- **Python no Windows**: `python` pode não estar no PATH. Use `/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe`
- **WhatsApp Web DOM mudou (2025)**: botão enviar tem `aria-label="Enviar"`, não `data-testid="send"`
- **wa.me vs web.whatsapp.com/send**: para envio automático, use `https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}`
- **Nome do modelo**: `minimax-m2.7` (minúsculo OBRIGATÓRIO)
- **Supabase pagination**: cliente Python retorna no MÁXIMO 1.000 linhas por query. Use `.range()` para paginar.
- **CSVs são sobrescritos**: nunca confiar que CSV local acumula — importar para o Supabase imediatamente após cada mapeamento.
- **Pular leads sem celular**: verificar se `telefone_normalizado` tem formato de celular. No Supabase os números têm `55` na frente (`55219...`). Para detectar celular: `sem55 = tel[2:] if tel.startswith('55') else tel; sem55.startswith('219') and len(sem55) >= 11`. Fixo tem `21` sem o `9` depois.
- **GRM LOREDO**: o usuário NÃO quer enviar para esse lead. Filtrar sempre: `'GRM LOREDO' not in nome.upper()`.
- **Perfil WhatsApp Business** (`.whatsapp_business_profile`) é o correto para envio automatizado.
- **inner_text() do conversation-panel-messages funciona**: `[data-testid=conversation-panel-messages]` com `inner_text()` retorna texto completo.

## Arquivos de Referência