# campanha_whatsapp.py entrypoint validation

Protocol and known defects from validating the centralized campaign entrypoint.

## Validation sequence

1. `--help` — confirm all expected flags exist
2. `--listar-nichos` — confirm nicho config without browser/lock
3. `plan --until <future> --limit N` — confirm capacity calc and lead selection
4. `plan --nicho X --subnichos A,B` — confirm subnicho filtering
5. `plan --nicho Y --todos-subnichos` — confirm other nicho doesn't mix assistencias
6. `semi --verify-only --limit N --nicho assistencias` — real matcher verification

## Known defect: NameError on LockWhatsAppMatch

**Commit:** before `1c41aee`
**Symptom:**
```
NameError: name 'LockWhatsAppMatch' is not defined. Did you mean: 'LockWhatsAppSender'?
```
**Cause:** `campanha_whatsapp.py` line 38 imports `LockWhatsAppSender` but line 1032 uses `LockWhatsAppMatch`.
**Fix:** Use the correct lock class for the mode. `plan` and `verify-only` should use `LockWhatsAppMatch` (imported from `config.lock_whatsapp_match`).

## Known defect: verification_budget TypeError

**Commit:** before `7fec2ec`
**Symptom:**
```
fazer_match_completo() got an unexpected keyword argument 'verification_budget'
```
**Cause:** `campanha_whatsapp.py` passes `verification_budget=15` to `fazer_match_completo()` but the function signature doesn't accept it.
**Fix:** Either add `verification_budget` to the `fazer_match_completo()` signature or remove the kwarg from the caller.

## Known defect: page=None in matcher

**Commit:** `7fec2ec`
**Symptom:**
```
Locator.count: 'NoneType' object has no attribute 'send'
```
**Cause:** The `page` object passed to the matcher is `None`. The browser context was not initialized or was closed before the matcher runs.
**Fix:** Ensure the browser context lifecycle in `campanha_whatsapp.py` creates and passes a valid `page` to `fazer_match_completo()`.

## Known defect: --dry-run skips verification

`--dry-run` with `--verify-only` short-circuits before calling the matcher. The output shows lead names but no real verification happens. To test the matcher path, omit `--dry-run`.

## Lock/profile separation

| Mode | Lock | Profile |
|------|------|---------|
| verify-only | LockWhatsAppMatch | profiles/whatsapp_match |
| plan | LockWhatsAppMatch | profiles/whatsapp_match (no browser opened) |
| semi (send) | LockWhatsAppSender | .whatsapp_business_profile |
| auto (send) | LockWhatsAppSender | .whatsapp_business_profile |

Never open `.whatsapp_business_profile` or acquire `LockWhatsAppSender` in verify-only or plan mode.