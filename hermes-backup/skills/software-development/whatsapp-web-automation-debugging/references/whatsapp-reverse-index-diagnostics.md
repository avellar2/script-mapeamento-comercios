# WhatsApp reverse-index diagnostics

Use this reference when a WhatsApp Web indexer or matcher behaves like it is reusing the previous chat.

## Symptoms that matter
- `chat_not_changed` dominates the run
- a control-positive matches, but campaign chats do not
- repeated hashes show up without new evidence
- the next chat appears to inherit the previous chat's phone or panel state

## Reproduction pattern
1. Run a small validation batch (about 10 chats) in a single persistent browser context.
2. Capture the active chat identifier before the click.
3. Click the new row/card.
4. Capture the active chat identifier again.
5. Only extract the phone after the identifier change is confirmed.

## What to log
- sanitized chat id
- pre-click active id
- post-click active id
- changed? yes/no
- phone confirmed? yes/no
- source of evidence
- hash partial
- last4
- outbound
- campaign_match
- final status
- elapsed time

## Interpretation
- Many `chat_not_changed` results: investigate the open/switch step before hashing.
- Same hash across multiple chats: suspect stale DOM/panel reuse before normalizing or changing hash logic.
- Control-positive fails: browser state or extraction source is wrong.
- Control-positive passes but campaign run fails: inspect campaign fingerprinting or lead-status filtering.

## Stop conditions
- 3 distinct chats share a hash with no new evidence
- active chat id does not change
- previous chat's phone reappears in the next chat
- a record is attached to the wrong card

## Safe default
If in doubt, stop and diagnose the switch step instead of patching hashing logic.
