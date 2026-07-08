# campanha_whatsapp.py — Entrypoint Unificado

Branch: `feat/protecao-duplicidade-whatsapp`
Projeto: `C:\projetos\script-mapear-comercios-whatsapp-dedup`

## Subcomandos

### plan
Planeja lote sem abrir browser, sem reservar, sem enviar.
```bash
python campanha_whatsapp.py plan --limit 1 --nicho assistencias --until 23:59 --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

### semi
Envio assistido com confirmação manual (input) ou por token.
```bash
python campanha_whatsapp.py semi --limit 1 --nicho assistencias --until 23:59 --interval-minutes 5 --verification-budget-seconds 15 --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

### semi com token (para agentes)
```bash
python campanha_whatsapp.py semi --limit 1 --nicho assistencias --until 23:59 --run-id run_20260707_hermes001 --semi-confirm-token "CONFIRMAR-3966-hermes001" --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

### verify-only
Verifica duplicidade sem enviar. Usa matcher profile e matcher lock SOMENTE.
```bash
python campanha_whatsapp.py semi --verify-only --limit 5 --nicho assistencias --until 23:59 --verification-budget-seconds 15
```

### recover-reserved
Recupera reservas órfãs.
```bash
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
```

### listar-nichos
```bash
python campanha_whatsapp.py plan --listar-nichos
```

## Token de Confirmação (--semi-confirm-token)

Formato: `CONFIRMAR-<ultimos4>-<runid_curto>`

Exemplo: telefone terminado em `3966`, run_id `run_20260707_hermes001` → token `CONFIRMAR-3966-hermes001`

O token substitui o `input()` interativo. Quando fornecido:
- Pula o prompt manual e registra `manual_confirmed` com origem por token
- Registra `post_manual_confirmed` e avança para `wa_me_opening`
- Se inválido, falha de forma segura (não envia)

## Perfil e Lock

| Recurso | Matcher (verificação) | Sender (envio) |
|---------|----------------------|----------------|
| Perfil | `profiles/whatsapp_match` | `.whatsapp_business_profile` |
| Lock | `output/avgestao/whatsapp_match.lock` | `output/avgestao/whatsapp_sender_global.lock` |

- `verify-only` usa SOMENTE matcher profile e matcher lock
- `semi` usa matcher para verificação, depois sender para envio
- Nunca apagar locks manualmente sem verificar se há processo ativo
- ⚠️ **Ambos os perfis precisam estar logados** — ver `references/whatsapp-semi-sender-validation.md` para diagnóstico e re-login

## Stages do Fluxo Semi (após confirmação por token)

```
lead_selected → reserved → safe_to_send → prompt_manual → manual_confirmed → post_manual_confirmed → wa_me_opening → [tela intermediária wa.me: clicar "Continuar para o WhatsApp Web"] → wa_me_loaded → chat_identity_checking → chat_identity_checked → existing_message_checking → existing_message_checked → message_box_searching → message_box_ready → message_filling → message_filled → send_button_searching → send_button_ready → send_clicking → send_clicked → outbound_confirming → settle_sent_done
```

## Validação Obrigatória Antes de Teste Real

### 1. Confirmar ambiente
```bash
git rev-parse HEAD           # HEAD esperado
git log --oneline -5         # commits recentes
git branch --show-current    # branch correta
```

### 2. Checar reservas pendentes
```bash
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
```
Deve retornar 0 reservas.

### 3. Checar locks
Verificar se `whatsapp_match.lock` e `whatsapp_sender_global.lock` existem.
Se existirem, verificar se há processo ativo (python/chrome/chromium).
Se stale (sem processo ativo), remover apenas os 2 arquivos de lock.
NUNCA apagar profiles, cookies ou diretórios.

### 4. Verificar sessão dos perfis
⚠️ **Etapa crítica frequentemente esquecida.** Ambos os perfis (`profiles/whatsapp_match` e `.whatsapp_business_profile`) precisam estar logados no WhatsApp Web. Se qualquer um estiver deslogado (QR Code), o fluxo falha. Ver procedimento de diagnóstico e re-login em `references/whatsapp-semi-sender-validation.md`.

### 5. Rodar plan
```bash
python campanha_whatsapp.py plan --limit 1 --nicho assistencias --until 23:59 --message-template templates/avgestao_assistencias_primeiro_contato.txt
```
Confirmar: encontrou 1 lead, template carregou, não abriu browser, não reservou.

### 6. Montar token
Usar os últimos 4 dígitos do telefone normalizado + run_id_curto.

### 7. Executar semi com token
Usar o mesmo run_id do plan.

### 8. Pós-teste
```bash
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run
```
Confirmar 0 reservas, locks limpos.

## Defeitos Conhecidos (resolvidos em commits específicos)

### TypeError: verification_budget (resolvido em fb687e0)
- Versões anteriores passavam `verification_budget` como keyword arg para `fazer_match_completo()`, que não aceitava esse parâmetro
- Resolvido: `campanha_whatsapp.py` agora passa `verification_budget_seconds` corretamente

### NoneType page no matcher (resolvido em 7fec2ec)
- O contexto do Playwright (`page`) chegava como `None` no matcher
- Sintoma: `Locator.count: 'NoneType' object has no attribute 'send'`
- Resolvido: inicialização correta do page/context antes do matcher

### wa.me tela intermediária (resolvido em 71e45d5)
- **Causa raiz:** `wa.me/<phone>?text=...` não abre o chat diretamente. Mostra uma landing page com heading "Conversar com +55 21 XXXX-XXXX no WhatsApp" e botões "Abrir app" e "Continuar para o WhatsApp Web".
- O método `abrir_wa_me()` precisa clicar em "Continuar para o WhatsApp Web" ANTES de procurar o campo de mensagem.
- **Resolvido em 71e45d5:** agora detecta a tela intermediária e clica no botão antes de procurar `div[contenteditable="true"]`.
- Número sem WhatsApp mostra "phone number shared via url is invalid" na landing page (diagnóstico diferencial).
- O fluxo falha de forma segura: `settle_outreach` é chamado, reserva liberada, `send_clicked=False`.

### Sessão expirada nos perfis (recorrente)
- Sintoma: QR Code aparece ao abrir `web.whatsapp.com` com o perfil
- Matcher deslogado → `verification_error` (campo de busca não encontrado)
- Sender deslogado → `wa_me_falha` (timeout 45s após wa.me redirecionar para QR Code)
- Solução: re-login via `python abrir_whatsapp.py` (sender) ou Playwright manual (matcher)
- Ver procedimento completo em `references/whatsapp-semi-sender-validation.md`

## Validações Realizadas

### Token-based confirmation (07/07/2026 — HEAD fb687e0)
- `--semi-confirm-token` funciona corretamente
- Token esperado vs recebido: idênticos
- Stages completados: `lead_selected → reserved → safe_to_send → prompt_manual → manual_confirmed (via token) → post_manual_confirmed → wa_me_opening`
- Falhou em `wa_me_loaded` porque wa.me mostra tela intermediária (corrigido em 71e45d5)

### Tela intermediária corrigida (07/07/2026 — HEAD 71e45d5, hermes002)
- Tela intermediária detectada e "Continuar para o WhatsApp Web" clicado ✅
- Falhou com timeout 45s — perfil sender deslogado
- Após re-login do sender (hermes003), matcher também estava deslogado

### Resumo das runs
| Run | HEAD | Token | Até | Falha |
|-----|------|-------|-----|-------|
| hermes001 | fb687e0 | ✅ | wa_me_opening | wa.me tela intermediária |
| hermes002 | 71e45d5 | ✅ | wa_me_opening + clique continuar | sender deslogado (QR Code) |
| hermes003 | 71e45d5 | ✅ | — (falhou no matcher) | matcher deslogado (QR Code) |

- Hermes NÃO pode confirmar manualmente via `input()` — terminal não é interativo. Token é a única forma para agentes.

## Regras Absolutas

- NUNCA executar modo `auto`
- NUNCA usar `--confirm-live-send` sem autorização explícita
- NUNCA apagar profile, cookies ou diretórios
- NUNCA mexer em checkpoint
- NUNCA enviar para mais de 1 lead em teste
- NUNCA repetir automaticamente se falhar
- NUNCA usar service role para leitura
- Hermes NÃO edita código — só diagnosticar e relatar