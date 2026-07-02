#!/usr/bin/env python3
"""Envia mensagens para os 5 leads aprovados da campanha assistencias"""
import os, json, time, ssl, urllib.request, sys
from pathlib import Path
from urllib.parse import quote
from datetime import datetime

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.lock_whatsapp_sender import LockWhatsAppSender
from sender_int import (
    normalizar_telefone_lead,
    obter_campaign_key,
    reserve_lead,
    settle_lead,
    get_supabase_client,
)
from utils.phone_utils import normalizar_telefone_br

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

# Leads com telefone (NÃO usar nome para matching)
LEADS = [
    {"nome": "Nick Cell - Assistência Técnica", "telefone": "5521990170874"},
    {"nome": "WR Smart (Conserto de Celular)", "telefone": "5521985755184"},
    {"nome": "Assistência técnica Freitas Cell", "telefone": "5521981780019"},
    {"nome": "MSC ASSISTÊNCIA TÉCNICA", "telefone": "5521981209833"},
    {"nome": "SWATCELL CONSERTOS DE CELULARES", "telefone": "5521970007855"},
]

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
print(f"  Enviando {len(LEADS)} leads - Assistencias")
print(f"  {datetime.now().strftime('%H:%M')}")
print("=" * 60)

# Adquire lock global do perfil dos senders
with LockWhatsAppSender() as lock:
    if not lock.acquired:
        print("ERRO: Já existe um sender ativo usando o perfil WhatsApp.")
        sys.exit(1)

    # Remove locks do Chromium (após adquirir o lock do sender)
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

        for i, lead_data in enumerate(LEADS, 1):
            nome = lead_data["nome"]
            tel_raw = lead_data["telefone"]
            tel_norm = normalizar_telefone_br(tel_raw)

            if not tel_norm:
                print(f"\n[{i}/{len(LEADS)}] {nome}")
                print(f"   ❌ Telefone inválido: {tel_raw}")
                continue

            # Busca lead_id pelo telefone
            lead_id = None
            try:
                req = urllib.request.Request(
                    f"{API_URL}?telefone_normalizado=eq.{tel_norm}&select=id,nome,produto,grupo",
                    headers=HEADERS
                )
                with urllib.request.urlopen(req, context=CTX) as r:
                    data = json.loads(r.read().decode())
                    if data:
                        lead_id = data[0]["id"]
                        nome = data[0].get("nome", nome)
            except Exception as e:
                print(f"   ⚠️ Erro ao buscar lead: {e}")

            if not lead_id:
                print(f"\n[{i}/{len(LEADS)}] {nome} - Lead não encontrado no Supabase")
                continue

            campaign_key = obter_campaign_key({"produto": "avgestao", "grupo": "assistencias"})
            msg = MSG.format(nome=nome)
            url = f"https://web.whatsapp.com/send?phone={tel_norm}&text={quote(msg)}"

            print(f"\n[{i}/{len(LEADS)}] {nome}")
            print(f"   📞 {tel_norm}")

            # Reserva atômica antes de abrir o WhatsApp
            reserve = reserve_lead(tel_norm, campaign_key, lead_id, source="sender:auto")
            if not reserve or reserve.get("outcome") not in ("reserved",):
                print(f"   ⚠️ Reserva recusada: {reserve.get('outcome', 'erro')}")
                continue

            reservation_id = reserve.get("reservation_id")
            reservation_token = reserve.get("reservation_token")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
            except:
                print("   ❌ Erro ao navegar")
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
                print("   ⚠️ Número inválido")
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
            # Finaliza a reserva como sent (NÃO faz PATCH separado em leads)
            settle = settle_lead(
                reservation_id, reservation_token, "sent",
                message_timestamp=datetime.now().isoformat(),
                obs="enviado_5_assistencias",
            )
            if settle and settle.get("outcome") == "settled":
                print("   ✅ Confirmado no Supabase (via settle_outreach)")
            else:
                print(f"   ⚠️ Falha ao finalizar: {settle}")

            if i < len(LEADS):
                print("   ⏳ 7min...")
                for s in range(420, 0, -1):
                    if s % 60 == 0 or s <= 10:
                        print(f"   {s//60}min {s%60:02d}s", end="\r")
                    time.sleep(1)
                print()

        browser.close()

print(f"\n✅ Envio concluido!")
