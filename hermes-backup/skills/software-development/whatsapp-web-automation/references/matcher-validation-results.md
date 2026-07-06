# Matcher Validation Results

## Histórico

| Data | Commit | Resultado |
|------|--------|-----------|
| 02/07 | `f49169e` | Controle positivo TECM: **MATCHED** em **13.74s** |
| 02/07 | `f49169e` | Dry-run 10 leads: 10 no_chat, ~66s/lead |
| 04/07 | `ae4d168` | Dry-run 20 leads: 16 no_chat, 1 ambiguous_contact, 3 search_field_not_found |
| 04/07 | `d104cbe` | Modal `confirm-popup` identificado e corrigido; sessão expirou após 04/07 |
| 04/07 | `c9f164f` | Re-test 4 leads com autenticação correta: todos **no_chat** (nenhum tem conversa ativa) |
| 04/07 | `5700d3f` | Dry-run 5 leads — validação ciclo de vida do navegador: ✅ 1 context, 1 page, reuso confirmado |
| 04/07 | `5700d3f` | Dry-run lote 2 (offset=20, 20 leads): 3 processados, bloqueado por modal de marketing |
| 04/07 | `5700d3f` | **Correção modal aplicada:** `_fechar_modal` com seletores específicos para `confirm-popup`; `extrair_telefone_confirmado_chat` com verificação pré-header e timeout 5s; `_fechar_modal` chamado após abrir conversa; `confirmar_numero` retorna 3 valores incluindo `modal_blocked` |
| 04/07 | `5700d3f` | **Teste Dra Isadora:** 10.45s, no_chat, sem travamento ✅ |
| 04/07 | `5700d3f` | **Lote retomado (offset=40):** 7/20 leads processados, todos no_chat, sem travamento de modal. Ainda rodando. |

---

## Controle positivo — TECM TECNOLOGIA (02/07)

- **Telefone:** mascara: `5521****7108`
- **Campaign key:** `avgestao:assistencias:primeiro_contato:v1`
- **Resultado:** `matched` (outbound detectado, campaign match = True)
- **Tempo total:** 13.74s (meta: ≤30s)

### Tempos por etapa

| Etapa | Tempo |
|-------|-------|
| search | 1.16s |
| group_detect | 0.02s |
| open_chat | 7.25s |
| confirm_phone | 5.31s |
| outbound_detect | 0.01s |
| fingerprint | 0.00s |

---

## Dry-run 20 leads (04/07 — sync_20260704_001948)

- **Total examinado:** 20
- **no_chat:** 16
- **ambiguous_contact:** 1 (Érica Freire)
- **search_field_not_found:** 3 (Danielle Lopes, Lift Life, Betapetsbr)
- **Tempo médio/lead:** ~19.9s
- **Tempo total:** 6min37s

### Causa do search_field_not_found

Os 3 leads tinham o modal de marketing `confirm-popup` ("As etiquetas agora são as Listas") bloqueando o clique no campo de busca.

**Fix:** `_fechar_modal()` fecha o dialog com Escape antes de cada busca.

---

## Re-test 4 leads (04/07 — autenticação correta)

| # | Lead | Telefone | Variante busca | Chat | Telefone extraído | Evidência | Status |
|---|------|----------|----------------|------|-------------------|-----------|--------|
| 1 | Érica Freire - Estética e Bem Estar | 5521991***2099 | 219913**** | Não | Nenhum | N/A | **no_chat** |
| 2 | Danielle Lopes Pilates | 5521998*** | 219866**** | Não | Nenhum | N/A | **no_chat** |
| 3 | Lift Life | 5521303*** | 213039**** | Não | Nenhum | N/A | **no_chat** |
| 4 | Betapetsbr Banho e Tosa | 5521998*** | 219872**** | Não | Nenhum | N/A | **no_chat** |

**Conclusão:** Todos `no_chat`. Os `ambiguous_contact` anteriores eram falsos positivos.

---

## Dry-run de ciclo de vida do navegador (04/07 — commit `5700d3f`)

5 leads processados com instrumentação de ciclo de vida:

| Métrica | Valor |
|---------|-------|
| `launch_persistent_context_calls` | 1 |
| `new_page_calls` | 1 |
| `about_blank_closed` | True |
| `context_close_calls` | 1 (somente no finally) |
| `playwright_stop_calls` | 1 |
| page_ids distintos | 1 |

