#!/usr/bin/env python3
"""Envia leads de assistencias do Supabase - ate 17:30"""
import os, json, time, ssl, urllib.request, random, sys
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timedelta

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.lock_whatsapp_sender import LockWhatsAppSender
from sender_int import (
    normalizar_telefone_lead,
    obter_campaign_key,
    reserve_lead,
    settle_lead,
)

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
API_URL = f"{SUPABASE_URL}/rest/v1/leads"
CTX = ssl.create_default_context()
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

# Buscar leads do Supabase
all_leads = []
offset = 0
while True:
    req = urllib.request.Request(
        f"{API_URL}?produto=eq.avgestao&grupo=eq.assistencias&status=in.(novo,pronto_para_enviar)"
        f"&select=id,nome,telefone,telefone_normalizado,cidade,subnicho,produto,grupo"
        f"&limit=1000&offset={offset}",
        headers=HEADERS
    )
    with urllib.request.urlopen(req, context=CTX) as r:
        data = json.loads(r.read().decode())
        if not data: break
        all_leads.extend(data)
        if len(data) < 1000: break
        offset += 1000

# Filtrar celular usando normalização unificada
cels = []
for l in all_leads:
    tel_norm = normalizar_telefone_lead(l)
    if tel_norm and tel_norm.startswith("5521") and len(tel_norm) == 13:
        cels.append(l)

random.shuffle(cels)

# Calcular quantos cabem ate 17:30
agora = datetime.now()
limite = datetime.now().replace(hour=17, minute=30, second=0)
minutos_restantes = (limite - agora).total_seconds() / 60
cabem = int(minutos_restantes // 7)
qtd = min(cabem, len(cels), 30)
leads = cels[:qtd]

print(f"Total disponiveis: {len(cels)}")
print(f"Cabem ate 17:30: {qtd}")
print()

MSG = (
    "Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
    "Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.\n\n"
    "Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação "
    "e o cliente acompanha o reparo pelo próprio link.\n\n"
    "Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\n"
    "Posso liberar e configurar o acesso de vocês?"
)

profile = Path(__file__).parent / ".whatsapp_business_profile"

from playwright.sync_api import sync_playwright

print("=" * 60)
print(f"  Enviando {len(leads)} leads - Assistencias")
print(f"  {agora.strftime('%H:%M')} ate {limite.strftime('%H:%M')}")
print("=" * 60)

# Adquire lock global do perfil dos senders
with LockWhatsAppSender() as lock:
    if not lock.acquired:
        print("ERRO: Já existe um sender ativo usando o perfil WhatsApp.")
        sys.exit(1)

    for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = profile / lock_file
        if p.exists(): p.unlink()

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile), channel="chrome",
            headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--new-instance"],
            viewport={"width": 800, "height": 900}, locale="pt-BR",
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        enviados = 0
        for i, lead in enumerate(leads):
            nome = lead["nome"]
            tel_norm = normalizar_telefone_lead(lead)
            if not tel_norm:
                print(f"\n[{i+1}/{len(leads)}] {nome} - Telefone inválido")
                continue

            campaign_key = obter_campaign_key(lead)
            msg = MSG.format(nome=nome)
            url = f"https://web.whatsapp.com/send?phone={tel_norm}&text={quote(msg)}"

            print(f"\n[{i+1}/{len(leads)}] {nome}")
            print(f"   📞 {tel_norm}")

            # Reserva atômica antes de abrir o WhatsApp
            reserve = reserve_lead(tel_norm, campaign_key, lead["id"], "sender:auto")
            if not reserve or reserve.get("outcome") not in ("reserved",):
                print(f"   ⚠️ Reserva recusada: {reserve.get('outcome', 'erro')}")
                continue

            reservation_id = reserve.get("reservation_id")
            reservation_token = reserve.get("reservation_token")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
            except:
                print("   ❌ Erro navegacao")
                settle_lead(reservation_id, reservation_token, "failed", obs="erro_navegacao")
                continue

            time.sleep(8)
            bt = page.inner_text("body", timeout=5000).lower()[:200]
            if "escaneie" in bt or "conectar" in bt:
                print("   ⚠️ QR Code! Escaneie...")
                for _ in range(36):
                    time.sleep(5)
                    bt = page.inner_text("body", timeout=5000).lower()[:200]
                    if "escaneie" not in bt and "conectar" not in bt:
                        print("   ✅ Conectado!")
                        break
                else:
                    print("   ❌ QR nao escaneado")
                    settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="qr_nao_escaneado")
                    continue

            if "inválido" in bt or "invalid" in bt:
                print("   ⚠️ Numero invalido")
                settle_lead(reservation_id, reservation_token, "failed", obs="numero_invalido")
                continue

            try:
                page.wait_for_selector('div[contenteditable="true"]', timeout=35000)
            except:
                print("   ⚠️ Campo nao apareceu")
                settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="campo_nao_apareceu")
                continue

            time.sleep(2)
            btn = page.locator('button[aria-label="Enviar"], button[aria-label="Send"]')
            if btn.count() > 0:
                btn.first.click()
                print("   ✅ Enviado!")
            else:
                ed = page.locator('div[contenteditable="true"]')
                if ed.count() > 0:
                    ed.first.click()
                    time.sleep(1)
                    page.keyboard.press("Enter")
                    print("   ✅ Enviado via Enter!")
                else:
                    print("   ❌ Botao nao encontrado")
                    settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="botao_nao_encontrado")
                    continue

            time.sleep(4)
            # Finaliza via settle (NÃO faz PATCH separado)
            settle = settle_lead(
                reservation_id, reservation_token, "sent",
                message_timestamp=datetime.now().isoformat(),
                obs="enviado_assistencias_hoje",
            )
            if settle and settle.get("outcome") == "settled":
                enviados += 1
                print("   ✅ Confirmado no Supabase")
            else:
                print(f"   ⚠️ Falha ao finalizar: {settle}")

            if i < len(leads) - 1:
                print("   ⏳ 7min...")
                for s in range(420, 0, -1):
                    if s % 60 == 0 or s <= 10:
                        print(f"   {s//60}min {s%60:02d}s", end="\r")
                    time.sleep(1)
                print()

        browser.close()

print(f"\n✅ Enviados: {enviados}/{len(leads)}")
