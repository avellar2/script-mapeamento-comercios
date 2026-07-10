# Protocolo de Auditoria — 2026-07-09

## Contexto

Auditoria post-lote de dois lotes de WhatsApp (002 e 003) rodados em 2026-07-09.

## Regras da auditoria (read-only)

- Não editar arquivos
- Não criar scripts
- Não fazer commit/push
- Não executar semi/auto/confirm-live-send
- Não enviar mensagem
- Não clicar Enviar/Tentar novamente
- Não apagar profiles/cookies/diretórios
- Não alterar banco

Pode: consultar logs/checkpoints, Supabase (leitura), comandos read-only, verificar reservas, relatar.

## Verificações por etapa

### 1. Confirmar ambiente

```bash
git status --short && git rev-parse HEAD && git branch --show-current
```

Esperado: `e1ceb2f`, `feat/protecao-duplicidade-whatsapp`, status limpo.

### 2. Checar reservas

```bash
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
```

Relatar: se há reserva pendente (0 = bom).

### 3.Checkpoint

Runs ficam em `output/avgestao/campanha_runs/<run_id>/checkpoint.json`.

Campos importantes:
- `sent_leads[]`: `{lead_id, phone_hash, sent_at, stage}`
- `failed_leads[]`: `{lead_id, reason, stage, failed_at}`
- `skipped_leads[]`: `{lead_id, reason, skipped_at}`

### 4. Queries Supabase (REST API, service role)

```python
import os
from dotenv import load_dotenv; load_dotenv()
import requests

SUPABASE_URL = os.environ['SUPABASE_URL']
SERVICE_KEY = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {'apikey': SERVICE_KEY, 'Authorization': f'Bearer {SERVICE_KEY}'}
```

**Outreach sent (por campaign_key):**
```
GET /rest/v1/lead_outreach?campaign_key=eq.avgestao%3Aassistencias%3Aprimeiro_contato%3Av1&status=eq.sent&select=id,lead_id,phone_normalized,status,error_code,source&limit=50
```

**Outreach por phone_normalized (cross-reference):**
```
GET /rest/v1/lead_outreach?phone_normalized=in.(CSV_OF_PHONES)&campaign_key=eq.KEY&select=id,lead_id,phone_normalized,status,error_code,source
```

**Leads por ID:**
```
GET /rest/v1/leads?id=in.(CSV_OF_IDS)&select=id,nome,telefone_normalizado,status,whatsapp,subnicho
```

**Outreach por lead_id (ambiguous check):**
```
GET /rest/v1/lead_outreach?lead_id=in.(CSV_OF_LEAD_IDS)&campaign_key=eq.KEY&select=id,lead_id,phone_normalized,status,error_code,source
```

### 5. Análise de ambiguous_contact

Para os bloqueados, verificar:
1. Overlap de phone com enviados (deve ser 0 se genuíno)
2. Status dos registros de outreach (devem ser todos `released` se nunca enviados)

**Genérico vs falso positivo:**
- Genuíno: overlap 0, registros released
- Falso positivo: overlap > 0 OU registros incluem sent

## Findings da auditoria 2026-07-09

### Lote 002 (run_20260709_lote_ate_1730_002)
- 23 enviados: todos `sent` no DB, zero erros
- 3 falhas wa.me (web.whatsapp confirmou) → não gerou sent
- 4 bloqueados (1 already_confirmed, 3 ambiguous)
- Verificados: 0 overlap ambiguous/enviados

### Lote 003 (run_20260709_lote_ate_1730_003)
- 0 enviados, 3 falhas wa.me, 31 bloqueados
- Os 3 falhados já haviam falhado no lote 002 (mesmos phones)
- 29 ambiguous: 0 overlap com enviados do lote 002
- 70 registros de outreach dos ambiguous: todos `released`

### 3 phones a excluir (falha recorrente em wa.me)
- 5521990498187 (Lucas Cell)
- 5521972110013 (ARY GAMES)
- 5521965801085 (Manutenção de impressoras)

**Nota:** Status no DB é `released` + `failed settle_failed` — não gerou sent. Leads permanecem `novo`. Recomendação: adicionar à exclusão.

## Queries de verificação rápidas

```python
# Verificar 3 inválidos
phones = ['5521990498187','5521972110013','5521965801085']
phones_csv = ','.join(phones)
# GET /rest/v1/lead_outreach?phone_normalized=in.(phones_csv)&campaign_key=eq.AVGESTAO_KEY
# Esperado: todos released/failed, nenhum sent

# Cross-reference batch 002 vs DB sent
batch2_phones = {'5521969237790','5521997154469',...}  # 23 phones do lote 002
# GET /rest/v1/lead_outreach?campaign_key=eq.KEY&status=eq.sent&select=phone_normalized
# Comparar: batch2 deve estar contido no DB sent
```
