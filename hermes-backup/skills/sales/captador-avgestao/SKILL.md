---
name: captador-avgestao
description: Operação do captador geográfico de leads AVGESTÃO — Google Maps scraping, orquestrador, run IDs, checkpoint, resume, dedup, dry-run, escalonamento, relatórios. NUNCA envia WhatsApp.
---

# Captador AVGESTÃO — Manual do Operador

## Projeto
- **Diretório:** `C:\projetos\script-mapear-comércios` (NÃO confundir com `saas-gestão` ou scripts de envio)
- **Orquestrador:** `executar_campanha_avgestao.py` — NUNCA envia WhatsApp
- **Captador:** `mapear_comercios.py`
- **Módulos:** `config/territorios.py`, `config/fila.py`, `config/dedup.py`, `config/limites.py`, `config/runs.py`, `config/avgestao.py`
- **Importação:** `import_leads_to_supabase.py`
- **Prospecção:** `prospectar_leads.py`

## Regra principal
Sou **OPERADOR, não desenvolvedor**. Durante captação:
- Não modifico código
- Não crio funcionalidades
- Não ajusto testes
- Não reescrevo templates
- Não altero score/classificação/subnichos/banco
- Não aplico migration
- Não faço commit/push

**Bug encontrado:** parar e apresentar: comando executado, erro completo, run_id, checkpoint, hipótese da causa, sugestão de correção. Não corrigir sem autorização explícita.

## Foco comercial
- **Grupo:** `assistencias`
- **6 subnichos:** celular, computadores, impressoras, eletrodomésticos, eletrônicos, videogames
- O script gera 1 tarefa por combinação cidade × subnicho (ex: 92 cidades × 6 = 552 tarefas)

## Dry-run (sempre antes da execução real)
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-por-consulta 3 --max-por-cidade 5 --ordem-cidades alfabetica --delay-min 6 --delay-max 12 --max-tentativas 3 --dry-run
```
**Validar:** 92 municípios, 6 subnichos, 552 tarefas, navegador NÃO aberto, pasta do run criada, config.json/fila.json/checkpoint.json presentes. Parar se algo estiver incorreto.

## Escalonamento obrigatório (NÃO pular etapas)
1. Teste real com 10 leads → validar CSV/XLSX/checkpoint/resume
2. Lote de 30 leads → validar
3. Lote de 50 leads → validar
4. Lote de 100 leads → validar
5. Só depois ampliar para RJ

Cada etapa depende da **validação da anterior** e da **autorização do Vanderson**. Não executar a próxima sem confirmação.

## Run ID
- Formato: `run_YYYYMMDD_HHMMSS_abc123`
- Guardar sempre
- Arquivos em: `output\avgestao\runs\<RUN_ID>\`
- Conteúdo: config.json, fila.json, checkpoint.json, leads_parciais.csv, leads_parciais.xlsx, resumo.json, execucao.log, erros.jsonl, XLSX geográfico final
- Nunca apagar durante execução
- Nunca enviar ao GitHub (contêm dados de empresas)

## Checkpoint e resume
Se execução parar (Ctrl+C, terminal fechado, erro, CAPTCHA, queda do navegador):
```bash
python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>
```
- Mesmo run_id — não criar novo run
- Preserva tarefas concluídas
- Não repete leads
- Não altera limites

## Status da fila
- `pendente`: ainda não executada
- `em_andamento`: execução atual
- `concluida`: pesquisa finalizada
- `erro`: falhou após tentativas
- `interrompida`: execução parou antes de concluir
- `ignorada_limite`: não executada porque limite foi atingido (NÃO é erro)

## Limites
- `--max-por-consulta`: máx resultados por pesquisa
- `--max-por-cidade`: máx leads únicos por município
- `--max-por-subnicho`: máx por subnicho
- `--max-total`: máx leads únicos no run
- `--limite-cidades`: máx cidades a processar
- Contam apenas leads ÚNICOS após dedup

## CAPTCHA/bloqueio Google
NÃO tentar resolver, contornar, atualizar página, trocar IP ou usar evasão.
Procedimento correto:
1. Salvar screenshot
2. Salvar checkpoint
3. Registrar erro
4. Fechar navegador
5. Informar run_id
6. Aguardar antes de retomar

## Deduplicação
Compara: place_id, maps_url, telefone, nome+endereço, nome+cidade (último fallback).
- Sem fuzzy match
- Telefone igual em cidades diferentes não elimina filial automaticamente
- Comparar com leads do run E com leads já no Supabase

## Supabase
- Migration geográfica já aplicada — não reaplicar
- Campos: uf, estado, regiao, source_query, source_scope, run_id, captured_at, place_id, maps_url
- Índices: idx_leads_uf, idx_leads_run_id, idx_leads_place_id
- Não apagar leads
- Não atualizar dados antigos em massa
- Não expor URL, chave, token ou .env

## Prospecção e campanha (após captura)
```bash
python executar_campanha_avgestao.py --etapas prospectar,campanha --run-id <RUN_ID> --top 10
```
- Processa leads captados
- Aplica classificação e score
- Seleciona os melhores
- Gera arquivos de campanha
- NÃO envia WhatsApp

## Leads elegíveis para campanha
- grupo `assistencias`
- `faz_assistencia = CONFIRMADO`
- score ≥ 70
- telefone/WhatsApp válido
- empresa ativa
- não ser apenas loja de acessórios
- não ter sido abordada anteriormente
- não duplicada
- não marcada para revisão manual

## Mensagem comercial aprovada (NÃO alterar)
```
Boa tarde, pessoal da {NOME_EMPRESA}! Tudo bem?

Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.

Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.

Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.

