# CONTINUAR EM CASA

## Branch atual
`feat/protecao-duplicidade-whatsapp`

## Último commit
`c93209e` — fix: validate and optimize WhatsApp phone matching

## Migration aplicada
- `supabase/migration_lead_outreach.sql` — aplicada no SQL Editor do Supabase
- Tabelas: `lead_outreach`, `lead_interactions`
- RPCs: `get_outreach_state` (anon), `confirm_outreach_from_whatsapp` (service_role)
- Grants aplicados: SELECT em lead_outreach e lead_interactions para anon

## 4 leads já confirmados (apply completo)
1. TECM TECNOLOGIA Conserto de Impressora — `f524cffb...` — 5521****9770
2. Suporte Smart Nova Iguaçu — `33f46d38...` — 5521****3011
3. You Cell Conserto de Celulares — `728f4420...` — 5521****6901
4. Smart Tech — `bf414a15...` — 5521****8611

Todos com:
- `lead_outreach.status = confirmed_from_whatsapp`
- `lead_interactions = 1` (sem duplicação)
- Idempotência confirmada (`already_confirmed` no 2º apply)

## Próxima etapa
Sincronização retroativa de 20 leads em **dry-run** antes de qualquer novo `--apply`.

```bash
python sincronizar_abordados_whatsapp.py --dry-run --limit 20
```

Só aplicar `--apply` nos leads que o dry-run confirmar como `matched` ou `confirmed`.

## Credenciais
- `.env` tem: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- Service role necessária apenas para `--apply` (confirm_outreach_from_whatsapp)
- Anon suficiente para dry-run e get_outreach_state

## Perfil WhatsApp
- `profiles/whatsapp_match` — perfil separado para o matcher (NÃO usar .whatsapp_business_profile)
- Campo de busca corrigido: `input[placeholder*="Pesquisar" i]` adicionado aos seletores

## Scripts auxiliares (não commitar)
- `_apply_3_leads.py` — script de validação dos 3 leads
- `_descobrir_controle_positivo.py` — descoberta automática de controle positivo
- `_diagnose_search_box.py` — diagnóstico do campo de busca

## Branches
- `master` — versão antiga (campanha assistencias)
- `feat/captador-geografico-avgestao-v1` — versão nova com territórios, runs, 346 testes
- `feat/protecao-duplicidade-whatsapp` — branch atual com matcher e outreach

## Worktree
`C:\projetos\script-mapear-comercios-whatsapp-dedup`