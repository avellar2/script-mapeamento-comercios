# Multi-repo GitHub push with Hermes backup

When the user asks to push everything to GitHub (trigger phrase: "push no gitb" or similar), the config is:

## Repos
1. `C:\projetos\saas-gestão` → `github.com/avellar2/saas-gestao.git`
2. `C:\projetos\script-mapear-comercios-whatsapp-dedup` → `github.com/avellar2/script-mapeamento-comercios.git`
3. `C:\projetos\script-mapear-comércios` → `github.com/avellar2/script-mapeamento-comercios.git` (same remote as #2)

## Push sequence
1. For each repo: `git add -A && git commit -m "..." && git push origin <current-branch>`
2. Push ALL branches: `git push --all origin`
3. If a branch is rejected (remote ahead): `git pull origin <branch> --no-edit && git push origin <branch>`
4. For the `script-mapear-comércios` repo, also push the `hermes-skills-e-memoria` branch separately if it exists

## Pull sequence (when user asks to sync from GitHub)
1. For each repo: `git pull origin <current-branch>`
2. If on `master` and the working branch is different, switch to the working branch first
3. Handle lock files: if `.git/index.lock` exists, `rm -f .git/index.lock`
4. Handle local changes blocking checkout: `git stash push --include-untracked -m "stash before switch"` then checkout

## Hermes skills + memory backup
- Create a branch `hermes-skills-e-memoria` in repo #3
- Copy skills from `~/AppData/Local/hermes/skills/` into `hermes-backup/skills/`
- Export memory content into `hermes-backup/memoria/MEMORY.md`
- Commit and push that branch

## Memory update after pull
When the user asks to pull repos AND update the memory backup:
1. Pull all repos first
2. Switch to `hermes-skills-e-memoria` branch in repo #3
3. Read current memory content from Hermes (via memory tool)
4. Rewrite `hermes-backup/memoria/MEMORY.md` with current content
5. If nothing changed, `git commit` will say "nothing to commit" — that's fine, memory is in sync
6. Switch back to the working branch (e.g. `master` or `feat/protecao-duplicidade-whatsapp`)
7. Restore stashed changes if any: `git stash pop`

## Authorization
This operation requires the user's break-the-rule password: "eu to mandando". Without it, Hermes cannot commit or push (per the permanent operator rule).

## Pitfalls
- The `script-mapear-comércios` repo has the same remote as `script-mapear-comercios-whatsapp-dedup` — pushing branches from one can affect the other's remote tracking
- `hermes-backup/memoria/MEMORY.md` only exists on the `hermes-skills-e-memoria` branch — it won't be visible on `master` or other branches
- Memory is dynamic — the backup file is a snapshot at push time. New memory entries after the push won't be in the file until the next push
- If `git stash` was used to switch branches, remember to `git stash pop` after finishing the memory update
