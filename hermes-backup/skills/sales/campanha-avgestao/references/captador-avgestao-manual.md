# Manual do Operador — Captador Geográfico AVGESTÃO v1

## 1. Projeto Correto

O captador está em: `C:\projetos\script-mapear-comércios`

NÃO confundir com:
- SaaS AVGESTÃO em Next.js
- Projeto `saas-gestão`
- Scripts antigos de envio
- Captadores de landing pages

## 2. Situação Atual

Versão 1 do captador geográfico concluída. Estado:
- 297 testes passando
- Migration Supabase aplicada
- 9 colunas geográficas presentes (uf, estado, regiao, source_query, source_scope, run_id, captured_at, place_id, maps_url)
- 3 índices presentes (idx_leads_uf, idx_leads_run_id, idx_leads_place_id)
- Código no GitHub: branch `feat/captador-geografico-avgestao-v1`, tag `captador-avgestao-v1`
- Modo landing pages preservado
- Funções comerciais preservadas

Migration já aplicada — não reaplicar.

## 3. Objetivo

Pesquisar estabelecimentos no Google Maps e gerar leads para AVGESTÃO.

Suporta escopos: cidade | cidades | uf | ufs | regiao | brasil | arquivo personalizado.

Possui: fila estruturada, checkpoint, resume, dedup global, limites, detecção de CAPTCHA, tratamento de Ctrl+C, CSV, XLSX, integração Supabase, orquestrador em 1 comando.

## 4. Foco Comercial Atual

Grupo: `assistencias`

6 subnichos:
1. Assistência técnica de celulares
2. Computadores e notebooks
3. Impressoras
4. Eletrodomésticos
5. Eletrônicos
6. Videogames

Cada execução gera pesquisa para cada combinação cidade × subnicho.

## 5. Arquivos

- `mapear_comercios.py` — captador (pesquisa, fila, dedup, checkpoint, resume, dry-run)
- `executar_campanha_avgestao.py` — orquestrador (encadeia mapear + prospectar + campanha)
- `config/territorios.py` — municípios, UFs, regiões
- `config/fila.py` — fila de pesquisas
- `config/dedup.py` — deduplicação global
- `config/limites.py` — limites por leads únicos
- `config/runs.py` — run_id, checkpoint, arquivos
- `config/avgestao.py` — regras comerciais
- `import_leads_to_supabase.py` — importação

NÃO alterar esses arquivos durante operação comum.

## 6. Regra Principal — Sou Operador, Não Desenvolvedor

Durante captação:
- Não modificar código
- Não criar funcionalidades
- Não ajustar testes
- Não reescrever templates
- Não alterar score/classificação/subnichos/banco
- Não aplicar migration
- Não fazer commit/push

Se encontrar BUG:
1. Parar
2. Apresentar: comando executado + erro completo + run_id + arquivo de checkpoint + hipótese da causa + sugestão de correção
3. NÃO corrigir sem autorização explícita

## 7. Dry-Run

Valida cidades, tarefas, grupos, subnichos, limites, fila e configuração SEM abrir navegador.

```bash
python executar_campanha_avgestao.py --grupo assistencias --escopo uf --uf RJ --max-total 300 --dry-run
```

Resultado: 92 cidades, 552 tarefas, pasta do run criada, fila e checkpoint gerados.

## 8. Escalonamento Obrigatório

NÃO começar com 300 leads. Sequência:
1. Teste real com 10 leads
2. Validar CSV, XLSX, checkpoint e resume
3. Lote de 30 leads
4. Lote de 50 leads
5. Lote de 100 leads
6. Só depois ampliar para RJ

Cada etapa depende da validação da anterior e autorização do Vanderson. NÃO pular etapas.

## 9. Run ID

Formato: `run_YYYYMMDD_HHMMSS_abc123`

Arquivos em: `output/avgestao/runs/<RUN_ID>/`

Podem existir: config.json, fila.json, checkpoint.json, leads_parciais.csv, leads_parciais.xlsx, resumo.json, execucao.log, erros.jsonl, XLSX geográfico final, arquivos de prospecção/campanha.

Nunca apagar durante execução. Nunca enviar ao GitHub (contêm dados de empresas).

