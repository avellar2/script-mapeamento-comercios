# wa.me Intermediate Screen & Token-Based Semi Confirmation

## wa.me Landing Page

When opening `https://wa.me/<phone>?text=<message>`, WhatsApp shows an intermediate page — NOT the chat directly.

### What the page contains

- Heading: "Conversar com +55 XX XXXX-XXXX no WhatsApp"
- Button: "Abrir app" (opens WhatsApp Desktop if installed)
- Button: **"Continuar para o WhatsApp Web"** (redirects to web.whatsapp.com with the chat open)
- Links: "Baixar o WhatsApp na Microsoft"

### DOM structure (confirmed 2026-07-07)

```
heading[level=2]: "Conversar com +55 21 3966-3966 no WhatsApp"
link: "Abrir app"
link: "Continuar para o WhatsApp Web"
```

### Old code failure (before commit `71e45d5`)

```python
# campanha_whatsapp.py — abrir_wa_me() (line 288-306)
await page.goto(link, wait_until="domcontentloaded", timeout=30000)
await page.wait_for_timeout(3000)
await page.wait_for_selector(
    'div[contenteditable="true"][data-tab="10"], '
    'div[contenteditable="true"][title], '
    'footer div[contenteditable="true"]',
    timeout=15000,
)
```

This waited for the message `div[contenteditable]` which doesn't exist on the intermediate page. After 15s → "Campo de mensagem não encontrado" → `wa_me_falha`.

### Fix (commit `71e45d5`)

After `page.goto(wa.me_link)`:
1. Detect the intermediate screen (look for "Continuar para o WhatsApp Web" link)
2. Click it
3. Wait for redirect to `web.whatsapp.com`
4. Then search for `div[contenteditable="true"]`

### Critical dependency: sender session

"Continuar para o WhatsApp Web" redirects to `web.whatsapp.com`. If `.whatsapp_business_profile` session is expired:
- Redirect lands on QR code page
- Chat never opens
- 45s timeout fires on `wa_me_loaded`
- Result: `wa_me_falha` (same error as the old bug, but different root cause)

**Always verify sender session is active before testing semi mode.**

### Diagnostic procedure

```python
# Quick session check (read-only, no send)
from playwright.sync_api import sync_playwright
import json, time

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir='.whatsapp_business_profile',
        headless=False,
        args=['--no-sandbox'],
        viewport={'width': 1280, 'height': 800},
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=60000)
    time.sleep(15)
    
    qr = page.query_selector('canvas, [data-ref] img, div:has-text("escaneie")')
    chat_list = page.query_selector('div[data-testid="chat-list"]')
    search = page.query_selector('input[placeholder*="Pesquisar" i]')
    
    print(json.dumps({
        'qr_found': qr is not None,
        'chat_list_found': chat_list is not None,
        'search_found': search is not None,
    }, indent=2))
    
    browser.close()
```

If `qr_found: true` → session expired, user must scan QR code.

## Token-Based Semi Confirmation

### Flag

`--semi-confirm-token "CONFIRMAR-<last4>-<run_id_curto>"`

### Token format

```
CONFIRMAR-<last4>-<run_id_curto>
```

Example: `CONFIRMAR-3966-hermes002`

- `<last4>` = last 4 digits of normalized phone (visible in `plan` output as `****3966`)
- `<run_id_curto>` = short run ID (e.g. `hermes002` from `run_20260707_hermes002`)

### How to derive the token

1. Run `plan --limit 1 --run-id run_20260707_hermes002` → observe `5521****3966`
2. Extract last 4: `3966`
3. Extract run_id_curto: `hermes002`
4. Token: `CONFIRMAR-3966-hermes002`

### Validated behavior (HEAD `fb687e0`)

```
Token valido - confirmacao automatica aceita
Iniciando pipeline de envio pos-confirmacao...
Abrindo wa.me...
```

Stages confirmed:
- `manual_confirmed` ✅ (source=token, not input())
- `post_manual_confirmed` ✅
- `wa_me_opening` ✅

### Security

The token is NOT a secret. It is derived from data already visible in `plan` output. It only authorizes the send pipeline to proceed past the `prompt_manual` stage.

### Full semi command with token

```bash
python campanha_whatsapp.py semi \
  --limit 1 \
  --nicho assistencias \
  --until 23:59 \
  --interval-minutes 5 \
  --verification-budget-seconds 15 \
  --run-id run_20260707_hermes002 \
  --semi-confirm-token "CONFIRMAR-3966-hermes002" \
  --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

## wa.me timeout fix (commit `6e40448`)

The wa.me redirect timeout was extended from 45s to 120s (`DEFAULT_WA_ME_OPEN_TIMEOUT_SECONDS = 120`). This resolved the `asyncio.TimeoutError` that fired when the intermediate screen consumed ~27s of the original 45s budget, leaving only ~18s for the redirect.

**Validated behavior (HEAD `6e40448`):**
- No more `asyncio.TimeoutError` ✅
- Intermediate screen detected and clicked ✅
- But still fails: `"wa.me: campo de mensagem nao encontrado apos continuar"` ❌

## wa.me fundamental unreliability (discovered 2026-07-07)

Even with the intermediate screen fix and extended timeout, wa.me is fundamentally unreliable for automated sending:

1. **wa.me redirects to `api.whatsapp.com/send/?phone=...`**, not directly to `web.whatsapp.com` with the chat open
2. The "Continuar para o WhatsApp Web" button exists on the page but is **not visible/stable** — `ElementHandle.click` times out with "element is not visible"
3. The intermediate page has a `link` element (not a `button`), and the click action fails because the element is behind a backdrop or not in the viewport
4. Even when the redirect works, it lands on the WhatsApp Web main page (QR code or chat list), not the specific chat — the `div[contenteditable]` selector never matches

**Recommendation: Bypass wa.me entirely.** Instead:
1. Open `web.whatsapp.com` with the sender profile (`.whatsapp_business_profile`)
2. Use the search box to find the contact by phone number
3. Click the contact to open the chat
4. Fill the message in the `div[contenteditable]` compose box
5. Click the send button

This eliminates the intermediate screen, the redirect, and the wa.me dependency entirely. The matcher already demonstrates this pattern (search → click → read) — the sender should use the same approach.
