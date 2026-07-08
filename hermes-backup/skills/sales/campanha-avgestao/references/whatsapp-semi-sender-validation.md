# WhatsApp Semi Sender — Fluxo com Confirmação por Token

## Resumo da Validação (julho 2026)

O modo `semi` com `--semi-confirm-token` foi validado em 7 runs (hermes001–hermes007) na branch `feat/protecao-duplicidade-whatsapp`. A run hermes007 conseguiu o **primeiro envio real com sucesso**.

## O que funcionou (validado end-to-end em hermes007)

- Token `CONFIRMAR-3966-hermes007` aceito corretamente
- `manual_confirmed` registrado com origem por token (`manual_confirm_source=token`)
- `post_manual_confirmed` registrado
- `wa_me_opening` → abriu `web.whatsapp.com/send` direto (sem wa.me)
- Campo de mensagem encontrado em 10s
- Chat aberto via URL direta
- Checagem de identidade e mensagem existente
- Botão Enviar localizado e clicado
- **Mensagem enviada com sucesso (clique confirmado)**
- `settle_outreach` confirmado
- Reserva atômica via `reserve_outreach` RPC
- Nenhum envio sem confirmação
- Zero edição de código

## Runs de validação

### hermes001 (HEAD fb687e0)
- Token aceito ✅
- Falhou em `wa_me_loaded` — wa.me mostra tela intermediária ("Continuar para o WhatsApp Web")
- `settle_outreach` liberou reserva, 0 pendências

### hermes002 (HEAD 71e45d5)
- Tela intermediária do wa.me **corrigida** ✅ — detectou e clicou em "Continuar para o WhatsApp Web"
- Falhou com timeout 45s após o clique — perfil `.whatsapp_business_profile` estava deslogado (QR Code)
- `settle_outreach` liberou reserva, 0 pendências

### hermes003 (HEAD 71e45d5, após re-login do sender)
- Matcher (`profiles/whatsapp_match`) também estava deslogado — "Campo de busca não encontrado"
- Classificação: `verification_error`
- Não chegou ao envio — falhou na verificação de duplicidade
- `settle_outreach` liberou reserva, 0 pendências

### hermes004 (HEAD 71e45d5, após re-login do matcher)
- Matcher funcionou: `safe_to_send` ✅
- Token aceito ✅
- Tela intermediária detectada e clicou em "Continuar" ✅
- Timeout de 45s estourou — wa.me demorou 27s só pra carregar a tela intermediária
- Sobraram apenas ~11s antes do timeout total
- `settle_outreach` liberou reserva, 0 pendências

### hermes005 (HEAD 6e40448 — timeout estendido para 120s)
- Matcher funcionou: `safe_to_send` ✅
- Token aceito ✅
- Tela intermediária detectada e clicou ✅
- Timeout **não estourou mais** (120s) ✅
- Mas após clicar em "Continuar", o wa.me redirecionou para `api.whatsapp.com/send/` e o campo de mensagem não apareceu em 40s
- **Causa:** o wa.me → "Continuar para WhatsApp Web" não completa o redirecionamento para `web.whatsapp.com` com o chat aberto
- `settle_outreach` liberou reserva, 0 pendências

### hermes006 (HEAD e37a4c0 — URL direta web.whatsapp.com/send)
- Matcher funcionou: `safe_to_send` ✅
- Token aceito ✅
- **Abriu `web.whatsapp.com/send?phone=...` direto** ✅ (sem wa.me, sem tela intermediária)
- URL: `https://web.whatsapp.com/send?phone=5521964103966&text=...`
- **Falso positivo de "número inválido"** — o texto `"número"` é muito genérico e aparece em qualquer página do WhatsApp em português
- `settle_outreach` liberou reserva, 0 pendências

