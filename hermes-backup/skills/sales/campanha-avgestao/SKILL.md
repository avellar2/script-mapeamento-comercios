---
name: campanha-avgestao
description: Campanha de prospecção para vender o AVGESTÃO (sistema de gestão R$49/mês) para comércios locais da Baixada Fluminense. Envio automático via Playwright com perfil WhatsApp Business.
---

# Campanha AVGESTÃO

## Produto
- **AVGESTÃO** — sistema de gestão para pequenos negócios
- Funcionalidades: clientes, orçamentos, OS, financeiro, estoque, relatórios
- Diferencial: link pro cliente aprovar orçamento e acompanhar OS
- Preço: a partir de R$49/mês (NÃO mencionar na primeira mensagem)
- Oferta: 15 dias grátis
- Projeto: `C:\projetos\saas-gestão` (Next.js + Prisma + PostgreSQL, VPS)

## Público-alvo
Negócios que usam OS e orçamentos:
- 🔧 Oficinas mecânicas, auto elétricas
- 📱 Assistência técnica (celular, informática)
- 🪚 Serralheria, marcenaria, vidraçaria
- ⚡ Prestadores de serviço (eletricista, pintor, encanador)
- ❄️ Refrigeração e ar condicionado

## Dores por nicho
| Nicho | Dor |
|-------|-----|
| Oficina | serviços autorizados, peças usadas, valores e entrega do veículo |
| Assistência Técnica | aparelhos, diagnóstico, peças e andamento do serviço |
| Serralheria/Marcenaria | medidas, alterações, orçamento e retrabalho |
| Prestadores | quem aprovou, serviço pendente e pagamento em aberto |
| Refrigeração | chamados, equipamentos, histórico e garantia |

## Cronograma de abordagem
```
Dia 1 → Abordagem inicial
Dia 3 → Follow-up 1 (mostrar valor)
Dia 7 → Follow-up 2 (último)
Depois → Marcar como "sem retorno" e encerrar
```

## Estrutura das mensagens (versão atual - junho 2026)
1. "Boa tarde, pessoal da [NOME]! Tudo bem?"
2. "Meu nome é Vanderson e desenvolvi o AVGESTÃO..."
3. Dor específica do nicho com consequência real
4. 2-3 funcionalidades contextualizadas (incluir portal do cliente)
5. "Estou liberando 15 dias gratuitos para teste."
6. CTA: "Posso criar um acesso para vocês entrarem e testarem?"

### Mensagens por nicho (APROVADAS - com acentuação OBRIGATÓRIA)

**Oficina mecânica:**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços, veículos e orçamentos.\n\nUm dos maiores problemas de uma oficina é perder o controle de qual serviço foi autorizado, o que já foi feito e quanto o cliente ainda precisa pagar. Isso pode causar atraso, retrabalho e até discussão na hora da entrega.\n\nNo AVGESTÃO vocês conseguem abrir a ordem de serviço, registrar tudo que será feito, enviar o orçamento para aprovação do cliente e acompanhar cada etapa do veículo.\n\nEstou liberando 15 dias gratuitos para teste.\n\nPosso criar um acesso para vocês entrarem no sistema e testarem na própria oficina?"

**Serralheria/Marcenaria:**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços personalizados e orçamentos.\n\nUm dos maiores riscos desse segmento é uma medida, alteração ou observação importante ficar perdida entre várias conversas no WhatsApp. Um detalhe esquecido pode gerar orçamento errado, retrabalho e prejuízo no material.\n

No AVGESTÃO vocês conseguem registrar o cliente, organizar as informações do serviço, montar o orçamento e enviar um link para o cliente aprovar antes da produção.\n\nO sistema está disponível para teste gratuito durante 15 dias.\n\nPosso criar um acesso para vocês entrarem e testarem no próprio negócio?"

**Prestador (eletricista, pintor, encanador):**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas e profissionais que trabalham com atendimentos e serviços externos.\n\nUm dos maiores problemas nessa rotina é perder o controle de quem pediu orçamento, quem aprovou, qual serviço ainda está pendente e qual cliente ainda não pagou.\n\nNo AVGESTÃO vocês conseguem organizar os clientes, criar orçamentos, abrir ordens de serviço e acompanhar os valores recebidos e pendentes em um só lugar.\n\nEstou liberando 15 dias gratuitos para teste.\n\nPosso criar um login para vocês entrarem no sistema e testarem com os próprios serviços?"

