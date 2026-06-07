# WhatsApp Extraction Playbook

## Two-Phase Approach (Working, tested 2025-06)

The original `extrair_historico_whatsapp.py` script relied on `div[data-testid="chat-list-item"]` selectors which no longer work. The WhatsApp Web DOM changed. Use this two-phase approach instead:

### Phase 1: Extract chat names with Playwright

```python
from playwright.sync_api import sync_playwright
import json, re, time

p = sync_playwright().start()
browser = p.chromium.launch_persistent_context(
    user_data_dir='.whatsapp_profile',  # saves session after QR scan
    headless=False,
    args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport={'width': 1280, 'height': 800},
)

page = browser.pages[0] if browser.pages else browser.new_page()
page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')
page.wait_for_selector('div[data-testid="chat-list"]', timeout=180000)

# Scroll to load all chats
for i in range(15):
    page.evaluate('document.querySelector(\'div[data-testid="chat-list\"]\').scrollTop += 800')
    time.sleep(0.8)

# Extract all span[title] from chat list
chat_names = page.evaluate('''() => {
    const chatList = document.querySelector('[data-testid="chat-list"]');
    if (!chatList) return [];
    const spans = chatList.querySelectorAll('span[title]');
    const results = [];
    const seen = new Set();
    spans.forEach(s => {
        const title = s.getAttribute('title') || '';
        if (title && !seen.has(title)) {
            seen.add(title);
            results.push(title);
        }
    });
    return results;
}''')

with open('output/whatsapp/chat_names.json', 'w', encoding='utf-8') as f:
    json.dump(chat_names, f, ensure_ascii=False, indent=2)

browser.close()
p.stop()
```

### Phase 2: Process in Python (no browser needed)

Data is intercalated: phone entries (`+55 21 9XXXX-XXXX`) alternate with message/name entries.

**Important**: Short phrases like "Sem compromisso, pode", "Obrigada. Ótimo final de semana", "Eu já tenho, obrigada" are **message previews from lead conversations**, NOT contact names. They correspond to phone numbers already extracted in the same list.

```python
import json, re, csv
from datetime import datetime, timedelta

with open('output/whatsapp/chat_names.json', 'r', encoding='utf-8') as f:
    chat_names = json.load(f)

MEU_NUMERO = '5521998438522'
EXCLUIR = ['lucia (vandinho)', 'padre paulo ricardo', 'tim brasil', 'carol nora cunhada']

leads = []
sem_numero = []
seen = set()

for name in chat_names:
    nc = name.replace('\u202a','').replace('\u202c','').replace('\u200e','').replace('\u200f','').strip()
    nl = nc.lower()
    
    # Skip system messages and excluded contacts
    skip = ['WhatsApp Business', 'lista de transmissão', 'LISTAGEM',
            'compartilhe sua chave pix', 'mensagens temporárias', 'serviço seguro da Meta']
    if any(s.lower() in nl for s in skip): continue
    if len(nc) > 200: continue
    if any(x in nl for x in EXCLUIR): continue
    
    # Phone pattern: +55 21 9XXXX-XXXX
    phone_match = re.search(r'\+55\s*(\d{2})\s*(\d{4,5})-?(\d{4})', nc)
    if phone_match:
        telefone = f'55{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}'
        if telefone == MEU_NUMERO or telefone in seen: continue
        seen.add(telefone)
        leads.append({'telefone': telefone, 'nome_wpp': phone_match.group(0), 'status': 'abordado'})
    elif len(nc) < 60:
        sem_numero.append({'nome': nc, 'observacao': 'Telefone não identificado'})
```

### Phase 3: Cross-reference "sem telefone" contacts with leads database

Contacts without visible phone numbers in WhatsApp are **NOT missing data** — they are leads that were contacted through the project's lead panel. Cross-reference by name:

**Data sources to search (in order):**
1. `output/playwright/leads_sem_site.csv` — primary leads database (~4,372 entries)
2. `output/playwright/todos_comercios.csv` — all mapped businesses (larger set)
3. `output/consolidado/base_emails_consolidada.csv` — email campaign leads
4. SQLite local: `output/painel/prospeccao.db` table `leads`

**Matching strategy:**
- Use partial name matching (both directions): `nome_busca.lower() in nome_db.lower() or nome_db.lower() in nome_busca.lower()`
- For compound names, split into keywords and match any: `any(keyword in nome_db.lower() for keyword in ['karina', 'gazetta'])`
- Instagram handles in WhatsApp message previews can help identify businesses (e.g., `@ferlainenevescabelireira`)
- When matching in SQLite, be careful with generic matches — always verify the niche/city matches expectations

