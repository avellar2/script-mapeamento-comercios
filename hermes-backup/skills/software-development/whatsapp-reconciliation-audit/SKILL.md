---
name: whatsapp-reconciliation-audit
description: Audit WhatsApp reverse-index runs against Supabase and local artifacts, classify matches, isolate errors, and decide whether reprocessing or code fixes are needed.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [whatsapp, supabase, reconciliation, audit, debugging, indexing]
---

# WhatsApp Reconciliation Audit

Use this skill when a WhatsApp reverse-index or reconciliation run has completed and you need to explain:
- what matched,
- what failed,
- whether the failure is reprocessable,
- and whether the next step is more data, reprocessing, or code correction.

## Trigger conditions
- A run folder exists with `resumo.json`, `indice_conversas.jsonl`, `checkpoint.json`, or `candidatos.csv`.
- The user asks for a sanitized diagnosis, candidate list, or control validation.
- A run returns `0` candidates unexpectedly.
- Some chats fail while the rest complete cleanly.

## Core workflow
1. Read the run artifacts first.
   - `resumo.json` for totals and `records`
   - `indice_conversas.jsonl` for one-row-per-chat evidence
   - `checkpoint.json` for scan state and last processed key
   - `candidatos.csv` for final candidate output
2. Classify run-level outputs before inspecting code.
   - Count chats, confirmed phones, outbound matches, campaign matches, and errors.
   - Look for one-hash collapse: many chats sharing one canonical phone hash.
3. Compare against **all** Supabase leads by reading only.
   - Do not restrict to eligible statuses until after the global hash match is known.
   - Confirm pagination explicitly by reading pages until a short page is returned.
4. Cross-check local archives.
   - Search JSON, CSV, SQL, and checkpoint files for the same canonical hash or sanitized control identifiers.
5. Validate known controls.
   - Known controls should be classified as already confirmed, not as new candidates.
6. Decide the next action.
   - If only a few chats fail, reprocess only those chats.
   - If pagination or hash mismatch is proven, escalate for code correction.
   - If the run matches already confirmed leads, report zero apply candidates as expected.

## Required evidence fields
Report only sanitized evidence:
- `technical_id_sanitized`
- `phone_last4`
- `phone_hash` or `phone_hash_parcial`
- `chat_type`
- `outbound_found`
- `anchor_count`
- `campaign_match`
- `status`
- whether the item is known/eligible/unmatched

Never persist or repeat:
- full phone numbers,
- raw JIDs,
- message text,
- cookies,
- tokens,
- or contact names.

## Pagination checklist
- Use explicit page sizes, commonly 1000.
- Keep fetching until a page returns fewer rows than requested.
- Record the total loaded rows.
- Distinguish between:
  - total table size,
  - eligible subset size,
  - and control-only subsets.

## Common pitfalls
- Assuming the first page of Supabase is complete.
- Treating `0` candidates as a bug when all successful chats collapse onto an already-confirmed lead.
- Ignoring local evidence when Supabase does not contain the candidate in an eligible status.
- Trying to infer cause from counts alone without checking the run artifacts.
- Reprocessing the whole dataset when only the final error rows need another pass.

## Decision rules
- **known_confirmed_control**: a known control already confirmed in outreach history.
- **eligible_match**: hash matches an eligible lead and the lead has no prior confirmation.
- **unmatched_any_source**: hash not found in Supabase or local archives.
- **reprocessable_error**: a chat failed before final classification and can be retried safely.

## Verification
Before closing the audit, confirm:
- run totals add up,
- pagination reached the final short page,
- control leads are not misclassified as candidates,
- the zero-candidate explanation is supported by counts,
- and the report remains sanitized.

## Related reference
- `references/whatsapp_reverse_index_audit.md`
