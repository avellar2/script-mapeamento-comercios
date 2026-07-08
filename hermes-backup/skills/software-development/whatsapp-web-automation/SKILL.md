---
name: whatsapp-web-automation
description: "Playwright automation of WhatsApp Web — matcher optimization, selector patterns, outbound detection, and timing budgets."
version: 1.0.0
tags: [whatsapp, playwright, automation, matcher, selectors, outbound-detection]
triggers:
  - otimizar matcher do WhatsApp
  - acelerar WhatsApp match
  - detectar mensagem de saída no WhatsApp
  - abrir conversa no WhatsApp Web
  - confirmar número no WhatsApp
  - detectar grupo/canal no WhatsApp
  - reduzir timeout do WhatsApp matcher
  - corrigir outbound detection
---

# WhatsApp Web Automation (Playwright)

Padrões de automação do WhatsApp Web via Playwright para match de leads,
detecção de outbound e verificação de campanhas. Foco em performance (~30s/lead).

## Projeto

`C:\projetos\script-mapear-comercios-whatsapp-dedup`
Branch: `feat/protecao-duplicidade-whatsapp`

## Arquivos principais

| Arquivo | Função |
|---------|--------|
| `whatsapp_match/matcher.py` | Lógica de match: pesquisar, abrir, confirmar, detectar outbound |
| `config/whatsapp_selectors.py` | Seletores CSS centralizados + timeouts + helpers |
| `utils/campaign_fingerprint.py` | Fingerprint de mensagens e correspondência de campanha |
| `sincronizar_abordados_whatsapp.py` | Orquestrador: lê leads do Supabase, faz match, reconcilia |

## Timeouts e orçamentos

```
TIMEOUT_PADRAO = 30000   # 30s (operações longas)
TIMEOUT_CURTO  = 1000    # 1s  (wait_for_selector individual)
TIMEOUT_RAPIDO = 500     # 500ms (checks rápidos com count())
```

Orçamentos por etapa:
- Busca sem conversa: 10-20s
- Conversa encontrada: 15-30s
- Controle positivo: ~30s
- Timeout global por lead: ~35s

## Padrão encontrar_seletor_rapido

SEMPRE use `count()` antes de `wait_for_selector` — é instantâneo se o elemento já existe:

```python
async def encontrar_seletor_rapido(page, selectors, timeout=500):
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            if count > 0:
                return selector  # instantâneo
            el = await page.wait_for_selector(selector, timeout=timeout)
            if el:
                return selector
        except Exception:
            continue
    return None
```

## Abertura de conversa com espera composta

Use `asyncio.gather` para aguardar header OU painel de mensagens em paralelo,
com orçamento global de 8s:

```python
async def abrir_conversa(page):
    chat_item.click()
    try:
        await asyncio.wait_for(
            asyncio.gather(
                wait_header(),      # CONVERSATION_HEADER_SELECTORS
                wait_messages(),    # conversation-panel-messages
                wait_loading_gone(), # LOADING_INDICATORS -> hidden
            ),
            timeout=8.0
        )
    except asyncio.TimeoutError:
        pass
    return header_ready or messages_ready
```

## Confirmação de telefone em camadas (`extrair_telefone_confirmado_chat`)

Função: `whatsapp_match.matcher.extrair_telefone_confirmado_chat(page, telefone_canonico)`
Retorna: `(confirmado: bool, telefone: str | None, tipo_evidencia: str)`

**Ordem de preferência (da mais para a menos confiável):**

1. `PHONE_IN_PROFILE_SELECTORS` — número no painel de informações do contato (mais confiável)
2. `a[href*="tel:"]` — link tel: no painel
3. `aria-label` / `title` contendo `+55` ou `55`
4. `data-id` com JID `XXXXXXXXXXX@s.whatsapp.net` no DOM

**Regra de confirmação:** apenas **igualdade canônica completa** (ex: `5521999999999` == `21999999999`).