**Steps:**
1. For each contact without a phone number, search all data sources by name
2. When found, extract the telefone, nicho, cidade, and score
3. Mark as `no_banco: SIM` if found in the project database
4. For contacts NOT found in any source, mark as needing manual verification
5. **Always present the cross-referenced list to the user** for confirmation before importing — the user knows their contacts better than the script
6. When the user provides missing phone numbers manually, update the CSV immediately before importing

**Output:**
- `historico_whatsapp.csv` — ALL leads (with phone + cross-referenced "sem telefone") — saved with `encoding='utf-8-sig'`
- `contatos_sem_numero.csv` — leads still without phone after cross-referencing

### Phase 4: Import to Supabase

```bash
python importar_historico_whatsapp.py --arquivo output/whatsapp/historico_whatsapp.csv
```

**After import, verify:**
- Run a Supabase query for `status = 'abordado'` to confirm count
- Check that `ultimo_contato_em` and `proximo_followup_em` (7 days out) are set
- Verify that leads no longer appear in `vw_leads_para_abordar`

## Key Bugs Found and Fixed

### Bug 1: `launch_persistent_context` double argument
**Error**: `TypeError: BrowserType.launch_persistent_context() got multiple values for argument 'user_data_dir'`
**Fix**: Pass `user_data_dir=str(perfil)` as keyword arg only, NOT as first positional arg.

### Bug 2: Phone extraction returns own number
The old script clicked each conversation to read the phone from the chat header. This **always returns the user's own number** (5521998438522) because the header shows the active account.
**Fix**: Parse phone numbers directly from `span[title]` text in the chat list. No clicking needed.

### Bug 3: Stale selector `chat-list-item`
`div[data-testid="chat-list-item"]` returns 0 elements in current WhatsApp Web.
**Fix**: Use `span[title]` inside `div[data-testid="chat-list"]`.

### Bug 4: `input()` in background scripts
Running scripts with `notify_on_complete` causes `EOFError` on `input()` prompts.
**Fix**: Remove or comment out `input()` confirmation prompts. Use auto-proceed or CLI flags.

### Bug 5: SQLite generic match returns wrong lead
When searching SQLite by name, a `LIKE '%nome%'` or partial match can return the wrong lead if multiple have similar names. The first match in `leads_db_list` may be wrong.
**Fix**: Always verify niche/city match. Use bidirectional partial matching: `nome_busca in nome_db or nome_db in nome_busca`. For ambiguous matches, try keyword-based matching with AND logic.

### Bug 6: CSV BOM encoding breaks import (CRITICAL)
**Error**: When a CSV is saved with `encoding='utf-8-sig'` (Python's csv module with BOM), and read with `encoding='utf-8'` (no BOM), the first column header gets an invisible `\ufeff` prefix. So the column name becomes `\ufefftelefone` instead of `telefone`.
**Result**: `row.get('telefone', '')` returns `''` for ALL rows → all phones normalizado to `None` → all rows skipped as "sem tel válido" with **0 errors and 0 warnings**. The import silently does nothing.
**Fix**: Always use `encoding='utf-8-sig'` when reading CSVs that were saved with BOM. The `importar_historico_whatsapp.py` script was patched (line 74) to use `utf-8-sig`.
**Pattern**: Any script that reads CSVs produced by other scripts in this project should use `utf-8-sig` to be safe.

## Excluded Contacts (NOT leads)

These WhatsApp contacts are personal/system and should always be removed:
- **Lucia (Vandinho)** — personal contact
- **Padre Paulo Ricardo** — not a business
- **TIM Brasil** — telecom/system
- **Carol Nora Cunhada** — personal contact

## Output Files

| File | Description |
|------|-------------|
| `output/whatsapp/chat_names.json` | Raw extracted chat titles |
| `output/whatsapp/historico_whatsapp.csv` | Processed contacts with phone, status, follow-up date (utf-8-sig encoded) |
| `output/whatsapp/contatos_sem_numero.csv` | Contacts without visible phone number |

## Session Results (2025-06-05)

- 95 conversations found in WhatsApp
- 32 contacts with phone numbers extracted (22 in database, 10 new)
- 9 contacts without phone numbers → 7 recovered via name cross-reference, 2 via user input (Ferlaine: 21 993057764, Advogada Cristiane: 21 999462584)
- 4 excluded (Lucia, Padre, TIM, Carol)
- 41 total leads abordados imported to Supabase successfully
- Critical BOM encoding bug discovered and fixed in `importar_historico_whatsapp.py`