## Follow-up 1 (Dia 3)
- "Passando para saber se conseguiram ver minha mensagem..."
- Reforçar: reúne clientes, orçamentos, OS, andamento, valores, histórico
- Link pro cliente aprovar e acompanhar
- "Posso criar o login de teste para vocês?"

## Follow-up 2 (Dia 7 — último)
- "Esse será meu último contato para não incomodar."
- Reforçar benefícios
- "Quer que eu deixe um acesso preparado para vocês?"
- Após isso: marcar como "sem retorno"

## Scripts de Envio

### Script PREFERIDO: `enviar_assistencias_hoje.py` (aprovado pelo Vanderson em 27/06)
- **Comando:** `python enviar_assistencias_hoje.py` (sem argumentos, sem flags)
- Busca leads com `produto=eq.avgestao&grupo=eq.assistencias&status=in.(novo,pronto_para_enviar)`
- Calcula automaticamente quantos cabem até 17:30 (7min entre cada, máximo 30)
- Só envia para celular DDD 21 com 9º dígito
- Mensagem fixa de assistência técnica (NÃO alterar a mensagem)
- Marca como "abordado" no Supabase após cada envio
- headless=False (NUNCA mudar)
- Perfil: `.whatsapp_business_profile/` (já logado)
- **NÃO tem lock de instância única** — verificar se já tem processo rodando antes de executar
- **NÃO tem fallback** se `channel=chrome` falhar — se o perfil corromper, avisar o Vanderson
- **NÃO tem filtro `--excluir`** — só envia assistências técnicas
- **NÃO alterar:** intervalo de 7min, mensagem, headless=False
- Se aparecer QR Code, avisar o Vanderson — não tentar resolver sozinho

### Script alternativo: `enviar_auto_avgestao.py`
- **Comando:** `python enviar_auto_avgestao.py [qtd] --excluir "nicho1,nicho2"`
- Mais complexo, com mensagens por nicho (9 funções)
- **CAUSOU DUPLICATAS** (Rtech enviado 2x) por buscar MUITAS categorias sem filtro de produto
- Só usar se o Vanderson pedir explicitamente
- Tem lock de instância única (.enviar_auto.pid)
- Tem fallback para Chromium bundled se channel=chrome falhar

### Pré-requisitos antes de rodar QUALQUER script de envio
1. **Verificar se há duplicatas no Supabase** — leads com mesmo nome podem ter 2 registros (um antigo sem telefone, um novo com telefone). Consultar `produto=eq.avgestao`, agrupar por nome, apagar os registros sem `telefone_normalizado` (exceto se status=convertido).
2. **Verificar se leads importados têm `grupo=assistencias`** — leads importados do progresso.json podem vir com `grupo=vazio`. Atualizar via PATCH antes de rodar o script.
3. **Matar Chrome antes de rodar** — `taskkill /F /IM chrome.exe` via Python (subprocess) para evitar conflito de lockfile.
4. **Verificar se o processo anterior morreu** — `ps aux | grep python` para ver se ainda tem script rodando.

### ⚠️ ERRO GRAVE: Importar leads sem verificar duplicatas (27/06/2026)

**O que aconteceu:** Importei 28 leads do `progresso.json` para o Supabase via INSERT direto, sem verificar se o `telefone_normalizado` já existia no banco. Resultado: **26 duplicatas** — o mesmo lead passou a ter 2 registros (um antigo sem telefone, um novo com telefone). O script de envio viu os registros novos como `status=novo` e **reenviou mensagem para leads que já tinham sido abordados**.

**Consequência:** Vanderson ficou puto (com razão). Leads receberam 2 mensagens em dias consecutivos sobre o mesmo assunto.

**Como evitar (regra ABSOLUTA):**
1. ANTES de importar qualquer lead para o Supabase, verificar se o `telefone_normalizado` já existe:
   ```python
   check = f\"{API_URL}?telefone_normalizado=eq.{numero}&select=id,status\"
   ```
