---
name: whatsapp-reverse-reconciliation
description: Validate reverse WhatsApp-to-Supabase matching with a control-positive first, compare canonical phone hashes, and separate confirmed controls from new apply candidates while preserving privacy and checkpoints.
---

# WhatsApp reverse reconciliation

Use this skill when validating or running a reverse indexer that compares WhatsApp Web conversations against Supabase leads by canonical phone hash.

## When to trigger
- Building or verifying a reverse WhatsApp indexer
- Comparing chats to leads without writing to Supabase
- Debugging mismatches between chat-side and lead-side phone hashes
- Generating candidate apply lists from conversation evidence

## Core rules
1. Validate a known control-positive lead first.
2. Use only read-only credentials for Supabase lookups.
3. Canonicalize phones through one shared function: `canonical_phone_hash(phone)`.
4. Never persist full phones, raw JIDs, contact names, or full message text.
5. Keep the main sync checkpoint separate from the reverse-index checkpoint.
6. Do not treat a scan-dedup checkpoint as proof that a chat was fully processed.
7. Separate confirmed controls from eligible apply candidates.
8. Stop before apply, send, or any write.

## Recommended workflow
### 1) Environment check
- Confirm branch and working directory.
- Confirm only read credentials are present.
- Confirm the main sync checkpoint remains unchanged.

### 2) Control-positive validation
- Pick a known reconciled lead.
- Confirm the lead exists in Supabase by read-only query.
- Confirm status and any outreach state available to the current role.
- Search the phone in WhatsApp Web using the validated matcher.
- Confirm: individual chat, full phone extracted, outbound found, campaign fingerprint matches, and chat hash equals lead hash.
- Classify as `known_confirmed_control`.

### 3) Full reverse index
- Use a single persistent WhatsApp Web context and one tab.
- Traverse the virtualized list until stable.
- Deduplicate chat cards by technical key.
- Ignore groups, channels, communities, and status surfaces.
- Save checkpoints progressively, but keep them separate from the main sync checkpoint.

### 4) Comparison and classification
Split results into:
- `known_confirmed_control`
- `eligible_match`
- `not_found_in_leads`
- `phone_unconfirmed`
- `outbound_other_campaign`
- `no_outbound`
- `chat_unsupported`
- `error`

A candidate for apply must satisfy all of:
- phone fully confirmed
- chat hash equals lead hash
- individual conversation
- outbound present
- `campaign_match=true`
- lead is eligible
- not already confirmed as a known control

### 5) Stop conditions
- If the control-positive lead fails at any step, stop the full run.
- Produce a sanitized technical report for later correction.
- Do not patch code in-session unless the task explicitly authorizes edits.

## Privacy checklist
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
- full phone numbers
- raw JIDs containing phone data
- contact names extracted from WhatsApp
- full message bodies
- cookies or tokens

## Pitfalls
- Do not hash partially normalized numbers.
- Do not let scan deduplication skip a chat that still needs processing.
- Do not classify a known control as a new apply candidate.
- Do not rely on a different normalization function on the chat side and the lead side.

## Support files
- references/control-positive-and-privacy.md
