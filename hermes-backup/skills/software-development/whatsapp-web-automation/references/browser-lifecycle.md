# Browser Lifecycle — Validação e Padrões

## Testes (`tests/test_browser_lifecycle.py`)

11 testes que comprovam:

| Teste | O que valida |
|-------|-------------|
| `test_setup_playwright_abre_um_context` | `launch_persistent_context` chamado exatamente 1 vez |
| `test_setup_playwright_nao_cria_nova_pagina_se_ja_existe` | Reutiliza página `web.whatsapp.com` existente |
| `test_setup_playwright_fecha_about_blank` | Fecha `about:blank` após setup |
| `test_multiplos_leads_mesma_page` | Vários leads usam `id(page)` idêntico |
| `test_context_fechado_somente_no_final` | `context.close()` chamado 1 vez no `finally` |
| `test_limpeza_campo_entre_leads` | Campo limpo com `fill("")` antes de cada preenchimento |
| `test_voltar_ao_painel_entre_leads` | Escape pressionado entre leads |
| `test_nao_altera_logica_match` | `fazer_match_completo` aceita `page` como 1o parâmetro |
| `test_setup_playwright_retorna_context_e_page` | Retorna `(playwright, (context, page))` |
| `test_setup_playwright_nao_cria_pagina_extra` | Exatamente 1 página após setup |
| `test_pesquisar_telefone_limpa_campo` | `pesquisar_telefone` chama `fill("")` antes de preencher |

## Função `limpar_campo_busca(page)`

Localização: `whatsapp_match/matcher.py`

```python
async def limpar_campo_busca(page) -> None:
    """Limpa campo de busca e volta ao painel lateral entre leads."""
    # 1. Pressiona Escape para fechar painel de informações
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    
    # 2. Limpa campo de busca
    search_selector = await encontrar_seletor_rapido(page, SEARCH_BOX_SELECTORS, 1000)
    if search_selector:
        search_box = page.locator(search_selector)
        await search_box.click()
        await search_box.fill("")
        await page.wait_for_timeout(200)
```

Chamada no sincronizador após cada `fazer_match_completo()`.

## Dry-run de validação (04/07 — commit `5700d3f`)

5 leads processados com métricas de ciclo de vida:

| Métrica | Valor |
|---------|-------|
| `launch_persistent_context_calls` | **1** |
| `new_page_calls` | **1** |
| `about_blank_closed` | **True** |
| `context_close_calls` | **1** (somente no finally) |
| `playwright_stop_calls` | **1** (somente no final) |
| Páginas abertas ao final | **1** (`web.whatsapp.com`) |
| Processos Chrome restantes | **0** |

| Lead | page_id | mesma_page | pages_count | Status | Tempo |
|------|---------|------------|-------------|--------|-------|
| DuoPilates | 2126487633216 | ✅ | 1→1 | no_chat | 10.42s |
| Clinicar Roosevelt | 2126487633216 | ✅ | 1→1 | no_chat | 10.20s |
| AMG Lulu Pet Shop | 2126487633216 | ✅ | 1→1 | no_chat | 10.17s |
| Lume Odontologia | 2126487633216 | ✅ | 1→1 | no_chat | 10.27s |
| AV Studio Pilates | 2126487633216 | ✅ | 1→1 | no_chat | 10.24s |

**page_ids distintos:** `{2126487633216}` → único, reutilizado por todos os leads.
**Campo de busca limpo entre leads:** ✅ (log confirma `limpar_campo_busca` executado após cada lead)

## Commits

- `5700d3f` — `perf: reuse WhatsApp page across lead batch`