**NÃO confirmam por si sozinhos:**
- Nome igual (mesmo sem telefone no painel)
- Últimos 4 ou 8 dígitos
- Texto de mensagem contendo o número
- Um único resultado de busca sem evidência do número no DOM
- Telefone parcialmente visível

**`ambiguous_contact`** é o estado correto quando:
- O matcher encontra uma conversa por busca de nome (não por telefone)
- O painel de informações não contém o número canônico do lead
- Nenhuma das 4 camadas consegue extrair e confirmar

Isso **não é um bug** — é o comportamento esperado quando o contato existe no WhatsApp mas o número salvo no celular não corresponde ao número canônico do lead.

## Detecção de outbound

Três camadas, da mais rápida para a mais lenta:

1. **`count()` imediato nos seletores CSS:**
   - `div[data-testid*="out"]`
   - `div.message-out`
   - `div[class*="message-out"]`

2. **Fallback JavaScript** que inspeciona o DOM real:
   - `querySelectorAll` para elementos com `data-testid*="out"` ou classe `message-out`
   - Inspeção de `justifyContent: flex-end` nos containers do painel

3. **NÃO depende de ícones de confirmação** (entregue/lida) — usa estrutura da bolha

## Detecção de grupo/canal/comunidade

Use `count()` imediato em todos os `GROUP_INDICATORS`. Classifique o tipo:

```python
async def detectar_grupo(page):
    for selector in GROUP_INDICATORS:
        count = await page.locator(selector).count()
        if count > 0:
            if "community" in selector: return "community"
            if "channel" in selector:    return "channel"
            return "group"
    return None
```

## Early exit

Implementar interrupção imediata em TODAS as etapas:
- Variante encontra conversa → não testa variantes restantes
- Telefone confirmado → não testa outros seletores
- Outbound encontrado → não carrega mais mensagens
- Grupo/canal detectado → retorna imediatamente

## Instrumentação de tempos

Todo `MatchResult` deve incluir `timings: dict[str, float]` com:
- `search`, `group_detect`, `open_chat`, `confirm_phone`, `outbound_detect`, `fingerprint`, `total`

## Perfil do WhatsApp

Perfil persistente do Chromium para WhatsApp Web. O caminho exato varia por ambiente:

```python
# Opção 1: perfil nomeado (caminho relativo ao home do usuário)
PROFILE_PATH = "profiles/whatsapp_match"

# Opção 2: perfil do Chrome padrão (número)
PROFILE_PATH = str(Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Profile 4")
```

**PITFALL CRÍTICO — Isolamento de sessão do Playwright:**
`launch_persistent_context` abre uma instância Chromium COMPLETAMENTE ISOLADA — não compartilha cookies nem sessão com abas WhatsApp já abertas no Chrome normal. Se a sessão do WhatsApp expirou (QR code visível), não há workaround programático: o QR code precisa ser escaneado manualmente na janela que o Playwright abriu. Nunca assume que "o WhatsApp está aberto no Chrome normal" significa que o Playwright terá sessão ativa.

**Sintoma de sessão expirada:**
- `page.url` retorna `about:blank` ou QR code detectado
- `wait_for_selector("#side")` dá timeout após 30s
- Resultado: `login_required`

**Sessão ativa vs. expirada:**
Quando a sessão está viva, `launch_persistent_context` reutiliza o perfil e o WhatsApp carrega direto. Quando expirou, abre o QR code — e o script fica bloqueado esperando escaneamento.

## Painel de informações — falso positivo `stale_info_panel`

### Causa raiz (descoberta em julho 2026)

O seletor `[data-testid*="drawer" i]` usado para detectar se o painel de informações está aberto produz **falso positivo** porque o WhatsApp Web mantém 5 elementos `drawer-*` permanentemente no DOM:

- `drawer-fullscreen`
- `drawer-left`
- `drawer-middle`
- `drawer-title-body`
- `drawer-right`