Posso liberar e configurar o acesso de vocês?
```
- Apenas substituir `{NOME_EMPRESA}` pelo nome curto correto
- Não inventar nome
- Não incluir preço
- Não oferecer vídeo ou demonstração
- Não alterar os 15 dias

## WhatsApp
O captador e o orquestrador NÃO enviam WhatsApp. Durante esta fase:
- Não abrir WhatsApp Web
- Não abrir links wa.me
- Não clicar em Enviar
- Não executar scripts de envio automático
- Não marcar lead como abordado sem confirmação
- Não enviar mensagens sozinho

## ⚠️ REGRA CRÍTICA: 1 Chrome por vez
NUNCA ter 2 Chrome abertos simultaneamente na captura. O script abre 1 navegador que reusa para todas as tarefas. Se outro Chrome do Playwright estiver aberto (de execução anterior), os dois podem sobrescrever o perfil. Sempre verificar com `ps aux | grep chrome` ou `tasklist` antes de iniciar.

## ⚠️ REGRA CRÍTICA: NÃO matar processos Chrome
NÃO usar `taskkill /F /IM chrome.exe`, `Stop-Process`, `os.kill` ou qualquer forma de encerrar processos Chrome. Cada `taskkill` também mata o Chromium do Playwright, causando "browser closed" e interrompendo o run. Em vez disso, deixar o script fechar o navegador no `finally` ou retomar com `--resume`.

## Navegação robusta (timeout, retry, saúde)

O `mapear_comercios.py` agora tem tratamento robusto de navegação:

### Constantes
- `_TIMEOUT_NAVEGACAO_MS = 90000` (90s) — timeout para `page.goto` e navegação
- `_TIMEOUT_SELETOR_MS = 30000` (30s) — timeout para seletores e ações (NÃO usar 90s para tudo)

### Função de saúde: `_avaliar_saude_pagina(browser, context, page)`
Retorna classificação explícita:
- `"page_valida"` — tudo OK
- `"page_fechada"` — browser/context vivos, page fechada (pode recriar)
- `"browser_morto"` — browser desconectado (levantar `NavegadorFechado`)
- `"context_morto"` — context fechado/inutilizável
- `"sem_browser"` — browser/context não informados (testes unitários)

**NUNCA classificar timeout de navegação como `NavegadorFechado`.** Timeout é recuperável; `NavegadorFechado` requer evidência (`browser.is_connected() == False`, `page.is_closed() == True`, erro `TargetClosed`/`BrowserClosed`).

### Fluxo de retry em `buscar_categoria`
1. Tentar `page.goto(url, timeout=90000)`
2. Em `PlaywrightTimeoutError`:
   - Verificar saúde com `_avaliar_saude_pagina()`
   - Se browser/context mortos → `NavegadorFechado`
   - Se page fechada → recriar via `_context.new_page()`, repetir navegação UMA vez
   - Se page válida → repetir navegação UMA vez (`wait_until="commit"`, timeout=30s)
3. Se segunda tentativa falha → retornar `[]` (NÃO `NavegadorFechado`, NÃO `items.count()`)

### Proteção antes de `items.count()`
Antes de contar resultados, verificar `_avaliar_saude_pagina()`:
- `browser_morto`/`context_morto` → levantar `NavegadorFechado`
- `page_fechada` → retornar `[]`
- `page_valida`/`sem_browser` → prosseguir com `items.count()`

### Reload seguro
`page.reload()` só pode ocorrer quando:
- Page não está fechada
- Browser está conectado
- Context está válido
Se reload falha → NÃO seguir para `items.count()`. Registrar erro e encerrar SOMENTE a tarefa atual.

### Logs persistentes
- `_logger_captura(run_id)` → grava em `output/avgestao/runs/<run_id>/captura.log`
- Cada navegação registra: timestamp, run_id, cidade, subnicho, URL, tentativa (1 ou 2), duração, exceção, traceback, `browser.is_connected()`, `page.is_closed()`, ação tomada
- `finally` registra classificação: conclusão normal / timeout / exceção recuperável / CAPTCHA / NavegadorFechado / erro inesperado

### Instrumentação Playwright
- `browser.on("disconnected")` — registra timestamp e run_id
- `page.on("close")` — registra timestamp
- `page.on("crash")` — registra timestamp
- NÃO declarar "Chromium fechou sozinho" sem evento `browser.on("disconnected")` ou evidência equivalente

### Bug fix crítico
Linha original com bug Python:
```python
if eh_nav or not browser.is_connected() if (_browser) else False:
```
Corrigido para:
```python
browser_morto = (_browser is not None and not _browser.is_connected())
if eh_nav or browser_morto:
```

### Testes
- `tests/test_navegacao_robusta.py` — 20 testes cobrindo `_avaliar_saude_pagina`, timeouts, retry, `NavegadorFechado`, page fechada, CAPTCHA, reload seguro
- `tests/test_lock.py` — 16 testes cobrindo lock global, lock por run, concorrência, abandono, recuperação
- Total: 346 testes (326 originais + 20 navegação + 16 lock, mas test_lock usa mocks com fd=999 — o fallback `write_text` cobre esse caminho)

### Scripts de diagnóstico
- `scripts/diagnostico_playwright_maps.py` — teste isolado do Chromium + Maps (30s de monitoramento)
- `scripts/smoke_test_barramansa.py` — consulta real "assistência de impressoras em Barra Mansa, RJ" sem escrever no run

## Lock global: bug corrigido (Windows msvcrt)

**Causa raiz (corrigida):** No Windows, `config/lock.py` usava `Path.write_text()` para escrever metadados no arquivo de lock logo após adquirir `msvcrt.locking()`. Isso abria um segundo handle no mesmo arquivo, causando `PermissionError`. O bug tornava TODO resume impossível — não era arquivo preso, era erro de implementação.

**Correção:** `_escrever_metadados()` agora recebe o `fd` e usa `os.write(fd, ...)` diretamente no handle com lock ativo, com fallback `write_text()` para mocks de teste (fd inválido).

**Se o resume falhar com PermissionError no lock:**
1. Diagnóstico: rodar `python scripts/diagnostico_lock.py` — testa adquirir, escrever via fd, ler, liberar
2. Verificar se há captador ativo: `python executar_campanha_avgestao.py --status --run-id <RUN_ID>` + `ps aux | grep mapear`
3. Inspecionar `.lock` e `.stale_*.lock`: tamanho, data, conteúdo (PID ativo?), permissões
4. Se lock abandonado (PID morto) e diagnóstico confirmar trava livre:
   - Backup: `cp output/avgestao/captador_global.stale_*.lock output/avgestao/backups_locks/<timestamp>/`
   - Mover stale locks para backup (NÃO apagar sem backup)
   - Mover `captador_global.lock` para `.bak_<timestamp>` se comprovadamente livre
5. NÃO apagar locks às cegas. NÃO usar `rm -f` sem diagnóstico prévio.

**Diagnóstico detalhado** → `references/lock-windows-diagnostico.md`

## Referência técnica

- **Diagnóstico de navegação robusta** → `references/navegacao-robusta-diagnostico.md` — causa raiz, correções, testes, scripts de diagnóstico
- **Diagnóstico do lock (Windows)** → `references/lock-windows-diagnostico.md` — PermissionError msvcrt.locking vs write_text, correção os.write via fd, procedimento de 9 etapas
- **Cross-PC resume** → `references/cross-pc-resume.md` — workflow completo para parar captação em um PC, subir pro GitHub, e retomar em outro PC (casa ↔ trabalho)

## Relatório obrigatório (após cada operação)
Apresentar:
- **Execução:** comando, run_id, horário início/término, status final
- **Fila:** cidades, subnichos, tarefas totais/concluídas/pendentes/interrompidas/erros/ignoradas
- **Leads:** brutos, únicos, duplicatas removidas, com telefone, sem telefone, por cidade, por subnicho, já existentes no Supabase
- **Arquivos:** caminho da pasta do run, CSV, XLSX, checkpoint, resumo, erros
- **Problemas:** CAPTCHA, falhas, tarefas que precisam de revisão, dados incompletos

Não afirmar que algo funcionou sem evidência no terminal ou nos arquivos.

## Auditoria obrigatória antes de qualquer envio
Antes de executar `enviar_assistencias_hoje.py` ou importar leads, apresentar:
1. Reconciliação de lotes (brutos por run, soma, duplicatas, únicos, com WhatsApp, existentes, novos, abordados, disponíveis)
2. Explicação de divergências (ex: 65→52 = 13 duplicatas entre runs)
3. Run IDs por lote
4. Análise completa dos leads
5. Confirmação no Supabase (nome, cidade, subnicho, score, faz_assistencia, status)
6. 5 leads elegíveis com critérios
7. Arquivo `fila_envio_5_<data>.csv`
8. Confirmação que script só marca abordado após envio confirmado

Pare após a auditoria. Não executar envio sem autorização.

## Comandos úteis

### Uma cidade
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidade --cidade "Duque de Caxias, RJ" --max-total 20
```

