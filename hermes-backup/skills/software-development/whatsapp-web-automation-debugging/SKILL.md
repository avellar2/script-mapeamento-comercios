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

## Reference material
- See `references/whatsapp-reverse-index-diagnostics.md` for a reusable checklist and stop conditions.
- See `references/campanha-whatsapp-entrypoint-validation.md` for the entrypoint validation protocol and known defects.