## 10. Status da Fila

- `pendente` — não executada
- `em_andamento` — execução atual
- `concluida` — pesquisa finalizada
- `erro` — falhou após tentativas
- `interrompida` — execução parou antes de concluir
- `ignorada_limite` — não executada porque limite foi atingido (NÃO é erro)

## 11. Limites

Contam apenas leads ÚNICOS após dedup.

Argumentos: `--max-por-consulta`, `--max-por-cidade`, `--max-por-subnicho`, `--max-total`, `--limite-cidades`.

Ex: `--max-total 10` = máximo 10 leads únicos no run todo.

## 12. CAPTCHA

Se aparecer CAPTCHA ou bloqueio:

1. Salvar screenshot
2. Salvar checkpoint
3. Registrar erro
4. Fechar navegador
5. Informar run_id
6. Aguardar antes de retomar

NÃO tentar resolver automaticamente, contornar, atualizar página, trocar IP ou usar evasão.

## 13. Deduplicação

Compara: place_id, maps_url, telefone, nome+endereço, nome+cidade (último fallback).

Regras:
- Sem fuzzy match
- Telefone igual em cidades diferentes não elimina filial automaticamente
- Comparar com leads do run E com leads já no Supabase

## 14. Checkpoint e Resume

Se execução parar (Ctrl+C, terminal fechado, erro, CAPTCHA, queda do navegador):

```bash
python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>
```

Regras:
- Mesmo run_id (NÃO criar novo run)
- Não repete tarefas concluídas
- Reconstroi dedup
- Continua tarefas pendentes/interrompidas
- Preserva leads já salvos
- NÃO altera limites do run existente

## 15. Comandos Úteis

```bash
# Uma cidade
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidade --cidade "Duque de Caxias, RJ" --max-total 20

# Várias cidades
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" --max-total 30

# Estado do Rio
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-total 100

# Vários estados
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo ufs --ufs RJ MG SP --max-total 300

# Região Sudeste
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo regiao --regiao sudeste --max-total 300

# Brasil (NUNCA sem limites)
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo brasil --limite-cidades 100 --max-total 500
```

## 16. Prospecção e Campanha

Após captura concluída:

```bash
python executar_campanha_avgestao.py --etapas prospectar,campanha --run-id <RUN_ID> --top 10
```

Antes, confirmar que `leads_parciais.csv` existe.

## 17. Leads Elegíveis

Para campanha de assistências, priorizar:
- grupo `assistencias`
- `faz_assistencia = CONFIRMADO`
- score >= 70
- telefone válido
- empresa ativa
- não ser apenas loja de acessórios
- não ter sido abordada anteriormente
- não duplicada
- não marcada para revisão manual

NÃO assumir que uma empresa conserta equipamentos só porque apareceu em uma busca.

## 18. Mensagem Comercial Aprovada

"Boa tarde, pessoal da {NOME_EMPRESA}! Tudo bem?

Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.

Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.

Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.

Posso liberar e configurar o acesso de vocês?"

Regras: não resumir/reescrever/expandir. Só substituir {NOME_EMPRESA}. Não incluir preço. Não oferecer vídeo ou demonstração. Não alterar 15 dias.

## 19. Relatório Obrigatório

Após cada operação, apresentar:

### Execução
- Comando executado, run_id, horário início/término, status final

### Fila
- Cidades, subnichos, tarefas totais, concluídas, pendentes, interrompidas, erros, ignoradas por limite

### Leads
- Brutos encontrados, únicos aceitos, duplicados removidos, com/sem telefone, por cidade, por subnicho, já existentes no Supabase

### Arquivos
- Caminho da pasta do run, CSV, XLSX, checkpoint, resumo, erros

### Problemas
- CAPTCHA, falhas, tarefas que precisam de revisão, dados incompletos, comportamento inesperado

NÃO afirmar que algo funcionou sem evidência no terminal ou nos arquivos.

---

## Apêndice A — Lições Aprendidas na Operação (28/06/2026)

### A.1 Chromium bundled fecha sozinho no Windows (falta --no-sandbox)

O `mapear_comercios.py` (linha 945) usa `p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])` **sem `--no-sandbox`**. No Windows, o Chromium bundled (versão ~145) pode fechar imediatamente após abrir, causando 100+ erros de "Target page, context or browser has been closed" e 0 leads capturados.