Esses elementos:
- estão sempre presentes (fazem parte do layout base)
- estão visíveis (`display != none`)
- não têm `aria-hidden`
- **não indicam** que o painel de informações do contato está aberto

### Sintoma
- `_fechar_painel_info_se_aberto()` tenta fechar o painel (Escape + botões de fechar)
- O check pós-fechamento usa `[data-testid*="drawer" i]` e encontra os 5 elementos
- Conclui que o painel não fechou → retorna `stale_info_panel`
- O indexador para de processar o lote inteiro

### Correção comprovada

**Seletor correto para painel aberto:**
```python
'[data-testid="chat-info-drawer"]'
```

**Seletor correto para botão de fechar:**
```python
'button[aria-label="Fechar"]'
```

**Condição de aberto:** `document.querySelector('[data-testid="chat-info-drawer"]') !== null`

**Condição de fechado:** `document.querySelector('[data-testid="chat-info-drawer"]') === null`

**Tempo de fechamento:** o elemento `chat-info-drawer` é removido do DOM em **<100ms** após clicar no botão de fechar. Não há animação visível — o elemento simplesmente desaparece.

**O que NÃO usar:**
- `[data-testid*="drawer" i]` — falso positivo (sempre presente)
- `section[data-testid*="contact"]` — não encontrado no DOM atual
- `div[data-testid="info-panel"]` — não encontrado no DOM atual
- `div[aria-label*="contact info" i]` — não encontrado no DOM atual
- `div[aria-label*="informações do contato" i]` — não encontrado no DOM atual

### Evidência de DOM (julho 2026)

Estado fechado (painel realmente fechado):
- `[data-testid="contact-info"]` → 0
- `[data-testid*="drawer" i]` → 5 (falso positivo)
- `div[data-testid="info-panel"]` → 0
- `button[aria-label*="Fechar" i]` → 0

Estado aberto (após clicar no header da conversa):
- `[data-testid="chat-info-drawer"]` → 1, visível, 420x1000, x=980
- `button[aria-label="Fechar"]` → 1, visível, 40x40, x=990

Após fechar (100ms):
- `[data-testid="chat-info-drawer"]` → 0
- `button[aria-label="Fechar"]` → 0
- `[data-testid*="drawer" i]` → 5 (permanecem, ignorados corretamente)

## Validação

### Controle positivo

Script que abre o WhatsApp Web, aguarda autenticação (até 5 min) e executa o match contra um telefone conhecido:

```bash
python scripts/controle_positivo_tecm.py
```

Script mais simples (requer WhatsApp já autenticado):

```bash
python scripts/validar_controle_positivo.py
```

### Dry-run

```bash
python sincronizar_abordados_whatsapp.py --dry-run --limit 10
```

**PITFALL:** O `.env` com `SUPABASE_URL` e `SUPABASE_ANON_KEY` precisa estar na raiz do projeto. Se o projeto foi clonado do GitHub, o `.env` não vem junto (gitignore). Copie manualmente de outro clone do mesmo projeto antes de rodar o dry-run.

### Resultados validados (julho 2026)

