---
name: whatsapp-web-automation-debugging
description: "Debug WhatsApp Web automation and reverse-index flows with active-chat verification, sanitized evidence, and control-positive checks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [whatsapp, playwright, browser-automation, debugging, root-cause, evidence]
    related_skills: [software-development:systematic-debugging, test-driven-development]
---

# WhatsApp Web Automation Debugging

Use this skill when validating or debugging WhatsApp Web automation that must read chats, extract phone numbers, and compare hashes without sending messages.

## What this skill is for
- Reverse indexing WhatsApp chats
- Chat switch / active-panel verification bugs
- Phone extraction and hash mismatches
- Control-positive validation flows
- Browser state leaks across chats
- "chat_not_changed" and repeated-hash investigations

## Core workflow

1. **Lock the browser shape**
   - Use one persistent browser context.
   - Use one WhatsApp Web tab.
   - Avoid opening a second automation session against the same profile.

2. **Verify active chat change before extraction**
   - Capture the active chat identifier before clicking a row.
   - Click the new chat.
   - Confirm the active identifier changed.
   - Only then extract phone, outbound evidence, and campaign fingerprint.

3. **Treat `chat_not_changed` as a switch bug first**
   - If multiple chats end with `chat_not_changed`, do not chase hashing yet.
   - Inspect chat opening, DOM selection, focus, virtualization, and stale-panel reuse.
   - A repeated hash with no evidence is usually a downstream symptom of the same switch bug.

4. **Use a control-positive separately**
   - Validate at least one known confirmed control in isolation.
   - Keep the control out of candidate/apply logic.
   - If the control fails, stop and fix the browser/state issue before continuing the campaign run.

5. **Compare with sanitized artifacts**
   - Record only sanitized identifiers, last4, partial hash, outbound, and campaign_match.
   - Do not persist full phone numbers, raw JIDs, or message bodies.

## Stop conditions
Stop immediately when any of these happen:
- Three distinct chats produce the same hash without new evidence.
- The active chat identifier does not change after click.
- A previous chat's phone appears in the next chat.
- `suspicious_repeated_phone` is emitted.
- A record is associated with the wrong card/chat.

## Debugging sequence

### Phase 1: Confirm the browser switch
- Compare pre-click vs post-click chat identifiers.
- Check whether the chat list row actually gained focus/open state.
- Prefer direct DOM reads from the active panel over assumptions from the list.

### Phase 2: Confirm the extraction source
- Verify the phone comes from the currently active panel.
- Check whether archived/virtualized content is still mounted and being reused.
- Ensure the previous panel is closed or invalidated before reading the next chat.

### Phase 3: Confirm the hash pipeline
- Normalize the phone first.
- Hash only the normalized value.
- Compare hash parity between chat evidence and lead evidence.

### Phase 4: Classify safely
- `known_confirmed_control` for verified controls.
- `eligible_match` only when the lead is eligible and not already confirmed.
- `unmatched_any_source` only when the hash is absent from both Supabase and local artifacts.

## Practical heuristics
- A run with many `chat_not_changed` results and zero phone extraction usually indicates a chat-switch bug, not a phone-format bug.
- If a control-positive matches but campaign chats do not, inspect the campaign fingerprint or lead-status filter.
- If the same hash appears across multiple chats, inspect stale DOM reuse before changing normalization code.
- Small validation runs (e.g. 10 chats) are the right first probe after browser-flow changes.
- Generic drawer selectors are often false positives in WhatsApp Web; verify count/visibility/geometry before treating them as an open info panel.
- The real info panel selector is `[data-testid="chat-info-drawer"]`, not `[data-testid*="drawer" i]`. The latter always finds 5 elements (drawer-fullscreen, drawer-left, drawer-middle, drawer-title-body, drawer-right) even when no panel is open.
- If the app is still loading, confirm the search box and side rail exist before probing chat rows or panel selectors.
- For read-only DOM investigations, use temporary browser queries and save only sanitized HTML/screenshots; do not create executable probes in the repo.

## Read-only DOM debugging
When the user explicitly forbids code changes or asks for diagnosis only:
- do not create or modify `.py`, `.js`, `.ts`, tests, configs, or patches
- inspect the live DOM with temporary `querySelector` / `querySelectorAll` / `page.evaluate` reads only
- capture sanitized outerHTML for the specific element(s) under investigation
- report the exact selector, the real element found, and the file/function the Command Code should review
- prefer evidence over assumptions: count visible vs hidden elements, note geometry, and compare before/after states
- if you identify a bug, stop and report it instead of trying to refine the workflow in code