**Diagnóstico:** Se o checkpoint mostra 100+ erros de "browser closed" e 0 leads, testar o Chromium isoladamente com `--no-sandbox`:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox'])
    page = browser.new_page()
    page.goto('https://google.com')
    print('OK')
    browser.close()
```
Se funcionar com `--no-sandbox` e falhar sem, o problema é a flag faltando.

**Solução:** Adicionar `"--no-sandbox"` na lista de args da linha 945 do `mapear_comercios.py`.

### A.2 Perfil .whatsapp_business_profile corrompido

Quando processos do Chrome são mortos na força bruta (`kill -9`, `taskkill /F`), o perfil `.whatsapp_business_profile/` pode ficar com `lockfile` travado. Sintomas: script de envio ou captura abre Chrome e ele fecha na hora.

**Solução:** Deletar a pasta `.whatsapp_business_profile/` e recriá-la vazia. Isso resolve o lockfile, mas o Vanderson precisará logar no WhatsApp Web novamente na próxima execução de envio.

### A.3 NUNCA ter 2 Chrome abertos simultaneamente na captura

O script `executar_campanha_avgestao.py` abre 1 navegador que reusa para todas as tarefas. Se outro Chrome do Playwright estiver aberto (de execução anterior), os dois podem sobrescrever o perfil um do outro, causando erros de navegação e perda de progresso.

**Procedimento:** Sempre verificar se há processo Chrome rodando antes de iniciar uma captura (via `ps aux | grep chrome` ou `taskkill`). Se houver 2, matar todos antes de começar — o tempo de captura com 2 Chrome é perdido.

### A.4 Vanderson quer dados crus, não formatação elaborada

Quando Vanderson pergunta "quantos leads?", "cade os numeros?", "me fala os telefones" — ele quer a informação pura, sem caixas/bordas/emojis decorativos, links wa.me formatados, tabelas elaboradas, explicações longas antes dos dados, ou múltiplas tentativas de adivinhar.

**Regra de ouro:** Se ele pediu X, dar X, não Y+Z. Formato preferido: lista simples com o dado que ele pediu. Só adicionar contexto extra se ele perguntar depois.

### A.5 Importar leads sem verificar duplicatas = erro GRAVE

**O que aconteceu (27/06/2026):** Importei 28 leads do `progresso.json` para o Supabase via INSERT direto, sem verificar se o `telefone_normalizado` já existia no banco. Resultado: 26 duplicatas — o mesmo lead passou a ter 2 registros (um antigo sem telefone, um novo com telefone). O script de envio viu os registros novos como `status=novo` e reenviou mensagem para leads que já tinham sido abordados.

**Procedimento correto:**
1. ANTES de importar, verificar se o `telefone_normalizado` já existe no Supabase
2. Se o telefone JÁ EXISTE: NÃO importar (seja qual for o status)
3. Se o registro existente NÃO TEM `telefone_normalizado` (vazio/null): ATUALIZAR o registro existente com PATCH, NÃO criar INSERT
4. Só criar INSERT se o telefone NÃO EXISTIR em nenhum registro
5. Ao importar, SEMPRE definir `produto: 'avgestao'` e `grupo: 'assistencias'`

### A.6 Vanderson verifica manualmente no WhatsApp Web

O Supabase pode mostrar `status=novo` mas o lead já ter sido abordado (por outro registro duplicado, envio manual, etc.). NUNCA confiar cegamente no status do banco — se ele disser que 18 dos 20 já foram enviados, acreditar nele e ajustar o banco via PATCH. Isso é uma verificação de sanidade essencial antes de qualquer lote de envio.

### A.7 Ao corrigir duplicatas confirmadas pelo Vanderson

1. Buscar os registros por `telefone_normalizado`
2. Fazer PATCH para `status: 'abordado'` com observação explicativa
3. NUNCA apagar registros que têm `telefone_normalizado` (são os com dados completos)
4. Apagar apenas registros SEM telefone (são duplicatas antigas sem dados úteis)
5. Exceção: manter registros com `status=convertido` mesmo sem telefone
