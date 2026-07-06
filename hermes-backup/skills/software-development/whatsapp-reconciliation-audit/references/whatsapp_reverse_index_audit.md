# WhatsApp reverse-index audit notes

## What to read from a run folder
- `resumo.json` — top-level counts, timings, and the `records` array.
- `indice_conversas.jsonl` — one sanitized row per processed chat.
- `checkpoint.json` — last processed chat key and scan state.
- `candidatos.csv` — final candidate list, often empty when the run collapses onto already-known leads.

## Sanitation pattern
Keep only:
- `technical_id_sanitized`
- `phone_hash` or partial hash
- `phone_last4`
- `chat_type`
- `outbound_found`
- `anchor_count`
- `campaign_match`
- `timestamp_technical`

Do not persist:
- raw phone
- raw JID
- message text
- contact name

## Common classification logic
- `campaign_matched`: phone confirmed + outbound found + campaign match true
- `error`: chat extraction failed before phone/outbound/campaign could be established
- `known_confirmed_control`: a known lead whose hash already exists in outreach history
- `eligible_match`: hash matches a lead in an eligible status and has not been previously confirmed

## Pagination checklist for Supabase
- Query with an explicit page size (commonly `1000`)
- Continue until a page returns fewer rows than the limit
- Count total rows loaded and report it explicitly
- Do not assume the first page is complete
- If the report says a lower count than expected, verify whether that is a filtered subset (e.g. eligible statuses only)

## RPC note
For outreach reconciliation in this repository, the anon-readable state RPC is called with:
- `p_phone_normalized`
- `p_campaign_key`

If the caller uses different parameter names, PostgREST may return a schema-cache mismatch even when the function exists.

## Real-run gotcha
A run can produce 180 successful campaign-matched chats but still 0 apply candidates if all hashes collapse to a single lead that is already `abordado`.