## Operator/Command-Code separation
The user (Vanderson) enforces a strict separation of responsibilities:
- **Hermes** = operator and diagnostician only. Cannot edit code, create scripts, modify tests, apply patches, commit, or push.
- **Command Code** (a separate coding agent or developer) = the only entity allowed to edit code, fix bugs, apply patches, commit, and push.
- When Hermes finds a bug, the protocol is: stop, generate a technical report with file/line/cause/evidence, and hand it to Command Code.
- **Break-the-rule password:** When the user writes the exact phrase "eu to mandando", it authorizes Hermes to break the no-code-edit rule and perform commits, pushes, edits, etc. This is the user's personal override — only valid when the user themselves types it. Treat it as full authorization for git operations and code edits for that turn only.

## Evidence checklist
For each inspected chat, capture:
- sanitized chat id
- pre-click active id
- post-click active id
- whether the id changed
- whether phone extraction succeeded
- partial hash
- last4
- outbound flag
- campaign_match flag
- final status
- elapsed time

## Entrypoint validation (campanha_whatsapp.py)

When validating a new centralized campaign entrypoint that wraps the matcher:

1. **Confirm `--listar-nichos` first** — it exits before acquiring any lock or opening a browser, so it isolates the niche/subnicho config without side effects.
2. **`plan` mode should not open a browser** — if it crashes before any Supabase query, suspect a lock/import mismatch (e.g. `LockWhatsAppMatch` used but only `LockWhatsAppSender` imported).
3. **`verify-only` with `--dry-run` skips real verification** — the dry-run path short-circuits before calling the matcher. To test the matcher path, run `--verify-only` *without* `--dry-run`.
4. **`verification_budget` parameter compatibility** — if `fazer_match_completo()` does not accept `verification_budget` as a kwarg, every lead gets `verification_error`. The caller must match the function's actual signature.
5. **`page` arriving as `None`** — if the matcher receives a `None` page object, all locator calls fail with `'NoneType' object has no attribute 'send'`. This means the browser context was not initialized or was closed before the matcher runs. Check the context lifecycle in the entrypoint, not in the matcher.
6. **Verify lock identity** — `verify-only` should acquire `LockWhatsAppMatch` (matcher lock), NOT `LockWhatsAppSender`. The sender profile (`.whatsapp_business_profile`) must never be opened in verify-only mode.

## Common NameError pattern
When a new entrypoint imports one lock class but uses another:
- Symptom: `NameError: name 'LockWhatsAppMatch' is not defined. Did you mean: 'LockWhatsAppSender'?`
- Cause: The import line uses the sender lock but the `with` statement uses the matcher lock name (or vice versa).
- Fix: Ensure the import matches the `with` statement. The entrypoint should import the lock it actually uses.

## Info-panel DOM evidence (confirmed 2026-07-05)

### Real panel root
- Selector: `[data-testid="chat-info-drawer"]`
- When open: `width=420, height=1000, display=flex, visible=true`
- When closed: **removed from DOM entirely** (count=0 within 100ms of clicking close)
- Close button: `button[aria-label="Fechar"]` (pt-BR locale), `40x40px`, positioned at top-left of the drawer

### False-positive selectors (DO NOT use for panel-open check)
- `[data-testid*="drawer" i]` — always finds 5 structural elements: `drawer-fullscreen`, `drawer-left`, `drawer-middle`, `drawer-title-body`, `drawer-right`
- `drawer-right` stays in DOM when closed but has `width=0` — not a reliable signal alone
- `[data-testid="contact-info"]` — count=0 even when panel is open (not the right selector in current WhatsApp Web)
- `div[data-testid="info-panel"]` — count=0 even when panel is open
- `div[aria-label*="contact info" i]` — count=0

### Opening the panel
- Click `[data-testid="conversation-info-header"]` (a `div[role="button"]` inside the conversation header)
- Panel appears within ~500-800ms

### Closing the panel
- Click `button[aria-label="Fechar"]` inside the drawer
- Panel is removed from DOM within 100ms
- No animation delay observed — `chat-info-drawer` count goes to 0 immediately

### Chat switch verification
- `aria-selected="true"` on the chat list row confirms selection
- The `#main` header title (`[data-testid="conversation-info-header-chat-title"]`) changes between chats
- Signature composed of conversation-header title + first/last message data-id + selected card title provides reliable switch detection

## Semi-sender validation

When validating a fix to the semi-mode sender flow (especially `input()` threading, timeout, manual confirmation stages, or `--semi-confirm-token`), follow the protocol in `references/semi-sender-validation.md`.

