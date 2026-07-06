# Chromium bundled fecha sozinho no Windows (--no-sandbox)

## Sintoma

O `mapear_comercios.py` (linha 945) abre o Chromium bundled do Playwright, mas ele fecha imediatamente. O checkpoint acumula dezenas de erros:

```
Locator.count: Target page, context or browser has been closed
```

Nenhum lead é capturado. O navegador aparece e desaparece sem executar nenhuma pesquisa.

## Causa

O `mapear_comercios.py` usa:

```python
browser = await p.chromium.launch(
    headless=False,
    args=["--disable-blink-features=AutomationControlled"],
)
```

**Sem `--no-sandbox`.** No Windows, o Chromium bundled (versão ~145) pode falhar ao inicializar sem essa flag, especialmente quando o Playwright tenta abrir o navegador em modo persistente ou com perfil.

## Teste de diagnóstico

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox'])
    print(f'✅ Chromium abriu. Versão: {browser.version}')
    page = browser.new_page()
    page.goto('https://google.com')
    print('✅ Navegou no Google')
    browser.close()
```

Com `--no-sandbox` funciona perfeitamente. Sem ele, o navegador abre e fecha na hora.

## Correção (linha 945 do mapear_comercios.py)

Adicionar `"--no-sandbox"` na lista de args:

```python
browser = await p.chromium.launch(
    headless=False,
    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
)
```

## Notas

- `--no-sandbox` é seguro no Windows porque o sandboxing do Chromium depende de recursos do Linux.
- O Chromium bundled do Playwright (versão 145.0.7632.6) foi testado e funciona com essa correção.
- O Chrome instalado (channel="chrome") não tem esse problema, mas pode ter incompatibilidade de versão com o perfil.
- Após aplicar a correção, o resume funciona: `python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>`