### Várias cidades
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" --max-total 30
```

### Estado do Rio
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-por-consulta 3 --max-por-cidade 5 --ordem-cidades alfabetica --delay-min 6 --delay-max 12 --max-tentativas 3
```

### Vários estados
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo ufs --ufs RJ MG SP --max-total 300
```

### Região Sudeste
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo regiao --regiao sudeste --max-total 300
```

### Brasil (NUNCA sem limites)
```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo brasil --limite-cidades 100 --max-total 500
```

## Consulta de andamento do run (protocolo fixo)

Quando Vanderson pedir "andamento", "status", "ver como está" ou similar:

1. Executar APENAS:
   ```bash
   python executar_campanha_avgestao.py --status --run-id <RUN_ID_ATIVO>
   ```
2. Obter PID do captador:
   ```bash
   wmic process where "name='python.exe'" get processid,commandline | grep -i "mapear\|campanha\|avgestao"
   ```
3. Informar APENAS: leads (contagem do CSV), cidade atual, subnicho, tarefas concluídas, tarefas pendentes, captação ativa (SIM/NÃO + PID)
4. NUNCA: executar resume, iniciar captação, abrir Chromium, alterar arquivos, apagar locks, encerrar processos

## Vanderson quer dados crus, não formatação elaborada
Quando Vanderson pergunta "quantos leads?", "cade os numeros?", "me fala os telefones" — ele quer a informação pura, sem caixas/bordas/emojis decorativos, links wa.me formatados, tabelas elaboradas, explicações longas antes dos dados. Se ele pediu X, dar X, não Y+Z. Formato preferido: lista simples com o dado que ele pediu. Só adicionar contexto extra se ele perguntar depois.
