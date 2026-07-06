# Diagnóstico: Chromium fecha durante captura (29/06/2026)

## Problema
Captura estadual RJ (run `run_20260629_014644_583c55`) interrompida com 100+ erros de "Target page, context or browser has been closed". Zero leads capturados em várias tentativas de resume.

## Hipótese inicial (ERRADA)
"O Chromium bundled crasha no Windows." Teste isolado provou o contrário.

## Diagnóstico
Script `scripts/diagnostico_playwright_maps.py` foi criado para testar o Chromium isoladamente:

```bash
python scripts/diagnostico_playwright_maps.py
```

**Resultado:** EXIT CODE 0. Chromium abriu, Maps carregou em 2s, monitoramento de 30s estável (6/6 checks), sem crash, sem disconnect, sem close inesperado.

## Causa real
O `buscar_categoria` (linha 603 do `mapear_comercios.py`) usa:

```python
await page.goto(url, wait_until="domcontentloaded", timeout=45000)
```

Com delays de 8-15s entre consultas, o Google Maps pode demorar mais de 45s para responder (rede, bloqueio temporário, consulta complexa). Quando o timeout estoura:

1. `page.goto` lança exceção
2. Código tenta `page.reload(wait_until="commit", timeout=30000)` (linha 608)
3. Se reload também falha, a página fica em estado inconsistente
4. `items.count()` (linha 631) encontra página inválida e levanta `TargetClosedError`
5. `_eh_erro_navegador_fechado()` interpreta como "navegador fechado"
6. Run é interrompido

**O navegador NÃO fechou — a página que entrou em estado inválido após timeout de navegação.**

## Solução
Aumentar timeout do `page.goto` em `buscar_categoria` de 45s para 90s (linha 603).

## Como reproduzir o diagnóstico
```bash
cd C:\projetos\script-mapear-comércios
python scripts/diagnostico_playwright_maps.py
```

O script:
- Abre Chromium bundled (sem channel="chrome")
- Navega para Google Maps
- Monitora por 30s (checks a cada 5s)
- Registra eventos de disconnect, close, crash
- Fecha normalmente
- Exit code 0 = estável

Log salvo em: `output/avgestao/diagnosticos/playwright_eventos_<timestamp>.log`
