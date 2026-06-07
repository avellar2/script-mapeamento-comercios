# Gateway Setup — Acesso Remoto ao Hermes

## Por que usar gateway

O usuário pode estar no trabalho e querer dar comandos ao Hermes sem estar no PC de casa.
O gateway permite conversar com o Hermes de qualquer lugar (Telegram, Discord, WhatsApp)
enquanto ele continua rodando no PC com todos os scripts, WhatsApp Business e dados.

## Telegram Gateway

### Criar bot
1. Abrir Telegram, procurar @BotFather
2. Enviar `/newbot`
3. Escolher nome (ex: "Hermes Prospecção")
4. Escolher username (termina com `bot`)
5. @BotFather retorna um token

### Pitfall: Telegram bloqueia criação de bots
Erro: "You cannot create new bots at this time. For more information on why this happened and what your appeal options are, please contact @Spambot."

Causa: conta do Telegram pode ser relativamente nova ou ter feito muitas ações seguidas.

Solução: esperar 24-48h e tentar novamente, ou usar Discord como fallback.

### Configurar gateway
```bash
hermes gateway setup
# Seguir wizard, escolher Telegram, colar token
hermes gateway run
```

## Discord Gateway (RECOMENDADO — já configurado)

### Setup Atual
- **Bot:** bot1512676735886426262
- **Server:** Hermes (ID: 1512676518856364122)
- **Canal:** #geral
- **Modelo:** minimax-m2.7 via ollama-cloud
- **Variável env:** DISCORD_BOT_TOKEN em ~/.hermes/.env

### Criar bot do zero (referência futura)
1. Acessar https://discord.com/developers/applications
2. New Application → nome (ex: "Hermes Prospecção")
3. Bot → Add Bot → Reset Token → copiar token
4. ⚠️ **OBRIGATÓRIO** — Habilitar Privileged Gateway Intents:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ **Message Content Intent** (sem isso, o bot conecta mas desconecta após 30s)
5. Gerar link de convite (com `integration_type=0`):
   ```
   https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=8&integration_type=0&scope=bot
   ```
6. Abrir link, escolher servidor, autorizar

### Configurar Hermes
```bash
# .env — variável é DISCORD_BOT_TOKEN (não DISCORD_TOKEN!)
DISCORD_BOT_TOKEN=MTUxMj...
DISCORD_ALLOW_ALL_USERS=true
GATEWAY_ALLOW_ALL_USERS=true

# Configurar modelo (SEMPRE minúsculo no ollama-cloud!)
hermes config set model.default minimax-m2.7
hermes config set model.provider ollama-cloud

# Iniciar gateway
hermes gateway run --replace
```

### Verificar conexão
```bash
# Verificar se conectou
tail -20 ~/.hermes/logs/gateway.log
# Procurar: [Discord] Connected as botXXXXXXXX#XXXX

# Verificar logs do agente
tail -20 ~/.hermes/logs/agent.log
# Procurar: model=minimax-m2.7 provider=ollama-cloud
```

## Escolha do PC

### Setup com 1 PC (recomendado)
- Instalar Hermes no PC que fica ligado (casa OU trabalho)
- Configurar gateway nele
- Conectar WhatsApp Business nele
- Conversar pelo Telegram/Discord de qualquer lugar

### Setup com 2 PCs
- Hermes no PC de casa + Hermes no PC do trabalho
- Skills e scripts vão por GitHub (clone nos dois)
- Cada PC tem seu próprio perfil WhatsApp Business
- Só pode ligar UM de cada vez (senão o gateway divide as mensagens entre os dois)
- GitHub sincroniza skills, memória e scripts entre os PCs

### Vanderson: PC do trabalho = principal
- Vanderson é o TI → pode deixar ligado 24h
- Scripts vão por GitHub
- WhatsApp Business separado em cada PC (escanear QR Code uma vez em cada)
- Discord é o canal de acesso remoto (Telegram bloqueado por Spambot)

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| Bot conecta mas desconecta após 30s | Message Content Intent não habilitado | Developer Portal → Bot → Privileged Gateway Intents → ligar todas as 3 |
| Token 401 Unauthorized | Token de usuário (não de bot) ou token errado | Usar token do Bot (Developer Portal → Bot → Reset Token) |
| "No messaging platforms enabled" | Variável errada no .env | Usar `DISCORD_BOT_TOKEN` (não `DISCORD_TOKEN`) |
| HTTP 404 "model not found" | Nome do modelo com maiúsculas | `hermes config set model.default minimax-m2.7` (minúsculo!) |
| Connection error com provider minimax | Provider nativo não funciona | `hermes config set model.provider ollama-cloud` |
| Bot responde modelo errado | Sessão antiga com histórico | Mandar `/new` no Discord |
| Bot invite retorna JSON `{"scope":["0"]}` | Faltando `integration_type=0` na URL | Adicionar `&integration_type=0` na URL de convite |
| Rate limiting 429 | Muitas mensagens seguidas | Gateway trata automaticamente com retry |

## Comandos Úteis

```bash
# Iniciar gateway
hermes gateway run --replace

# Parar gateway
hermes gateway stop

# Reiniciar gateway
hermes gateway stop && hermes gateway run --replace

# Verificar logs
tail -20 ~/.hermes/logs/gateway.log
tail -20 ~/.hermes/logs/agent.log

# Verificar modelo atual
cat ~/.hermes/config.yaml | grep -A3 "model:"

# Mudar modelo
hermes config set model.default minimax-m2.7
hermes config set model.provider ollama-cloud
```