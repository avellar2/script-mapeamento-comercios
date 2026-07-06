---
name: hermes-gateway-setup
label: Hermes Gateway Setup
description: Configure messaging platforms (Discord, Telegram, WhatsApp, etc.) as gateways for Hermes Agent. Covers env vars, bot token setup, platform-specific requirements, and troubleshooting.
author: Vanderson
version: "1.0"
triggers:
  - "setup discord"
  - "configure telegram"
  - "gateway not connecting"
  - "messaging platform setup"
  - "connect bot to channel"
  - "discord timeout"
---

# Hermes Gateway Setup

Guia completo para configurar plataformas de mensagem como gateway do Hermes Agent.

## Visão Geral

O Hermes Gateway permite conversar com o Hermes via Discord, Telegram, WhatsApp, etc. Cada plataforma tem requisitos específicos.

---

## Discord — Setup Completo

### 1. Criar o Bot no Discord Developer Portal

1. Acessar: https://discord.com/developers/applications
2. Clicar em **New Application** → nomear (ex: `Hermes Prospecção`)
3. Ir em **Bot** no menu lateral
4. Clicar **Add Bot** → **Reset Token** → **copiar o token** (é o `DISCORD_BOT_TOKEN`)
5. **⚠️ IMPORTANTE — Habilitar Privileged Gateway Intents** (senão o bot conecta mas desconecta após 30s):
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent** ← **ESSENCIAL — sem ele o bot não lê mensagens**
6. Clicar **Save Changes**

### 2. Adicionar o Bot ao Servidor

Gerar link de convite:
```
https://discord.com/oauth2/authorize?client_id=<BOT_CLIENT_ID>&permissions=8&integration_type=0&scope=bot
```

Substituir `<BOT_CLIENT_ID>` pelo ID do bot (encontrado em General Information do app).

**⚠️ Pitfall:** Sem `integration_type=0` na URL, o convite pode retornar `{"scope": ["0"]}` em JSON ao invés da página de autorização. Sempre incluir `integration_type=0`.

### 3. Variáveis de Ambiente

No arquivo `~/.hermes/.env`:

```bash
# Discord Gateway
DISCORD_BOT_TOKEN=seu_token_aqui
DISCORD_ALLOW_ALL_USERS=true
GATEWAY_ALLOW_ALL_USERS=true
```

**⚠️ ATENÇÃO:** O nome da variável é `DISCORD_BOT_TOKEN`, NÃO `DISCORD_TOKEN`. Muitas tentativas de setup falham por causa desse erro.

### Configurar modelo

**⚠️ IMPORTANTE — Case sensitivity:** Modelo DEVE ser minúsculo no ollama-cloud.

```bash
# CORRETO (minúsculo)
hermes config set model.default minimax-m2.7

# ERRADO — causa HTTP 404 e retrying infinito
hermes config set model.default MiniMax-M2.7
```

Provider:
```bash
hermes config set model.provider ollama-cloud
```

### 5. Iniciar o Gateway

```bash
hermes gateway run --replace
```

### 6. Verificar Logs

```bash
tail -20 ~/.hermes/logs/gateway.log
```

Sinais de sucesso:
```
[Discord] Connected as botXXXXXXXX#XXXX
✓ discord connected
Gateway running with 1 platform(s)
```

Sinais de problema:
```
discord connect timed out after 30s
"Reconnect discord error: discord connect timed out after 30s"
```

---

## Troubleshooting Discord

### "discord connect timed out after 30s" + desconecta

**Causa mais comum:** Message Content Intent não está habilitado.

**Solução:** Ir em https://discord.com/developers/applications → Bot → Privileged Gateway Intents → ligar **Message Content Intent** → Save Changes → reiniciar gateway.

### Token inválido (401 Unauthorized)

- Verificar se o token copiado é de **Bot** (não de User)
- Token de bot começa com números e tem formato: `MTUxMj...G7hR3j.abc...`
- User tokens são mais longos e não servem pra bots

### "No messaging platforms enabled"

