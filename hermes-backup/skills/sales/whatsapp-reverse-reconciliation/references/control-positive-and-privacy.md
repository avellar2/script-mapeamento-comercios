# Control-positive and privacy checklist for WhatsApp reverse reconciliation

Use this as the operational playbook when validating a reverse WhatsApp indexer against Supabase.

## Control-positive first
- Always validate one known reconciled lead before any large run.
- Confirm in read-only Supabase first: `lead_id`, canonical phone, status, and any outreach record available to the current role.
- Then confirm in WhatsApp Web: conversation exists, it is individual, outbound is present, and campaign fingerprint matches.
- If the control does not pass, stop the full run and diagnose before proceeding.

## Canonical phone hash rule
- Raw phone -> Brazilian canonical normalization -> digits only -> one unique canonical format -> SHA-256 over UTF-8.
- Use one shared function for both chat-side and lead-side hashing.
- Never hash partially normalized strings or formatted variants.

## Privacy rules
Persist only:
- phone hash
- last 4 digits
- irreversibly masked technical identifier
- chat type
- outbound flag
- anchor count
- campaign_match
- timestamps
- masked lead_id

Never persist:
- full phone number
- raw JID containing phone
- contact name extracted from WhatsApp
- full messages
- cookies or tokens

## Checkpoint rules
- Keep the main sync checkpoint separate from the reverse-index checkpoint.
- A scan-dedup checkpoint must not imply that a chat was fully processed.
- Reprocessing an explicit control is allowed only through the control path, not by clearing the primary checkpoint blindly.

## Output separation
Keep the report split into:
- known_confirmed_control
- eligible_match
- not_found_in_leads
- phone_unconfirmed
- outbound_other_campaign
- no_outbound
- chat_unsupported
- error

## Diagnostic order when a control fails
1. search / open chat
2. phone extraction
3. canonical hash comparison
4. outbound detection
5. campaign fingerprint
6. Supabase lookup / row selection

## Operational stop condition
If the control-positive lead fails on any step, do not continue to full indexing. Produce a sanitized technical report for later correction.