2. Se o telefone JÁ EXISTE no banco:
   - Se status é `novo` ou `pronto_para_enviar` → NÃO importar (já está na fila)
   - Se status é `abordado`, `respondeu`, `interessado`, `convertido`, `perdido` → NÃO importar (já foi abordado)
   - Se o registro existente NÃO TEM `telefone_normalizado` (vazio/null) → ATUALIZAR o registro existente com os dados novos (PATCH), NÃO criar um novo
3. Só criar INSERT se o telefone NÃO EXISTIR em nenhum registro no banco
4. Ao importar, SEMPRE definir `produto: 'avgestao'` e `grupo: 'assistencias'` no INSERT/PATCH

**Limpeza de duplicatas (procedimento):**
1. Buscar todos os leads com `produto=eq.avgestao`
2. Agrupar por `nome` (lowercase)
3. Para cada grupo com >1 registro:
   - Separar registros com `telefone_normalizado` vs sem
   - Apagar os registros SEM telefone (DELETE), EXCETO se `status=convertido`
4. Verificar se ainda há duplicatas por `telefone_normalizado`

### Vanderson verifica manualmente no WhatsApp Web se o lead já foi enviado
O Supabase pode mostrar `status=novo` mas o lead já ter sido abordado (por outro registro duplicado, envio manual, etc.). NUNCA confiar cegamente no status do banco — se ele disser que 18 dos 20 já foram enviados, acreditar nele e ajustar o banco. Isso é uma verificação de sanidade essencial antes de qualquer lote de envio.

### Ao corrigir duplicatas (Vanderson confirmou que leads já foram enviados):
1. Buscar os registros por `telefone_normalizado`
2. Fazer PATCH para `status: 'abordado'` com observação explicativa
3. NUNCA apagar registros que têm `telefone_normalizado` (são os com dados completos)
4. Apagar apenas registros SEM telefone (são duplicatas antigas sem dados úteis)

### Captura interrompida (processo morto)
O script `mapear_comercios.py` salva progresso em `output/avgestao/assistencias/progresso.json`. Se o processo for morto (exit -15), os leads capturados até aquele momento estão salvos. Para continuar, basta rodar o mesmo comando novamente — ele retoma de onde parou (não repete leads já capturados). Em 27/06/2026, a captura foi interrompida com 316 leads (Nova Iguaçu e Duque de Caxias parcialmente varridos).

## Regras
- Não enviar mensagens idênticas em massa
- Não inventar informações do comércio
- Não pressionar
- Respeitar quem pedir pra parar
- Após 2 follow-ups sem resposta → encerrar
- Horário ideal: 9h-11h ou 14h-16h
- **Acentação OBRIGATÓRIA** em todas as mensagens
- Não mencionar preço (R$49/mês) na primeira mensagem

## Fluxo de envio (automático)
1. Script busca leads do Supabase (status novo/pronto_para_enviar, produto=avgestao)
2. Filtra só celular (DDD 21 com 9 = celular, 21 sem 9 = fixo)
3. Abre Chrome com perfil WhatsApp Business
4. Navega pra URL de envio com mensagem personalizada
5. Clica em enviar
6. Marca como "abordado" no Supabase
7. Aguarda 7 min, repete
8. **SEM pausa de bloco** — vai direto do primeiro ao último

## Pipeline completa (4 passos)

### NOVO FLUXO (v1 — orquestrador, recomendado)
Usar `executar_campanha_avgestao.py` para capturar leads. O orquestrador NUNCA envia WhatsApp.

**Dry-run (validar cidades/tarefas sem abrir navegador):**
```bash
python executar_campanha_avgestao.py --grupo assistencias --escopo uf --uf RJ --max-total 300 --dry-run
```

