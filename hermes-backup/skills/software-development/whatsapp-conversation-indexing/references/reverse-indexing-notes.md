# Reverse indexing notes

Session-derived implementation notes for privacy-safe WhatsApp conversation indexing.

## Core pattern
- Build a local index from existing WhatsApp chats first.
- Compare that local index to eligible leads second.
- Produce candidates for later apply, but do not apply during indexing.

## Proven constraints
- Keep the campaign sync checkpoint unchanged; the indexer must have its own checkpoint.
- Use `profiles/whatsapp_match` with one persistent context and one WhatsApp tab.
- Supabase access stays read-only with anon credentials only.

## Important pitfall: seen vs processed
Do not use one set for both traversal dedup and resume state.

Use:
- `scan_seen_keys`: current-run dedup while traversing the virtualized list.
- `processed_keys`: only chats that fully finished processing and are safe to skip after restart.

If you persist scan-only keys as processed, restarts silently skip chats that were merely seen but never opened.

## Important pitfall: false status detection
A broad heuristic like “body contains status/WhatsApp/atualiza” is too aggressive and can classify ordinary chats as `status`.

Safer choices:
- explicit URL signal such as `/status`
- explicit technical selectors / identifiers
- group/community/channel icons for non-individual chats

## Privacy persistence rules
Persist only:
- SHA-256 of canonical phone
- last 4 digits
- sanitized technical chat id
- chat type
- outbound/campaign flags
- anchor count
- technical timestamp
- compact evidence label

Do not persist:
- full phone number
- raw technical id if it may contain a phone
- full message body

## Real validation outcome pattern
A healthy first batch can look like:
- 20 chats indexed
- phones confirmed
- outbound found in a subset
- campaign matches found in a subset
- zero candidates if none of those matched the current eligible-lead table

That outcome still validates the indexer; candidate count depends on overlap with the lead snapshot.

## Suggested validation sequence
1. `python -m py_compile indexar_conversas_whatsapp.py tests/test_indexar_conversas_whatsapp.py`
2. new indexer tests
3. target regression pack around matcher/dry-run/browser lifecycle
4. full suite checked against baseline for zero new failures
5. `python indexar_conversas_whatsapp.py --dry-run --limit 20`

## Useful test categories
- virtualized scroll stabilizes
- duplicates are not reprocessed
- unsupported chat types ignored
- full phone accepted / partial rejected
- no full text in persisted artifacts
- no sender / no apply / no write paths present
