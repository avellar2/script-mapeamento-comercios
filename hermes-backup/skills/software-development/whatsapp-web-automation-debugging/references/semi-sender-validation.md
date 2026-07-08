# Semi Sender Validation Protocol

Use this when validating a fix to the semi-mode sender flow, especially after changes to `input()` threading, timeout, or manual confirmation stages.

## Pre-flight checks

1. **Confirm the fix commit is an ancestor of HEAD**
   ```bash
   git merge-base --is-ancestor <FIX_COMMIT> HEAD && echo FIX_PRESENT
   ```

2. **Confirm the latest WIP commit did NOT touch `campanha_whatsapp.py` or sender tests**
   ```bash
   git show --name-only --oneline HEAD
   ```
   If it touched the entrypoint or sender logic, stop and report before testing.

3. **Check for stale locks**
   ```bash
   ls -la output/avgestao/whatsapp_sender_global.lock output/avgestao/whatsapp_match.lock
   ```
   If either exists, stop and ask for authorization before removing.

4. **Check for pending reservations**
   ```bash
   python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
   ```
   Only continue if 0 pending. This command requires `SUPABASE_SERVICE_ROLE_KEY` in `.env`.

5. **Run `plan` first** to confirm the entrypoint works without opening a browser
   ```bash
   python campanha_whatsapp.py plan --until <FUTURE_TIME> --limit 1 --nicho assistencias --message-template templates/avgestao_assistencias_primeiro_contato.txt
   ```
6. **Verify `.whatsapp_business_profile` is logged in** — open `web.whatsapp.com` with the sender profile and check for QR code. If QR code appears, the session expired and must be re-authenticated before any semi test. `wa.me` will redirect to QR code, not the chat, causing a 45s timeout.

## Execution

Run semi mode with 1 lead only:

```bash
python campanha_whatsapp.py semi --limit 1 --nicho assistencias --until <FUTURE_TIME> --interval-minutes 5 --verification-budget-seconds 15 --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

Never use `auto` or `--confirm-live-send` during validation.

## Expected stages after manual confirmation (`s`)

After the user types `s` and presses Enter, the following stages should appear in order:

```
manual_confirmed
post_manual_confirmed
wa_me_opening
wa_me_loaded
chat_identity_checking
chat_identity_checked
existing_message_checking
existing_message_checked
message_box_searching
message_box_ready
message_filling
message_filled
send_button_searching
send_button_ready
send_clicking
send_clicked
outbound_confirming
settle_sent_done
```

## Stop conditions (do NOT send)

Stop without sending if any of these occur:

- Lead is not `safe_to_send`
- Phone diverges between reservation and chat
- Contact is ambiguous
- Previous AVGESTÃO message exists in the chat
- Wrong chat opened
- Send button does not appear
- User does not confirm (timeout or `n` response)
- Reservation error
- Settle error
- Lock error

## Failure modes

### Failure before click
- `send_clicked` must be `False`
- Must NOT generate `send_clicked_needs_reconciliation`
- Reservation must be released by the official flow
- Do NOT retry automatically

### Failure after click
- Record whether `send_clicked=True`
- If outbound cannot be confirmed, may generate `send_clicked_needs_reconciliation`
- Report for manual reconciliation

## Post-test verification

```bash
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
```

Confirm:
- 0 pending reservations
- No stale locks
- Only 1 lead processed
- No messages sent without confirmation

## Known defects (July 2026)

- `recover-reserved` requires `SUPABASE_SERVICE_ROLE_KEY` which may not be in `.env`
- Stale locks from killed processes block execution — must be removed manually
- `page` arriving as `None` in the matcher causes all locator calls to fail with `'NoneType' object has no attribute 'send'`
- **wa.me intermediate screen** — `wa.me` shows a "Continuar para o WhatsApp Web" landing page before redirecting to the chat. If not handled, `Campo de mensagem não encontrado` occurs. Fixed in commit `71e45d5`.
- **Sender session expiry** — if `.whatsapp_business_profile` is not logged in, `wa.me` redirects to QR code, not the chat. The 45s timeout fires and the lead gets `wa_me_falha`. Always verify the sender session before testing semi mode.

## Token-based confirmation (`--semi-confirm-token`)

Commit `fb687e0` added `--semi-confirm-token` for non-interactive confirmation (agents/CI). Token format:

```
CONFIRMAR-<last4>-<run_id_curto>
```

Example: `CONFIRMAR-3966-hermes002`

- `<last4>` = last 4 digits of normalized phone (from `plan` output `****3966`)
- `<run_id_curto>` = short run ID suffix (e.g. `hermes002` from `run_20260707_hermes002`)

The token is NOT a secret — it is derived from data already visible in `plan` output.

Full command:
```bash
python campanha_whatsapp.py semi \
  --limit 1 --nicho assistencias --until 23:59 \
  --interval-minutes 5 --verification-budget-seconds 15 \
  --run-id run_20260707_hermes002 \
  --semi-confirm-token "CONFIRMAR-3966-hermes002" \
  --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

Validated stages with token (HEAD `fb687e0`): `manual_confirmed` ✅ → `post_manual_confirmed` ✅ → `wa_me_opening` ✅.

See `references/wa-me-intermediate-screen.md` for full details on wa.me landing page handling and sender session diagnostics.