**Primeiro teste real (10 leads):**
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" --max-por-consulta 3 --max-total 10 --delay-min 4 --delay-max 8
```

**Objetivo do primeiro teste:** validar navegador, pesquisas, cidades, 6 subnichos, telefone, place_id, maps_url, dedup, limite de 10, fechamento do navegador. Após o teste, apresentar relatório completo e AGUARDAR autorização para o próximo passo.

**Escalonamento OBRIGATÓRIO (não pular etapas):**
1. ✅ Teste real com 10 leads → validar CSV, XLSX, checkpoint, resume
2. ⬜ Lote de 30 leads → validar
3. ⬜ Lote de 50 leads → validar
4. ⬜ Lote de 100 leads → validar
5. ⬜ Só depois ampliar para RJ

Cada etapa depende da **validação da anterior** e da **autorização do Vanderson**. Não executar a próxima sem confirmação.

**Retomar execução interrompida:**
```bash
python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>
```

**Após captura concluída, prospectar + campanha:**
```bash
python executar_campanha_avgestao.py --etapas prospectar,campanha --run-id <RUN_ID> --top 10
```

**Run ID:** Cada execução gera um ID tipo `run_20260628_120000_abc123`. Guardar sempre. Arquivos em `output\avgestao\runs\<RUN_ID>\`.

**Arquivos do run:** config.json, fila.json, checkpoint.json, leads_parciais.csv, leads_parciais.xlsx, resumo.json, execucao.log, erros.jsonl, XLSX geográfico final. Nunca apagar durante execução. Nunca enviar ao GitHub (contêm dados de empresas).

**Status da fila:** pendente, em_andamento, concluída, erro, interrompida, ignorada_limite. `ignorada_limite` não é erro — significa que o limite de leads foi atingido antes de executar aquela tarefa.

**Limites:** `--max-por-consulta`, `--max-por-cidade`, `--max-por-subnicho`, `--max-total`, `--limite-cidades`. Contam apenas leads ÚNICOS após dedup.

**CAPTCHA/bloqueio Google:** NÃO tentar resolver, contornar, atualizar página, trocar IP ou usar evasão. Procedimento correto: salvar screenshot, salvar checkpoint, registrar erro, fechar navegador, informar run_id, aguardar antes de retomar.

### ⚠️ REGRA CRÍTICA: NUNCA ter 2 Chrome abertos simultaneamente na captura
O script `executar_campanha_avgestao.py` abre 1 navegador que reusa para todas as tarefas. Se outro Chrome do Playwright estiver aberto (de execução anterior), os dois podem sobrescrever o perfil um do outro, causando erros de navegação e perda de progresso.

**Procedimento correto ANTES de iniciar captura:**
1. Verificar se há Chrome rodando (`ps aux | grep chrome`)
2. Se houver, matar TODOS via Python subprocess: `subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'])`
3. Aguardar 2s
4. Só então iniciar o script

**Procedimento correto QUANDO o script já está rodando e Vanderson avisa que tem 2 Chrome:**
1. **NÃO matar todos os Chrome** — isso mata o navegador que o script está usando e interrompe a captura
2. Perguntar a ele qual fechar, ou pedir pra ele fechar o que NÃO tem o Google Maps rodando
3. Se ele já fechou um, verificar se o script ainda está rodando e retomar se necessário

**Erro cometido em 28/06/2026:** Vanderson avisou que tinha 2 Chrome abertos. Matei todos via taskkill, o que matou o navegador que o script estava usando. A captura foi interrompida, perdeu-se progresso, e ele ficou irritado (com razão). **NUNCA repetir este erro.**

### ⚠️ Chromium bundled fecha sozinho no Windows (falta --no-sandbox)
O `mapear_comercios.py` (linha 945) usa `p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])` **sem `--no-sandbox`**. No Windows, o Chromium bundled (versão ~145) pode fechar imediatamente após abrir, causando 100+ erros de "Target page, context or browser has been closed" e 0 leads capturados. O Chromium bundled funciona perfeitamente quando testado isoladamente com `--no-sandbox`. **Solução:** adicionar `"--no-sandbox"` na lista de args da linha 945.

**Diagnóstico:** Se o checkpoint mostra 100+ erros de "browser closed" e 0 leads, testar o Chromium isoladamente com `--no-sandbox`. Se funcionar, o problema é a flag faltando. Ver `references/cromium-bundled-no-sandbox-fix.md` para detalhes completos.

### ⚠️ Perfil .whatsapp_business_profile corrompido
Quando processos do Chrome são mortos na força bruta (`kill -9`, `taskkill /F`), o perfil `.whatsapp_business_profile/` pode ficar com `lockfile` travado. Sintomas: script de envio ou captura abre Chrome e ele fecha na hora. **Solução:** deletar a pasta `.whatsapp_business_profile/` e recriá-la vazia. Isso resolve o lockfile, mas o Vanderson precisará logar no WhatsApp Web novamente na próxima execução de envio.