Key pre-flight checks before any semi-mode test:
1. Confirm the fix commit is an ancestor of HEAD
2. Confirm the latest WIP commit did NOT touch `campanha_whatsapp.py` or sender tests
3. Check for stale locks (`whatsapp_sender_global.lock`, `whatsapp_match.lock`)
4. Check for pending reservations via `recover-reserved --dry-run`
5. Run `plan` first to confirm the entrypoint works without opening a browser
6. **Verify `.whatsapp_business_profile` is logged in** — open `web.whatsapp.com` with the sender profile and check for QR code. If QR code appears, the session expired and must be re-authenticated before any semi test. `wa.me` will redirect to QR code, not the chat, causing a 45s timeout.

### Token-based confirmation (`--semi-confirm-token`)

Commit `fb687e0` added `--semi-confirm-token` for non-interactive confirmation (agents/CI). The token format is:

```
CONFIRMAR-<last4>-<run_id_curto>
```

Where `<last4>` are the last 4 digits of the normalized phone and `<run_id_curto>` is the short run ID (e.g. `hermes002` from `run_20260707_hermes002`).

Validated stages with token (HEAD `fb687e0`):
- `manual_confirmed` ✅ (via token, not `input()`)
- `post_manual_confirmed` ✅
- `wa_me_opening` ✅

The token is not a secret — it only authorizes the send pipeline to proceed, derived from data already visible in `plan` output.

### wa.me intermediate screen (commit `71e45d5`)

`wa.me/<phone>?text=...` does NOT redirect directly to a WhatsApp Web chat. It shows an intermediate landing page with:

- Heading: "Conversar com +55 XX XXXX-XXXX no WhatsApp"
- Two buttons: "Abrir app" and **"Continuar para o WhatsApp Web"**

The old code (`abrir_wa_me` before `71e45d5`) did `page.goto(wa.me_link)`, waited 3s, then searched for `div[contenteditable="true"]` — which doesn't exist on the intermediate page. Result: "Campo de mensagem não encontrado" → `wa_me_falha`.

The fix (`71e45d5`) detects the intermediate screen, clicks "Continuar para o WhatsApp Web", then waits for the message field on `web.whatsapp.com`.

**Critical dependency:** The "Continuar para o WhatsApp Web" button redirects to `web.whatsapp.com`. If the sender profile (`.whatsapp_business_profile`) session is expired (QR code), the redirect lands on the QR code page, not the chat. The 45s timeout for `wa_me_loaded` will fire. **Always verify the sender session is active before testing semi mode.**

### Diagnosing wa.me failures

When `semi` fails at `wa_me_falha` or times out after `wa_me_opening`:

1. Check if the sender profile is logged in (open `web.whatsapp.com` with `.whatsapp_business_profile`)
2. If QR code → session expired, user must scan before retrying
3. If logged in → check if the wa.me intermediate screen was handled (look for "tela intermediaria" in logs)
4. If intermediate screen was handled but still timed out → check if the phone number has WhatsApp (open `wa.me/<phone>` manually and observe)
5. Do NOT click "Enviar" during diagnosis

Expected stages after manual confirmation (`s` or token): `manual_confirmed` → `post_manual_confirmed` → `wa_me_opening` → (intermediate screen handling) → `wa_me_loaded` → ... → `send_clicked` → `settle_sent_done`.

### wa.me timeout fix (commit `6e40448`)

The wa.me redirect timeout was extended from 45s to 120s (`DEFAULT_WA_ME_OPEN_TIMEOUT_SECONDS = 120`). This resolved the `asyncio.TimeoutError` that fired when the intermediate screen consumed ~27s of the original 45s budget, leaving only ~18s for the redirect.

**Validated behavior (HEAD `6e40448`):**
- No more `asyncio.TimeoutError` ✅
- Intermediate screen detected and clicked ✅
- But still fails: `"wa.me: campo de mensagem nao encontrado apos continuar"` ❌

### wa.me fundamental unreliability (discovered 2026-07-07)

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

## Reference material
- See `references/whatsapp-reverse-index-diagnostics.md` for a reusable checklist and stop conditions.
- See `references/campanha-whatsapp-entrypoint-validation.md` for the entrypoint validation protocol and known defects.
- See `references/github-multi-repo-push.md` for the multi-repo GitHub push workflow with Hermes skills+memory backup.
- See `references/semi-sender-validation.md` for the semi-mode sender validation protocol, pre-flight checks, expected stages, and failure modes.
- See `references/wa-me-intermediate-screen.md` for wa.me landing page handling, token-based semi confirmation, and sender session diagnostics.
