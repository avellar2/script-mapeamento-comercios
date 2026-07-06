---
name: whatsapp-conversation-indexing
description: Privacy-safe indexing of existing WhatsApp Web conversations for reverse reconciliation against lead lists, with virtualized sidebar traversal, resumable checkpoints, and zero-send / zero-write guarantees.
---

# WhatsApp Conversation Indexing

Use this skill when you need to scan existing WhatsApp Web chats to build a local index for matching or reconciliation **without sending messages** and **without writing back to the source system**.

## When to use
- Reverse-match existing WhatsApp conversations against a CRM / Supabase lead table.
- Build a one-time or resumable local index of chats already present in WhatsApp Web.
- Detect whether a specific outbound campaign already happened before deciding on apply/update work.
- Audit outreach coverage without processing the remaining leads one by one.

## Hard safety rules
1. **One persistent context, one WhatsApp tab.** Open `web.whatsapp.com` once and close only at the end.
2. **Never send messages.** No sender flow, no typing into message composer, no Enter in chat body.
3. **No apply during indexing.** Index first, compare second, produce candidates only.
4. **No Supabase writes.** Read-only client only (`SUPABASE_URL` + `SUPABASE_ANON_KEY`). Do not load service role.
5. **Do not persist full phone numbers or full message text.** Persist only hashed / masked identifiers and compact evidence.
6. **Do not advance unrelated operational checkpoints.** Keep the main campaign/sync checkpoint unchanged; use a separate checkpoint for the indexer.

## Recommended workflow
1. Confirm the project path, branch, and the operational checkpoint that must remain untouched.
2. Create a **separate script** for indexing (for example `indexar_conversas_whatsapp.py`).
3. Reuse the established WhatsApp profile (`profiles/whatsapp_match`) unless the user explicitly says otherwise.
4. Traverse the virtualized sidebar with controlled scroll:
   - collect visible rows,
   - derive a sanitized technical key,
   - scroll gradually,
   - stop only after several rounds with no new keys,
   - guard against infinite loops.
5. For each chat:
   - open the row,
   - classify unsupported chat types early,
   - extract phone in strict evidence order,
   - inspect outbound messages only as far as needed to classify the campaign,
   - persist only sanitized fields.
6. Load eligible leads read-only from Supabase.
7. Normalize each lead phone in memory, hash it the same way, and compare against the local index.
8. Output a local sanitized report and a candidate list for later apply.
9. Validate first on a small batch (for example `--limit 20`) before running the full index.

## Sidebar traversal rules
- WhatsApp chat lists are virtualized; do **not** assume a static DOM list.
- Use a two-set approach:
  - **scan_seen_keys**: keys seen during the current traversal so scrolling does not loop forever.
  - **processed_keys**: keys already fully processed and safe to skip on resume.
- Persist only `processed_keys` in the checkpoint.
- Do **not** let “seen while scanning” imply “already processed”. That bug causes silent skips after restart.
- Archived chats are best-effort: try once if the archived entry is available, then merge them into the same dedup model.

## Chat classification rules
Classify unsupported chat types before any heavy extraction.
- Ignore groups, channels, communities, and status.
- Prefer explicit technical signals (URL, data-testid, group/community/channel icons).
- **Pitfall:** do not classify `status` from generic body text containing words like “status” or “WhatsApp”. That heuristic is too broad and can turn real individual chats into false `status` rows.

## Phone confirmation order
Accept a phone only when a full normalized number is confirmed. Use this order:
1. JID containing the phone (for example `@s.whatsapp.net`)
2. explicit technical attribute containing the full phone
3. `tel:` link
4. info panel phone field
5. `aria-label` or `title` containing the complete number

Reject confirmation from:
- contact name
- last digits only
- list position
- message text

## Persistence shape
Persist only sanitized record fields such as:
- `phone_hash` (SHA-256 of canonical phone)
- `phone_last4`
- `chat_type`
- `technical_id_sanitized`
- `outbound_found`
- `anchor_count`
- `campaign_match`
- `timestamp_technical`
- compact evidence label

Never persist:
- full phone number
- raw technical IDs if they contain phone-like data
- full message text
- screenshots / HTML dumps with sensitive data unless the user explicitly asks and the files are excluded from git

## Pitfall: stale_info_panel false positive

The selector `[data-testid*="drawer" i]` always finds 5 elements in the WhatsApp Web DOM:
- `drawer-fullscreen`
- `drawer-left`
- `drawer-middle`
- `drawer-title-body`
- `drawer-right`

These are structural layout drawers that persist regardless of whether the contact info panel is open. Using this selector to check if the info panel is open produces a permanent false positive, causing every chat to return `stale_info_panel`.

**Correct selector for the real info panel:** `[data-testid="chat-info-drawer"]`
- Present in DOM when panel is open (width=420, visible)
- Removed from DOM when panel is closed (count=0 within 100ms of clicking close)
- Close button: `button[aria-label="Fechar"]` (pt-BR locale)

**Correct close confirmation:** Check that `[data-testid="chat-info-drawer"]` count is 0, NOT that `[data-testid*="drawer" i]` is absent.

## Campaign detection
- Detect outbound messages first.
- Check campaign anchors / fingerprint next.
- Stop as soon as there is enough evidence to classify.
- Use explicit statuses such as:
  - `campaign_matched`
  - `outbound_other_campaign`
  - `no_outbound`
  - `phone_unconfirmed`
  - `chat_unsupported`
  - `error`

## Testing checklist
At minimum add tests for:
- virtualized list traversal
- stabilization after repeated no-new-key rounds
- duplicate chats not reprocessed on resume
- groups/channels/communities ignored
- full phone accepted, partial phone rejected
- equal hash finds matching lead
- full message text never persisted
- checkpoint resume behavior
- no apply / no sender / no write guarantees

## Validation protocol
1. Run syntax/compile validation first.
2. Run the new indexer tests.
3. Run the existing target regression pack around WhatsApp matching and dry-run safety.
4. Run the broader suite and compare against the known baseline; the standard is **zero new failures**, not “everything green” when the repo already has pre-existing failures.
5. Run a real `--dry-run --limit 20` pass and inspect the generated sanitized report before any full run.

## Git hygiene
- Commit only code/tests/skill docs.
- Do not commit profiles, outputs, screenshots, raw HTML, credentials, or sensitive artifacts.
- If diagnostics are needed, keep them local and gitignored.

## Reference
- `references/reverse-indexing-notes.md` — concrete pitfalls and implementation notes from a real reverse-indexing session against WhatsApp Web + Supabase.