### Auditoria obrigatória antes de qualquer envio (seção 24 do manual)
Antes de executar `enviar_assistencias_hoje.py` ou importar leads no Supabase, apresentar relatório respondendo:

1. **Reconciliação de lotes:** brutos por run, soma bruta, duplicatas entre runs, únicos consolidados, com WhatsApp, já existentes, novos importados, abordados, disponíveis para envio
2. **Explicação de divergências:** se 65 brutos viraram 52 únicos, explicar que foram 13 duplicatas entre runs. Se 55 viraram 52, explicar o erro de conta
3. **Run IDs por lote:** relacionar cada lote ao run_id correspondente
4. **Análise dos leads:** quantos têm telefone, WhatsApp válido, sem telefone, duplicados, já existentes no Supabase, realmente inseridos, abordados, não abordados, em revisão manual, CONFIRMADOS, score ≥ 70
5. **Confirmação no Supabase:** consultar os leads novos e mostrar nome, cidade, subnicho, score, faz_assistencia, status (sem expor chaves/tokens)
6. **5 leads elegíveis para envio:** identificar nominalmente com critérios (grupo assistencias, faz_assistencia CONFIRMADO, score ≥ 70, WhatsApp válido, não abordado, não duplicado, não NAO_CONTATAR, não loja de acessórios, não em revisão manual)
7. **Arquivo de fila:** gerar `output/avgestao/assistencias/fila_envio_5_<data>.csv` sem sobrescrever consolidado original
8. **Confirmação do script:** verificar que `enviar_assistencias_hoje.py` só marca como abordado APÓS o envio ser confirmado (linha 158 do script)

Pare após a auditoria. Não executar o script de envio sem autorização.

### Dry-run antes de qualquer execução real
Sempre executar `--dry-run` primeiro para validar cidades, tarefas, subnichos, limites, fila e configuração SEM abrir navegador. Confirmar que os números estão corretos antes de remover o `--dry-run`.

**Após confirmar dry-run correto, iniciar execução real AUTOMATICAMENTE** — não perguntar "pode executar?". O Vanderson já deu autorização ao passar o comando. Só parar se o dry-run mostrar números incorretos.

Exemplo:
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-por-consulta 3 --max-por-cidade 5 --ordem-cidades alfabetica --delay-min 6 --delay-max 12 --max-tentativas 3 --dry-run
```
Resultado esperado: 92 cidades, 552 tarefas, navegador não aberto, pasta do run criada, config.json/fila.json/checkpoint.json presentes. Parar se algum número estiver incorreto.

### ⚠️ REGRA CRÍTICA: NUNCA ter 2 Chrome abertos simultaneamente na captura
O script `executar_campanha_avgestao.py` abre 1 navegador que reusa para todas as tarefas. Se outro Chrome do Playwright estiver aberto (de execução anterior), os dois podem sobrescrever o perfil um do outro, causando erros de navegação e perda de progresso.

**Procedimento correto ANTES de iniciar captura:**
1. Verificar se há Chrome rodando (`ps aux | grep chrome`)
2. Se houver, matar TODOS via Python subprocess: `subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'])`
3. Aguardar 2s
4. Só então iniciar o script

**Procedimento correto QUANDO o script já está rodando e Vanderson avisa que tem 2 Chrome:**
1. **NÃO matar todos os Chrome** — isso mata o navegador que o script está usando e interrompe a captura
2. Perguntar a ele qual fechar, ou pedir pra ele fechar o que NÃO tem o Google Maps rodando
3. Se ele já fechou um, verificar se o script ainda está rodando e retomar se necessário

**Erro cometido em 28/06/2026:** Vanderson avisou que tinha 2 Chrome abertos. Matei todos via taskkill, o que matou o navegador que o script estava usando. A captura foi interrompida, perdeu-se progresso, e ele ficou irritado (com razão). **NUNCA repetir este erro.**

### ⚠️ Chromium bundled fecha durante captura (timeout de navegação, não crash)
**Diagnóstico comprovado em 29/06/2026:** O Chromium bundled NÃO crasha. Teste isolado (`scripts/diagnostico_playwright_maps.py`) manteve o navegador estável por 30s com Maps carregado, exit code 0.