### hermes007 (HEAD 5dd93cb — falso positivo corrigido) ✅ ENVIADO COM SUCESSO
- Matcher funcionou: `safe_to_send` ✅
- Token aceito ✅
- **Abriu `web.whatsapp.com/send` direto** ✅
- **Campo de mensagem encontrado em 10s** ✅
- **Chat aberto via URL direta** ✅
- **Botão Enviar localizado e clicado** ✅
- **Mensagem enviada com sucesso (clique confirmado)** ✅
- **`settle_outreach` confirmado** ✅
- Resumo: `enviados: 1, falhas: 0, pulados: 0, total_processado: 1`
- Tempo total: ~40s

## Commits da correção (ordem cronológica)

| Commit | Descrição | Run validada |
|--------|-----------|--------------|
| `0686656` | fix: prevent semi sender hang after manual confirmation | (pré-hermes001) |
| `fb687e0` | feat: allow token-based semi confirmation for agents | hermes001 |
| `71e45d5` | fix: handle wa.me intermediate web continue screen | hermes002 |
| `6e40448` | fix: extend wa.me redirect timeout after continue | hermes005 |
| `e37a4c0` | fix: open whatsapp web send url directly | hermes006 |
| `5dd93cb` | fix: avoid false invalid phone detection on whatsapp page | hermes007 ✅ |

## ⚠️ PITFALL CRÍTICO: Ambos os perfis precisam estar logados

O fluxo `semi` usa **dois perfis** do Playwright, e **ambos precisam ter sessão ativa**:

| Perfil | Uso | Lock |
|--------|-----|------|
| `profiles/whatsapp_match` | Verificação de duplicidade (matcher) | `output/avgestao/whatsapp_match.lock` |
| `.whatsapp_business_profile` | Envio (sender) | `output/avgestao/whatsapp_sender_global.lock` |

Se **qualquer um** dos dois estiver deslogado (QR Code), o fluxo falha:
- Matcher deslogado → `verification_error` (campo de busca não encontrado)
- Sender deslogado → `wa_me_falha` (timeout após wa.me redirecionar para QR Code)

### Diagnóstico rápido de sessão (sem envio)
```python
from playwright.sync_api import sync_playwright
import json, time

PROFILE = '.whatsapp_business_profile'  # ou 'profiles/whatsapp_match'

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE, headless=False, args=['--no-sandbox'],
        viewport={'width': 1280, 'height': 800},
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=60000)
    time.sleep(15)
    qr = page.query_selector('canvas, div:has-text("escaneie")')
    chat_list = page.query_selector('div[data-testid="chat-list"]')
    print(json.dumps({'qr_found': qr is not None, 'chat_list_found': chat_list is not None}))
    browser.close()
```

### Procedimento de re-login do sender
1. Rodar `python abrir_whatsapp.py` em background (usa `.whatsapp_business_profile`, confirma linha 11)
2. Escanear QR Code com WhatsApp Business no celular
3. Aguardar lista de conversas aparecer
4. Matar o processo (não tem Ctrl+C não-interativo; usar `process kill` ou taskkill)
5. Perfil preservado com cookies/sessão

### Procedimento de re-login do matcher
O perfil `profiles/whatsapp_match` também pode expirar. Não há script dedicado como `abrir_whatsapp.py` para o matcher. Para logar, abrir manualmente com Playwright `launch_persistent_context(user_data_dir='profiles/whatsapp_match')`, navegar para `web.whatsapp.com`, escanear QR, fechar.

### ⚠️ Não pode abrir dois navegadores com o mesmo perfil
Tentar lançar um segundo `launch_persistent_context` com o mesmo `user_data_dir` enquanto um já está aberto causa `TargetClosedError`. Sempre fechar o primeiro antes de diagnosticar.

## ⚠️ PITFALL: wa.me é frágil — usar web.whatsapp.com/send direto

O caminho via `wa.me/<phone>?text=...` tem múltiplas falhas:
1. **Tela intermediária** — mostra "Continuar para o WhatsApp Web" que precisa ser clicado
2. **Redirecionamento incompleto** — após clicar em "Continuar", pode cair em `api.whatsapp.com/send/` sem abrir o chat
3. **Timeout insuficiente** — o wa.me demora 27s só pra carregar a tela intermediária
4. **Sessão expirada** — se o perfil sender estiver deslogado, redireciona para QR Code

