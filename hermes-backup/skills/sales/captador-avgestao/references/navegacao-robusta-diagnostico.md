# Diagnóstico e Correção de Navegação — Junho 2026

## Problema
O run `run_20260629_014644_583c55` travava repetidamente com "🛑 Navegador/contexto fechado — run interrompido". O Chromium bundled era estável em testes isolados, mas falhava durante a captação.

## Causa raiz
O `page.goto()` usava `timeout=45000` (45s). Quando o Google Maps demorava para responder (rede lenta, consulta complexa), o timeout disparava. O código então fazia `page.reload()` sem verificar se a página estava saudável, e depois tentava `items.count()` em uma página em estado inconsistente, resultando em `TargetClosedError` que era interpretado como "navegador fechado".

**O navegador NÃO fechou — a página entrou em estado inválido após timeout de navegação.**

## Correções aplicadas

### 1. Import PlaywrightTimeoutError
```python
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
```

### 2. Constantes de timeout separadas
```python
_TIMEOUT_NAVEGACAO_MS = 90000  # 90s para page.goto
_TIMEOUT_SELETOR_MS = 30000   # 30s para seletores/ações
```

### 3. Função `_avaliar_saude_pagina(browser, context, page)`
Retorna: `"page_valida"`, `"page_fechada"`, `"browser_morto"`, `"context_morto"`, `"sem_browser"`

### 4. Retry controlado em `buscar_categoria`
- Timeout na 1ª tentativa → verifica saúde → 2ª tentativa (se page válida)
- Page fechada com browser vivo → recria via `_context.new_page()`
- Browser morto → `NavegadorFechado`
- 2ª tentativa falha → `[]` (NÃO `NavegadorFechado`)

### 5. Proteção antes de `items.count()`
Verifica saúde antes de contar resultados. Page fechada → `[]`. Browser morto → `NavegadorFechado`.

### 6. Reload seguro
Só recarrega se `page.is_closed() == False` E `browser.is_connected() == True`.

### 7. Bug fix
```python
# ANTES (bug Python — avaliação condicional ambígua):
if eh_nav or not browser.is_connected() if (_browser) else False:

# DEPOIS (claro e correto):
browser_morto = (_browser is not None and not _browser.is_connected())
if eh_nav or browser_morto:
```

### 8. Logs persistentes e instrumentação Playwright
- Logger `_logger_captura(run_id)` grava em `output/avgestao/runs/<run_id>/captura.log`
- Eventos: `browser.on("disconnected")`, `page.on("close")`, `page.on("crash")`
- Log explícito no `finally`: conclusão normal / timeout / NavegadorFechado / CAPTCHA / erro

### 9. `_executar_com_browser` atualizado
- `page.set_default_navigation_timeout(90000)`
- `page.set_default_timeout(30000)`
- Retry com `PlaywrightTimeoutError` ao carregar Maps inicial
- Verificação de saúde em cada ponto de falha
- Tratamento explícito de `NavegadorFechado` no try principal

## Testes
- `tests/test_navegacao_robusta.py` — 20 testes
- Total: 346 (326 originais + 20 novos)

## Scripts de diagnóstico
- `scripts/diagnostico_playwright_maps.py` — teste isolado Chromium + Maps
- `scripts/smoke_test_barramansa.py` — consulta real Barra Mansa

## Problema residual: PermissionError no lock
O resume falhou com `PermissionError` ao escrever `captador_global.lock`. Causa: locks stale de execuções anteriores. Solução: apagar `captador_global.stale_*.lock` e/ou `captador_global.lock`, depois retomar.

## Run preservado
- `run_20260629_014644_583c55`: 41 tarefas, 507 pendentes, 231 leads, Barra Mansa - impressoras