**Causa real:** O `buscar_categoria` (linha 603 do `mapear_comercios.py`) usa `page.goto(url, wait_until="domcontentloaded", timeout=45000)`. Com delays de 8-15s entre consultas, o Google Maps pode demorar mais de 45s para responder (rede, bloqueio temporário, consulta complexa). Quando o timeout estoura, o código tenta `page.reload()` (linha 608), que também pode falhar. Depois disso, `items.count()` (linha 631) encontra uma página em estado inconsistente e levanta `TargetClosedError`, que é interpretado como "navegador fechado" pelo `_eh_erro_navegador_fechado()`.

**Solução:** Aumentar o timeout do `page.goto` em `buscar_categoria` de 45s para 90s (linha 603 do `mapear_comercios.py`). Isso dá tempo suficiente para o Google Maps responder mesmo com delays longos entre consultas.

**Diagnóstico rápido:** Se o checkpoint mostra 100+ erros de "browser closed" e 0 leads, executar:
```bash
python scripts/diagnostico_playwright_maps.py
```
Se o diagnóstico funcionar (exit code 0, 30s estável), o problema NÃO é o Chromium — é o timeout de navegação. Ver `references/diagnostico-playwright-maps.md` para detalhes.

### Vanderson quer dados crus, sem formatação elaborada
Quando Vanderson pergunta "quantos leads?", "cade os numeros?", "me fala os telefones" — ele quer a informação pura. **NÃO** usar: caixas/bordas/emojis decorativos, links wa.me formatados, tabelas elaboradas com bordas, explicações longas antes dos dados, múltiplas tentativas de adivinhar o que ele quer, agrupamento por categoria não solicitado. **Formato preferido:** lista simples com APENAS o dado que ele pediu. Se ele pediu telefones, dar só os telefones. Se ele pediu quantos leads, dar só o número. Só adicionar contexto se ele perguntar depois. Regra de ouro: se ele pediu X, dar X, não Y+Z.

### Dry-run → execução real automática (sem pedir autorização de novo)
Após confirmar que o dry-run está correto (92 municípios, 552 tarefas, 6 subnichos, etc.), iniciar a execução real **automaticamente** sem perguntar \"pode executar?\". O Vanderson já deu a autorização ao passar o comando. Só parar se o dry-run mostrar números incorretos.

**Deduplicação:** Compara place_id, maps_url, telefone, nome+endereço, nome+cidade (último fallback). Sem fuzzy match. Telefone igual em cidades diferentes não elimina filial automaticamente. Comparar com leads do run E com leads já no Supabase.

**Checkpoint e resume:** Se execução parar (Ctrl+C, terminal fechado, erro, CAPTCHA, queda do navegador), usar MESMO run_id para retomar. Não criar novo run. Resume preserva tarefas concluídas, não repete leads, não altera limites.

**Sou operador, NÃO desenvolvedor.** Durante captação: não modifico código, não crio funcionalidades, não ajusto testes, não reescrevo templates, não altero score/classificação/subnichos/banco, não aplico migration, não faço commit/push. Se encontrar BUG: parar, apresentar comando executado + erro completo + run_id + checkpoint + hipótese da causa + sugestão de correção. Não corrigir sem autorização explícita do Vanderson.

Ver manual completo em `references/captador-avgestao-manual.md`.

### FLUXO ANTIGO (passo a passo, ainda funcional)

### 1. CAPTURAR leads do Google Maps
```bash
python mapear_comercios.py --produto avgestao --grupo assistencias
```
- Busca 6 subnichos de assistência em 11 cidades da Baixada
- Salva CSV em `output/avgestao/assistencias/`
- Progresso em `output/avgestao/assistencias/progresso.json` (não repete lead)
- Demora uns 40-60 min

### 2. QUALIFICAR + gerar XLSX
```bash
python prospectar_leads.py --produto avgestao --grupo assistencias
```
- Lê o CSV, calcula score 0-100, gera mensagens
- Salva em `output/avgestao/prospeccao_avgestao_assistencias.xlsx`

### 3. IMPORTAR pro Supabase
```bash
python import_leads_to_supabase.py --arquivo output/avgestao/prospeccao_avgestao_assistencias.xlsx
```
- Cada lead entra com `produto=avgestao`, `grupo=assistencias`, `status=novo`
- NUNCA sobrescreve lead já abordado (status protegidos)

