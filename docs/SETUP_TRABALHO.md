# Setup no PC do Trabalho — Amanhã 🚀

## 1. Instalar Hermes

```bash
# Abrir PowerShell como Administrador
winget install NousResearch.Hermes
# ou
curl -fsSL https://hermes-agent.nousresearch.com/install.ps1 | powershell
```

---

## 2. Clonar o repositório

```bash
cd C:\projetos\
git clone https://github.com/avellar2/script-mapeamento-comercios.git
cd script-mapeamento-comercios
```

---

## 3. Copiar skills do Hermes

```bash
# Copia as skills do repositório pro Hermes
xcopy /E /I hermes-config\skills\* %USERPROFILE%\AppData\Local\hermes\skills\
```

---

## 4. Criar arquivo .env

Criar `C:\projetos\script-mapeamento-comercios\.env` com:

```
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=xxxxxxxxxxxx
DISCORD_BOT_TOKEN=xxxxxxxxxxxx
```

> ⚠️ Pegar as chaves no PC de casa ou onde salvou. Não subir pro GitHub.

---

## 5. Configurar modelo do Hermes

```bash
hermes config set model.default minimax-m2.7
hermes config set model.provider ollama-cloud
```

---

## 6. Escanear WhatsApp Business

```bash
cd C:\projetos\script-mapeamento-comercios
python enviar_teste_whatsapp_business.py
```

> Vai abrir um Chrome com QR Code do WhatsApp. Escanear com o **WhatsApp Business** (o de prospecção).

---

## 7. Subir gateway Discord

```bash
hermes gateway run --replace
```

Testar no Discord:

```
@bot1512676735886426262 oi, to no trabalho
```

---

## 8. Verificar leads no Supabase

```bash
python -c "from supabase import create_client; import os; from pathlib import Path; [exec('os.environ[k.strip()]=v.strip().strip(chr(39))') for line in Path('.env').read_text().splitlines() if '=' in line and not line.startswith('#') for k,v in [line.split('=',1)]]; supa=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_ANON_KEY']); resp=supa.table('leads').select('*',count='exact').execute(); print(f'Total leads: {len(resp.data)}')"
```
> Deve mostrar ~8.194 leads.

---

## 9. Começar a prospectar! 🎯

Pelo terminal ou Discord:

```
@bot1512676735886426262 prepara campanha pra hoje
```

---

## Memória dos ponteiros

Quando o Hermes perguntar "qual sua memória?", responder os ponteiros abaixo no comando `/memory add`:

1. Discord: bot1512676735886426262, server 1512676518856364122, @menção, minimax-m2.7 minúsculo
2. Supabase ~8.194 leads (Baixada + Rio Premium)
3. Baixada R$149, Rio Premium R$247-297. Chrome visível
4. Skill: llm-model-selection — qual modelo usar
5. Cliente só paga depois da página no ar

---

## Como usar esse MD com o Hermes

Quando estiver no trabalho, mande esta mensagem no Discord:

```
@bot1512676735886426262 Leia o arquivo C:\projetos\script-mapeamento-comercios\docs\SETUP_TRABALHO.md e me guie passo a passo
```

O Hermes vai ler o MD e te orientar em cada etapa. ✅

---

## Comandos úteis

| Pra quê | Comando |
|---------|---------|
| Mapear Baixada | `python mapear_comercios.py --regiao baixada` |
| Mapear Rio Premium | `python mapear_comercios.py --regiao rio_premium` |
| Importar pro Supabase | `python importar_rio_premium.py` (ou import_leads_to_supabase.py) |
| Campanha | `python campanha_diaria.py --regiao baixada --top 15` |
| Enviar WhatsApp | `python enviar_teste_whatsapp_business.py` |
| Gateway Discord | `hermes gateway run --replace` |
| Ver progresso | Ler `output/rio_premium/playwright/progresso.json` |