- Verificar se `DISCORD_BOT_TOKEN` está no `.env` (não `DISCORD_TOKEN`)
- Verificar se o gateway está lendo o `.env` correto
- Rodar `hermes gateway run --replace` após mudar variáveis

### Bot responde "estou usando modelo X" errado

**Sintoma:** O bot diz que está usando um modelo diferente do configurado (ex: "glm-5.1" em vez de "minimax-m2.7").

**Causa:** Sessão antiga do Discord com histórico de mensagens referenciando o modelo antigo.

**Solução:** Mandar `/new` no Discord para iniciar nova conversa. O modelo correto será usado na nova sessão.

### Sessão antiga persistindo modelo/tópicos

**Sintoma:** O gateway reiniciou com modelo novo, mas o bot continua com comportamento da sessão antiga.

**Solução:** Mandar `/new` no Discord para resetar a sessão. O gateway preserva sessões entre restarts — é necessário iniciar uma nova conversa para usar configurações atualizadas.

### Rate limiting (429)

Normal em msgs muito longas ou muitas mensagens seguidas. O gateway trata automaticamente com retry.

### Provider error "Connection error" ou "404 model not found" com minimax

O provider `minimax` nativo (base_url `api.minimax.io`) não funciona com o gateway. Usar `ollama-cloud`:

```bash
hermes config set model.provider ollama-cloud
```

**⚠️ CRITICAL — Case sensitivity:** O nome do modelo DEVE ser minúsculo. Usar `minimax-m2.7` (NÃO `MiniMax-M2.7`). O ollama-cloud retorna HTTP 404 para nomes com maiúsculas, causando retry loops infinitos no Discord.

```bash
# CORRETO
hermes config set model.default minimax-m2.7

# ERRADO — causa 404 e retrying infinito
hermes config set model.default MiniMax-M2.7
```

**Sintomas do bug:** Bot conecta ao Discord normalmente (`✓ discord connected`) mas fica em "retrying" ao tentar responder mensagens. Logs mostram `model "MiniMax-M2.7" not found` (HTTP 404).

---

## Telegram (alternativa)

Se Discord não funcionar, Telegram é boa alternativa:

1. Criar bot via @BotFather no Telegram
2. Pegar o token
3. No `.env`: `TELEGRAM_BOT_TOKEN=seu_token`
4. `hermes gateway run`

**⚠️ Problema conhecido:** Contas novas do Telegram podem receber "You cannot create new bots at this time" — tentar de outro dispositivo/conta ou aguardar 24-48h.

---

## Configurações Comuns de Platform

### Allowlist (produção)

```bash
GATEWAY_ALLOW_ALL_USERS=true  # DEV — permite qualquer usuário
# ou
DISCORD_ALLOWED_USERS=id1,id2  # PROD — só usuários específicos
TELEGRAM_ALLOWED_USERS=id1,id2
```

### Home Channel (para cron jobs e notificações)

```bash
DISCORD_HOME_CHANNEL=canal_id
```

---

## Padrão de Variáveis de Ambiente por Plataforma

| Plataforma | Variável de Token | Outras variáveis |
|------------|------------------|-----------------|
| Discord | `DISCORD_BOT_TOKEN` | `DISCORD_ALLOWED_USERS`, `DISCORD_HOME_CHANNEL` |
| Telegram | `TELEGRAM_BOT_TOKEN` | `TELEGRAM_ALLOWED_USERS` |
| WhatsApp | `WHATSAPP_SESSION_DIR` | — |
| Slack | `SLACK_BOT_TOKEN` | `SLACK_TEAM_ID` |

**Regra:** Nunca usar `DISCORD_TOKEN` — sempre `DISCORD_BOT_TOKEN`. O mesmo vale pra outras plataformas — verificar o `plugin.yaml` de cada uma para confirmar o nome exato da variável.

---

## Referências

- Documentação oficial: https://hermes-agent.nousresearch.com/docs
- Discord Developer Portal: https://discord.com/developers/applications
- Gateway commands: `hermes gateway run`, `hermes gateway stop`, `hermes gateway restart`