- Controle positivo TECM: **MATCHED** em **13.74s** (junho, sessão ativa)
- Dry-run 10 leads: 10 no_chat, ~66s/lead (8 variantes, sem conversa)
- Dry-run 20 leads (julho): 16 no_chat, 1 ambiguous_contact (Érica Freire), 3 search_field_not_found (Danielle, Lift Life, Betapetsbr) — 3 com dialog modal interceptando clique no campo de busca
- **Modal confirm-popup identificado:** `data-testid="confirm-popup"`, `role="dialog"`, `aria-modal="true"`, conteúdo "As etiquetas agora são as Listas" — fecha com **Escape** via `_fechar_modal()`
- 1 variante por lead (sem conversa): ~10s/lead vs ~66s (8 variantes)
- Sessão expirou após 04/07 — `login_required` até re-autenticação
- **Re-test 4 leads (julho):** Após autenticação correta com perfil `profiles/whatsapp_match` e busca com variante nacional (`2199131xxxx`), todos os 4 leads (Érica Freire, Danielle Lopes, Lift Life, Betapetsbr) retornaram `no_chat` — **nenhum possui conversa ativa** na conta WhatsApp. Os `ambiguous_contact` anteriores eram falsos positivos de uma sessão diferente ou estado de DOM inconsistente. Status correto: `no_chat`.
- **Dry-run ciclo de vida (julho, commit `5700d3f`):** 5 leads processados com 1 context, 1 page, mesmo `page_id` para todos. `about:blank` fechada. Campo limpo entre leads. Zero processos Chrome restantes. ~10s/lead.
- **Dry-run lote 2 (julho, 20 leads offset=20):** 3 leads processados antes do bloqueio. Lead 1 `no_chat`, Lead 2 `ambiguous` (outbound encontrado mas campanha não confirmada), Lead 3 **BLOCKED** por modal de marketing "As etiquetas agora são as Listas" — dialog `aria-modal="true"` interceptou pointer events por 31s. `_fechar_modal` não conseguiu fechar este popup específico. 17 leads restantes não processados.

### PITFALL: Variante de busca obrigatória

O campo de busca do WhatsApp Web aceita **apenas o formato nacional** (DDD+número, sem +55, sem +). A função `variantes_busca_telefone(telefone_canonico)` retorna `["21991312099"]` para `"5521991312099"`. **Nunca** passe o canônico `5521...` diretamente para `fill()` — resultado será 0 chats encontrados. Sempre use `variantes_busca_telefone()` para obter a variante de busca.

### PITFALL: `mascarar_telefone` não existe

A função `mascarar_telefone` NÃO existe em `utils/phone_utils.py`. As funções disponíveis são: `normalizar_telefone_br`, `variantes_busca_telefone`, `gerar_link_whatsapp`, `extrair_telefone_lead`. Para mascarar, use inline: `tel[:5] + "***" + tel[-4:]`.

### PITFALL: Modal de marketing bloqueia extração de telefone

O WhatsApp Web exibe periodicamente um popup de marketing "As etiquetas agora são as Listas" com `data-testid="confirm-popup"`, `role="dialog"`, `aria-modal="true"`. Este modal **intercepta pointer events** — qualquer `click()` em elementos atrás dele (incluindo o header da conversa) fica preso por 30s até timeout.

**Sintoma:** `Locator.click: Timeout 30000ms exceeded` com mensagem `...from <span> subtree intercepts pointer events`.

**Estratégia de fechamento (`_fechar_modal`):**
1. Tenta **Escape** via `page.keyboard.press("Escape")`
2. Tenta **botões seguros** em `_BOTOES_SEGUROS_MODAL` (Fechar, Close, OK, Continuar, Agora não, etc.)
3. Tenta `mouse.click(0, 0)` no backdrop
4. Se persistir, retorna `False` — o chamador deve tratar como `modal_blocked`

**Seletores adicionados para o popup `confirm-popup`:**
```python
'div[data-testid="confirm-popup"] [role="button"]',
'div[data-testid="confirm-popup"] button',
'div[data-testid="confirm-popup"] button[aria-label*="Fechar" i]',
'div[data-testid="confirm-popup"] span[data-icon="x"]',
'div[data-testid="confirm-popup"] span[data-icon="close"]',
'div[data-testid="confirm-popup"] svg[data-icon="x"]',
'div[data-testid="confirm-popup"] svg[data-icon="close"]',
]

**Proteção contra travamento de 30s em `extrair_telefone_confirmado_chat()`:**

```python
# ANTES de clicar no header: verifica se existe modal bloqueando
modal_check = page.locator('[role="dialog"][aria-modal="true"]')
modal_count = await modal_check.count()
if modal_count > 0:
    modal_fechado = await _fechar_modal(page)
    if not modal_fechado:
        return False, None, "modal_blocked"  # <-- retorna imediatamente, sem tentar click