### 4. ENVIAR WhatsApp
```bash
python enviar_assistencias_hoje.py
```
- Busca no Supabase: `produto=avgestao + grupo=assistencias + status=novo/pronto_para_enviar`
- Envia até as 17:30, 7 min entre cada
- Marca abordado no Supabase após cada envio
- Perfil: `.whatsapp_business_profile` (já logado)
- Se QR Code aparecer, avise o Vanderson

### Regras gerais
- NUNCA altere intervalo de 7 minutos
- NUNCA mude headless=False
- NUNCA altere as mensagens
- NUNCA rode 2 scripts de envio ao mesmo tempo
- Passos 1, 2, 3 só precisa rodar se tiver leads novos
- Passo 4 roda todo dia que tiver lead pendente no Supabase

## Scripts
- `enviar_assistencias_hoje.py` — **script PREFERIDO** para envio automático
- `enviar_auto_avgestao.py` — script antigo (causou duplicatas, evitar)
- `executar_campanha_avgestao.py` — orquestrador de captura (NUNCA envia WhatsApp)
- `mapear_comercios.py` — captador de leads do Google Maps
- `prospectar_leads.py` — qualificação e score
- `import_leads_to_supabase.py` — importação
- Base de leads: Supabase (produto=avgestao, grupo=assistencias, status=novo)

## Resultados
- 23/06/2026: 38 leads enviados (oficina 12, serralheria 10, eletricista 7, pintor 6, marcenaria 3)
- 26/06/2026: Eduardo Cell (conserto de celular, NI) respondeu perguntando preço
- **27/06/2026: 🎉 PRIMEIRO CLIENTE! Universo do Celular (Posse - Nova Iguaçu, conserto de celular) ativou a conta AVGESTÃO às 08:49 (Brasília). R$49/mês.**
- 27/06/2026: 25 mensagens enviadas, 26 duplicatas limpas do banco
- 28/06/2026: 52 leads capturados em 4 lotes (10+23+17+15), 3 novos importados no Supabase

## Quando o lead responde

### Lead perguntou sobre preço/funcionamento
Usar esta estrutura de resposta:

1. Agradecer e responder a pergunta
2. Explicar que é mensal, a partir de R$49/mês
3. Reforçar os 15 dias grátis
4. Contextualizar 2-3 funcionalidades relevantes pro nicho
5. CTA: oferecer criar acesso de teste

**Modelo de resposta (assistência técnica/celular):**
"Bom dia! Obrigado pelo retorno 😊

O AVGESTÃO é um sistema online para organizar clientes, ordens de serviço, orçamentos e controle financeiro. É **mensal**, a partir de **R$49/mês**, e você pode testar **15 dias grátis** sem compromisso.

Nele você consegue abrir a OS, registrar os aparelhos que entram, enviar orçamento pro cliente aprovar por link e acompanhar o andamento de cada serviço — tudo em um lugar só, sem depender do WhatsApp ou caderno.

Quer que eu crie um acesso pra você testar gratuitamente?"

### Fluxo de registro
1. Buscar lead no Supabase pelo telefone (`telefone_normalizado` ou `whatsapp`)
2. Atualizar status para `respondeu`
3. Salvar a resposta do lead em `resposta_cliente`
4. Salvar a resposta enviada em `observacoes`
5. Se pediu teste → status `interessado`, agendar demonstração

### Busca de lead por telefone no Supabase
- Formato no Supabase: `5521XXXXXXXX` (sem espaços, parênteses, traços)
- O lead pode estar com `telefone_normalizado` diferente do número que respondeu
- Estratégia: buscar por final do número (`like.*2926`) ou pelo nome do comércio
- Leads de assistência/celular podem estar categorizados como "loja de celulares" no Supabase (não "assistência técnica") — usar `or=(categoria.ilike.*celular*,categoria.ilike.*assistência*)`

## Referências
- `references/mensagens-completas.md` — texto integral de todas as mensagens aprovadas (abordagem + follow-ups por nicho)
- `references/caso-eduardo-cell-resposta-preco.md` — caso real: lead de assistência técnica respondeu perguntando preço, resposta enviada e lições
- `references/captador-avgestao-manual.md` — manual completo do captador geográfico v1 (orquestrador, run IDs, checkpoint, resume, dedup, limites, CAPTCHA, escalonamento, comandos)