| Lead | page_id | mesma_page | pages_count | Status | Tempo |
|------|---------|------------|-------------|--------|-------|
| DuoPilates | 2126487633216 | ✅ | 1→1 | no_chat | 10.42s |
| Clinicar Roosevelt | 2126487633216 | ✅ | 1→1 | no_chat | 10.20s |
| AMG Lulu Pet Shop | 2126487633216 | ✅ | 1→1 | no_chat | 10.17s |
| Lume Odontologia | 2126487633216 | ✅ | 1→1 | no_chat | 10.27s |
| AV Studio Pilates | 2126487633216 | ✅ | 1→1 | no_chat | 10.24s |

---

## Dry-run lote 2 — 20 leads offset=20 (04/07 — sync_20260704_105109)

**BLOCKED** após 3 leads. Modal de marketing "As etiquetas agora são as Listas" (`data-testid="confirm-popup"`, `role="dialog"`, `aria-modal="true"`) interceptou pointer events durante `confirmar_numero()`.

| # | Lead | Telefone | Status | Obs |
|---|------|----------|--------|-----|
| 1 | Pizza Port Delivery | 2196****4332 | no_chat | Normal |
| 2 | Dress Hair Company | 2196****1671 | **ambiguous** | Chat+outbound encontrados, campanha não confirmada |
| 3 | Dra Isadora Correa | 5521****8668 | **BLOCKED** | Modal interceptou click no header por 31s |

**Causa raiz:** O `_fechar_modal` tentou Escape, botões seguros e `mouse.click(0,0)`, mas nenhum fechou este popup específico. Quando o modal persiste, `extrair_telefone_confirmado_chat` tenta clicar no `header[data-testid="conversation-header"]` e fica preso porque o dialog intercepta pointer events.

**Correção aplicada (04/07):**
1. `_BOTOES_SEGUROS_MODAL` expandido com 8 novos seletores para `confirm-popup`
2. `extrair_telefone_confirmado_chat` verifica modal **antes** de clicar no header
3. `header.click()` com timeout de 5s (em vez de 30s)
4. `_fechar_modal` chamado após abrir conversa (ETAPA 3)
5. `confirmar_numero` retorna 3 valores: `(bool, str, str)` — evidencia inclui `"modal_blocked"`
6. `fazer_match_completo` trata `modal_blocked` e retorna imediatamente

**Teste Dra Isadora (pós-correção):** 10.45s, no_chat, sem travamento ✅

---

## Lote retomado — offset=40 (04/07 — sync_20260704_110638)

| # | Lead | Status | Tempo |
|---|------|--------|-------|
| 1 | Academia 15 | no_chat | ~10s |
| 2 | Academia Plena Forma | no_chat | ~10s |
| 3 | Academia Saene Fitness | no_chat | ~10s |
| 4 | Academia Saúde Fit | no_chat | ~10s |
| 5 | Academia Smart Training | no_chat | ~10s |
| 6 | Academia Top Fitness | no_chat | ~10s |
| 7 | Auto Escola Usa do Farrula | no_chat | ~15s |
| 8-20 | (ainda rodando) | — | — |

**Nenhum travamento de modal até o momento.** ✅

---

## Modal confirm-popup

- **Identificado em:** dry-run de 04/07
- **data-testid:** `confirm-popup`
- **role:** `dialog`
- **aria-modal:** `true`
- **Conteúdo:** "As etiquetas agora são as Listas"
- **Fecha com Escape:** SIM (para modais que reagem ao Escape)
- **MAS:** este popup específico reabre ou ignora Escape — precisa de botão dedicado ou click via JS
- **Botões seguros testados:** Fechar, Close, OK, Continuar, Agora não, Not now, Mais tarde, Maybe later — nenhum fecha este popup
- **Botões NUNCA clicados:** Enviar, Delete, Block, Report
- **Proteção implementada:** verificação pré-header + timeout 5s + retorno `modal_blocked`

---

## Sessão expirou após 04/07

Sintoma: `login_required` em todos os leads.
Fix: Escanear QR code na janela do Playwright.

---

## Falhas pré-existentes (não relacionadas ao matcher)

27 falhas em testes de territórios e senders. 479 passes, 14 skips (julho 2026).