# Clica no header com timeout curto (5s em vez de 30s)
try:
    await header.click(timeout=5000)
except Exception as e:
    # Tenta fechar modal e retenta
    modal_fechado = await _fechar_modal(page)
    if not modal_fechado:
        return False, None, "modal_blocked"
    try:
        await header.click(timeout=5000)
    except Exception:
        return False, None, "modal_blocked"
```

**Fechamento de modal após abrir conversa (ETAPA 3 do `fazer_match_completo`):**

```python
# ETAPA 3: Abrir conversa
result.chat_found = True

# Fecha modal de marketing que pode aparecer ao abrir conversa
await _fechar_modal(page)

# ETAPA 4: Confirmar número
confirmado, tel_encontrado, evidencia = await confirmar_numero(page, phone_normalized)
if evidencia == "modal_blocked":
    result.status = MatchStatus.MODAL_BLOCKED
    return result
```

**`confirmar_numero` agora retorna 3 valores:**
```python
async def confirmar_numero(page, telefone_canonico: str) -> tuple[bool, Optional[str], str]:
    # Retorna: (confirmado, telefone_encontrado, tipo_evidencia)
    # tipo_evidencia pode ser: "phone_profile", "tel_link", "aria_label", "jid", "modal_blocked", "none"
```

**Impacto no lote:** Sem esta proteção, cada lead com modal ativo fica preso 31s. Com a proteção, retorna `modal_blocked` em <1s e o lote continua para o próximo lead.

**JavaScript fallback (última estratégia antes de `modal_blocked`):**

Quando os seletores Playwright não encontram o botão de fechar, o `_fechar_modal` executa um fallback via `page.evaluate()` que inspeciona o DOM real. O fallback **NUNCA** clica no primeiro botão visível — só clica com correspondência explícita em allowlist segura (texto, aria-label, data-testid, ou ícone X).

```python
fechou_js = await page.evaluate("""
    () => {
        const dialogs = document.querySelectorAll('[role="dialog"][aria-modal="true"]');
        if (dialogs.length === 0) return true;
        for (const d of dialogs) {
            const textos_seguros = ['fechar', 'close', 'ok', 'continuar', 'continue',
                                     'entendi', 'got it', 'agora nao', 'not now',
                                     'mais tarde', 'maybe later', 'x'];
            const botoes = d.querySelectorAll('button, [role="button"], a[role="button"]');
            for (const b of botoes) {
                const texto = (b.textContent || '').trim().toLowerCase();
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                const testid = (b.getAttribute('data-testid') || '').toLowerCase();
                for (const seguro of textos_seguros) {
                    if (texto.includes(seguro) || aria.includes(seguro) || testid.includes(seguro)) {
                        if (!b.hasAttribute('disabled')) { b.click(); return true; }
                    }
                }
            }
            const x_icons = d.querySelectorAll('span[data-icon="x"], span[data-icon="close"], ' +
                                              'svg[data-icon="x"], svg[data-icon="close"]');
            for (const icon of x_icons) {
                const parent = icon.closest('button, [role="button"], a');
                if (parent && !parent.hasAttribute('disabled')) { parent.click(); return true; }
                if (!icon.closest('button') && !icon.closest('[role="button"]')) { icon.click(); return true; }
            }
        }
        return false;
    }
""")
```

**Ordem completa de fechamento de modal:**
1. Escape via `page.keyboard.press("Escape")`
2. Botões seguros em `_BOTOES_SEGUROS_MODAL` (seletores CSS com `aria-label`, `data-testid` ou `data-icon` explícitos)
3. `mouse.click(0, 0)` no backdrop
4. **JavaScript fallback** (texto seguro → X icon apenas — **NUNCA** clica no primeiro botão visível)
5. Se persistir, retorna `False` → `modal_blocked`

**REGRAS DE SEGURANÇA DO FALLBACK (commit `3406249`):**
- **Nunca clicar no primeiro botão visível** de um dialog desconhecido
- **Clicar somente** quando houver correspondência explícita em allowlist segura
- **Allowlist permitida:** Fechar, Close, OK, Continuar, Entendi, Agora não, Not now, Mais tarde, Maybe later, ícone X (`data-icon="x"` ou `data-icon="close"`)
- **Nunca clicar em:** Enviar, Apagar, Excluir, Bloquear, Denunciar, Sair, Desconectar
- **Se nenhum controle seguro for encontrado**, retornar `modal_blocked`
- **Não usar click fora** como confirmação de fechamento
- **Só considerar fechado** quando o dialog realmente desaparecer (`count() == 0`)

**Reproduzir o popup para inspeção:**

Se o popup já foi fechado permanentemente no perfil, tente limpar chaves de localStorage relacionadas:

```python
await page.evaluate("""
    () => {
        const keys = Object.keys(localStorage);
        for (const k of keys) {
            if (k.toLowerCase().includes('label') || 
                k.toLowerCase().includes('list') || 
                k.toLowerCase().includes('popup') ||
                k.toLowerCase().includes('dialog') ||
                k.toLowerCase().includes('confirm') ||
                k.toLowerCase().includes('etiqueta') ||
                k.toLowerCase().includes('nux')) {
                localStorage.removeItem(k);
            }
        }
    }
""")
await page.reload()
```

Isso pode não funcionar se o popup for controlado por flag no servidor ou cookie de sessão. Nesse caso, um perfil novo é necessário.

**Resultados validados (julho 2026, commit `3406249`):**
- Lote offset=80 (20 leads): **20 no_chat**, 0 matched, 0 ambiguous, 0 modal_blocked, 0 erros. Tempo médio ~10s/lead. Zero modais bloqueando. Ciclo de vida: 1 context, 1 page, fechado no final.
- 2 leads que antes eram `modal_blocked` (PET SHOP PIAM, Pet Luxo) retornaram `no_chat` em ~10s cada após adicionar o JS fallback
- 18 leads `no_chat`, 2 `modal_blocked` no lote de 20 (offset=40)
- Zero travamentos de 30s — todos os modais retornaram `modal_blocked` em <1s ou foram fechados
- **Lote offset=120-169 (50 leads):** 50/50 `no_chat`, 0 matched, 0 ambiguous, 0 modal_blocked, 0 erros. Tempo total ~13 min, média ~15s/lead. 1 context, 1 page, fechado no final. Zero processos Chrome restantes.
- **Cobertura total:** offsets 0-169 = 170 leads concluídos, 0 lacunas, 0 duplicações entre runs finais.

## Gargalos remanescentes

Leads sem conversa ainda testam todas as 8 variantes de telefone (~7s cada = ~60s). O early exit só funciona quando a conversa é encontrada. Para reduzir: limitar variantes a 3-4 (as mais comuns: +55DDDNNNNNNNNN, DDDNNNNNNNNN, DDDNNNNN-NNNN) ou adicionar timeout global por lead.

## Ciclo de vida do navegador (batch)

**Regras obrigatórias para `setup_playwright()`:**

1. **Um único `launch_persistent_context` por lote** — nunca abrir/fechar context por lead
2. **Reutilizar página existente** — se `context.pages` já tem `web.whatsapp.com`, usar essa página; não chamar `context.new_page()`
3. **Fechar `about:blank`** — após confirmar WhatsApp ativo, fechar todas as páginas `about:blank` que não sejam a do WhatsApp
4. **Limpar campo de busca entre leads** — chamar `limpar_campo_busca(page)` após cada `fazer_match_completo()`: pressiona Escape (fecha painel de info) e faz `fill("")` no campo de busca
5. **Fechar context/page somente no `finally`** — nunca dentro do loop de leads

```python
async def setup_playwright():
    context = await p.chromium.launch_persistent_context(...)
    
    # Procura página já aberta
    wa_page = None
    for pg in context.pages:
        if "web.whatsapp.com" in getattr(pg, "url", ""):
            wa_page = pg
            break
    
    if wa_page is None:
        wa_page = await context.new_page()
        await wa_page.goto("https://web.whatsapp.com", ...)
    
    # Fecha about:blank
    for pg in list(context.pages):
        if pg is not wa_page and getattr(pg, "url", "") == "about:blank":
            await pg.close()
    
    await wa_page.wait_for_selector('div[data-testid="chat-list"]', ...)
    return p, (context, wa_page)