**Solução definitiva (commit `e37a4c0`):** usar URL direta do WhatsApp Web:
```
https://web.whatsapp.com/send?phone=<telefone>&text=<mensagem_url_encoded>&type=phone_number&app_absent=0
```

Isso elimina a tela intermediária, o redirecionamento e a dependência do wa.me.

## ⚠️ PITFALL: Falso positivo de "número inválido"

A lista `_WA_ME_INVALID_PHONE_TEXTS` continha `"número"` como termo de detecção. Essa palavra aparece em qualquer página do WhatsApp em português (ex: "número de telefone", "Conversar com +55 21 3966-3966"), causando falso positivo.

**Solução (commit `5dd93cb`):** usar termos específicos como `"número inválido"`, `"número de telefone inválido"`, `"invalid phone number"` em vez de `"número"` isolado.

## Locks stale

- `whatsapp_match.lock` e `whatsapp_sender_global.lock` podem ficar stale após processos mortos
- Verificar se há processo ativo (python/chrome/chromium) antes de remover
- Remover apenas os 2 arquivos de lock, nunca profiles/cookies/diretórios
- No Windows, `ps -W | grep -i "campanha\\|whatsapp\\|chrome\\|chromium"` para verificar processos

## SUPABASE_SERVICE_ROLE_KEY

- Necessária para `recover-reserved`
- Deve ser adicionada manualmente no `.env` local
- Hermes não adiciona, não inventa, não pede no chat
- Variáveis existentes no `.env`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ZOHO_SMTP_*`

## Comandos de Validação

```bash
# Ambiente
git rev-parse HEAD
git branch --show-current
git merge-base --is-ancestor 0686656 HEAD && echo CORRECAO_INPUT_ESTA_NO_HEAD
git merge-base --is-ancestor fb687e0 HEAD && echo TOKEN_CONFIRM_ESTA_NO_HEAD
git merge-base --is-ancestor 71e45d5 HEAD && echo WA_ME_INTERMEDIARIA_ESTA_NO_HEAD
git merge-base --is-ancestor 6e40448 HEAD && echo WA_ME_TIMEOUT_ESTA_NO_HEAD
git merge-base --is-ancestor e37a4c0 HEAD && echo WEB_WHATSAPP_DIRECT_ESTA_NO_HEAD

# Reservas
python campanha_whatsapp.py recover-reserved --campaign-key avgestao:assistencias:primeiro_contato:v1 --dry-run

# Locks
ls -la output/avgestao/whatsapp_match.lock output/avgestao/whatsapp_sender_global.lock

# Plan
python campanha_whatsapp.py plan --limit 1 --nicho assistencias --until 23:59 --run-id run_20260707_hermesNNN --message-template templates/avgestao_assistencias_primeiro_contato.txt

# Semi com token
python campanha_whatsapp.py semi --limit 1 --nicho assistencias --until 23:59 --interval-minutes 5 --verification-budget-seconds 15 --run-id run_20260707_hermesNNN --semi-confirm-token "CONFIRMAR-XXXX-hermesNNN" --message-template templates/avgestao_assistencias_primeiro_contato.txt
```

## Stages do fluxo semi (após confirmação por token)

```
lead_selected → reserved → safe_to_send → prompt_manual → manual_confirmed → post_manual_confirmed → wa_me_opening → [web.whatsapp.com/send direto] → wa_me_loaded → chat_identity_checking → chat_identity_checked → existing_message_checking → existing_message_checked → message_box_searching → message_box_ready → message_filling → message_filled → send_button_searching → send_button_ready → send_clicking → send_clicked → outbound_confirming → settle_sent_done
```

## Checklist pré-teste (obrigatório)

1. HEAD confere
2. Commits ancestrais confirmados
3. 0 reservas pendentes
4. Locks limpos (ou stale removidos)
5. **Perfil matcher logado** (sem QR Code)
6. **Perfil sender logado** (sem QR Code)
7. Plan encontra 1 lead
8. Token montado com últimos 4 do telefone
9. Semi executado com mesmo run_id do plan
10. Pós-teste: 0 reservas, locks limpos