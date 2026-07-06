# Discord Bot Setup Atual

## Vanderson's Discord Bot

- **Bot Name:** bot1512676735886426262
- **Bot username:** bot1512676735886426262#5769
- **Server (Guild):** Hermes (ID: 1512676518856364122)
- **Home Channel:** #geral
- **Token:** Armazenado em `~/.hermes/.env` como `DISCORD_BOT_TOKEN`
- **Gateway:** `ollama-cloud` provider (modelo: `minimax-m2.7` — minúsculo obrigatório)

## Status (2025-06-06)

- ✅ Bot conectado e funcionando
- ✅ Message Content Intent habilitado
- ✅ Gateway rodando com Discord
- ✅ 62 skills registradas via slash commands
- ✅ Channel directory: 2 targets
- ✅ Modelo `minimax-m2.7` via `ollama-cloud` confirmado nos logs

## Troubleshooting Aplicado

1. **Timeout de 30s** → Habilitar Message Content Intent no Developer Portal
2. **Provider "minimax" nativo (api.minimax.io) não conecta** → Mudar pra `ollama-cloud`: `hermes config set model.provider ollama-cloud`
3. **Token DISCORD_TOKEN não funcionava** → Variável correta é `DISCORD_BOT_TOKEN` (verificado no plugin.yaml do Discord)
4. **HTTP 404 "model not found"** → Nome do modelo DEVE ser minúsculo: `minimax-m2.7` (não `MiniMax-M2.7`). O ollama-cloud é case-sensitive.
5. **Telegram bloqueado** → @BotFather retorna "You cannot create new bots" em contas novas. Usar Discord como alternativa.
6. **BotInvite URL** → `https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&permissions=8&integration_type=0&scope=bot` (o `integration_type=0` é necessário, sem ele retorna `{"scope": ["0"]}`)
7. **Bot responde modelo errado** → Sessão antiga com histórico. Mandar `/new` no Discord para iniciar conversa limpa com configurações atualizadas.
8. **Gateway killed (exit -15)** → Normal quando outro gateway `--replace` toma o lugar. O novo processo sobe automaticamente.

## Comandos Úteis

```bash
# Iniciar gateway (foreground)
hermes gateway run --replace

# Parar gateway
hermes gateway stop

# Verificar logs
tail -20 ~/.hermes/logs/gateway.log

# Verificar modelo atual
hermes config show | grep model

# Mudar modelo (sempre minúsculo!)
hermes config set model.default minimax-m2.7
hermes config set model.provider ollama-cloud

# Verificar se gateway está rodando
ps aux | grep hermes

# Resetar sessão Discord (se modelo errado)
# Mandar /new no Discord

# Verificar logs do agente (modelo usado por sessão)
tail -20 ~/.hermes/logs/agent.log | grep "model=\|provider="
```

## Configuração do .env

```bash
# Discord Gateway
DISCORD_BOT_TOKEN=<token_aqui>
DISCORD_ALLOW_ALL_USERS=true
GATEWAY_ALLOW_ALL_USERS=true
```