```

Loop principal:
```python
try:
    for lead in leads:
        result = await fazer_match_completo(page, ...)
        await limpar_campo_busca(page)  # Escape + fill("")
except ...:
    ...
finally:
    await context.close()
    await p.stop()
```

## Perfil do WhatsApp — autenticação

O perfil `profiles/whatsapp_match` é persistente. Se o Chromium for encerrado abruptamente, pode deixar um processo zombie (chrome.exe) segurando o `SingletonLock`. Sintoma: próximo `launch_persistent_context` crasha com exit code 21. Fix: matar o processo chrome.exe via `wmic process where "processid=XXXX" delete`.

Se o perfil não estiver autenticado, o script de controle positivo detecta o QR code e aguarda até 5 minutos. Mantenha a janela visível para o usuário escanear.

### PITFALL: Lock file após kill

Quando um processo do sincronizador é morto (SIGTERM/kill), o lock file em `output/avgestao/whatsapp_match.lock` **não é limpo automaticamente**. O próximo `launch_persistent_context` funciona, mas o script recusa executar com:

```
Já existe uma sincronização ativa.
```

**Fix:** remover o lock manualmente antes de reexecutar:

```bash
rm -f output/avgestao/whatsapp_match.lock
```

### PITFALL: PYTHONUNBUFFERED para logs em tempo real

O Python faz buffer de stdout por padrão quando a saída não é um terminal (como em background processes). Isso faz com que logs do sincronizador demorem minutos para aparecer, dando a impressão de que o processo travou.

**Sintoma:** `process(action="poll")` mostra `output_preview=""` mesmo com o processo rodando há 30s+.

**Fix:** sempre usar `PYTHONUNBUFFERED=1` ao executar o sincronizador em background:

```bash
PYTHONUNBUFFERED=1 python -u sincronizar_abordados_whatsapp.py --dry-run --resume --limit 20
```

Ou usar `python -u` (unbuffered) diretamente.

## Auditoria de cobertura entre runs

Quando há múltiplos runs (especialmente após kills/interrupções), é necessário auditar a cobertura antes de iniciar o próximo lote.

**Procedimento:**

1. Listar todos os runs em `output/avgestao/sincronizador/`
2. Para cada run, ler `dryrun_matches.csv` e extrair `lead_id` + `status`
3. Verificar duplicações entre runs (mesmo `lead_id` em runs diferentes)
4. Verificar lacunas (offsets sem resultado)
5. Confirmar que o checkpoint não avançou indevidamente após SIGTERM

**Comando de auditoria:**

```bash
python -c "
import csv
from pathlib import Path
base = Path('output/avgestao/sincronizador')
all_ids = {}
for d in sorted(base.iterdir()):
    if not d.is_dir(): continue
    csv_file = d / 'dryrun_matches.csv'
    if csv_file.exists():
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_ids.setdefault(row['lead_id'], []).append(d.name)
duplicados = {k:v for k,v in all_ids.items() if len(v) > 1}
print(f'Total lead_ids unicos: {len(all_ids)}')
print(f'Duplicados: {len(duplicados)}')
for k,v in duplicados.items():
    print(f'  {k[:12]}... aparece em: {v}')
"
```

**Resultados validados (julho 2026):**
- 100 lead_ids únicos entre 8 runs, 20 duplicações esperadas (reprocessamento de desenvolvimento)
- **Zero duplicação entre runs finais** (115332 e 120026)
- **Checkpoint não corrompido por SIGTERM** — o processo morto não salvou checkpoint
- **Cobertura completa:** offsets 0-99 = 100 leads, 0 lacunas

## Execução de lotes grandes (50 leads)

O sincronizador suporta `--limit 50` com `--resume`. O lote de 50 leads (offset 120-169) foi executado com sucesso:

- **Tempo total:** ~13 min (média ~15s/lead)
- **50/50 `no_chat`**, 0 matched, 0 ambiguous, 0 modal_blocked, 0 erros
- **Ciclo de vida:** 1 context, 1 page, fechado no final
- **Zero processos Chrome restantes**

**Comando:**
```bash
PYTHONUNBUFFERED=1 python -u sincronizar_abordados_whatsapp.py --dry-run --resume --limit 50
```

O checkpoint avança corretamente de 120 para 170.

## Reteste de leads modal_blocked

Quando leads retornam `modal_blocked` em um run, eles podem ser reprocessados individualmente após correções no `_fechar_modal`. O script `scripts/retest_11_blocked.py` demonstra o padrão:

1. Carregar `lead_id` do CSV do run anterior
2. Buscar telefone real no Supabase
3. Executar `fazer_match_completo` individualmente
4. Relatar estado final

**Resultados validados (julho 2026, commit `3406249`):**
- **11/11 leads modal_blocked resolvidos** para `no_chat` após adicionar JS fallback
- Tempo médio: ~10.2s/lead
- Zero `modal_blocked` remanescentes
- Zero travamentos de 30s

## Referência técnica

- **Resultados de validação** → `references/matcher-validation-results.md` — controle positivo TECM (13.74s MATCHED), dry-run 10 leads, análise de tempos por etapa, comparação de falhas
- **Browser lifecycle** → `references/browser-lifecycle.md` — testes do ciclo de vida do navegador, função `limpar_campo_busca`, padrão de reuso de página

## Envio via web.whatsapp.com/send (sem wa.me)

**Aprendizado validado em julho 2026 (7 runs hermes001–hermes007):** o caminho via `wa.me/<phone>?text=...` é frágil e NÃO deve ser usado para envio automatizado. Falhas comprovadas:

1. **Tela intermediária** — wa.me mostra "Continuar para o WhatsApp Web" que precisa ser clicado
2. **Redirecionamento incompleto** — após clicar, cai em `api.whatsapp.com/send/` sem abrir o chat
3. **Timeout insuficiente** — wa.me demora 27s só pra carregar a tela intermediária; 45s estoura, 120s ainda não resolve o redirect
4. **Sessão expirada** — se o perfil sender estiver deslogado, redireciona para QR Code

**URL correta para envio (commit `e37a4c0`):**
```
https://web.whatsapp.com/send?phone=<telefone>&text=<mensagem_url_encoded>&type=phone_number&app_absent=0
```

Vantagens: sem tela intermediária, sem redirect, campo de mensagem aparece em ~10s, funciona com perfil sender logado. Validada end-to-end em hermes007 com envio real confirmado.

**PITFALL — falso positivo de "número inválido" (commit `5dd93cb`):** a lista `_WA_ME_INVALID_PHONE_TEXTS` não deve conter `"número"` isolado — essa palavra aparece em qualquer página do WhatsApp em português (ex: "Conversar com +55 21 3966-3966"). Usar apenas termos específicos: `"número inválido"`, `"número de telefone inválido"`, `"invalid phone number"`, `"does not exist"`.

## Regras absolutas

- NUNCA enviar mensagens
- NUNCA executar `--apply`
- NUNCA escrever no Supabase
- NUNCA aplicar migration
- NUNCA executar sender
- Apenas leitura do WhatsApp Web
