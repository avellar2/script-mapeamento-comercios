#!/usr/bin/env python3
"""Envia 7 leads de assistencias - ate 17:45"""
import os, json, time, ssl, urllib.request, random
from pathlib import Path
from urllib.parse import quote
from datetime import datetime

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

all_leads = []
offset = 0
while True:
    req = urllib.request.Request(f"{API_URL}?produto=eq.avgestao&grupo=eq.assistencias&status=in.(novo,pronto_para_enviar)&select=id,nome,telefone,telefone_normalizado&limit=1000&offset={offset}", headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX) as r:
        data = json.loads(r.read().decode())
        if not data: break
        all_leads.extend(data)
        if len(data) < 1000: break
        offset += 1000

def is_cel(t):
    if not t: return False
    d = t.replace("55","",1) if t.startswith("55") else t
    d = d.replace(")","").replace("(","").replace(" ","").replace("-","")
    return d.startswith("21") and len(d) >= 11 and d[2] == "9"

cels = [l for l in all_leads if is_cel(l.get("telefone_normalizado") or l.get("telefone") or "")]
random.shuffle(cels)
leads = cels[:7]

MSG = "Boa tarde, pessoal da {nome}! Tudo bem?\n\nAqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.\n\nCom ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.\n\nEu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\nPosso liberar e configurar o acesso de vocês?"

def marcar(lid, status):
    body = json.dumps({"status": status, "ultimo_contato_em": datetime.now().isoformat()}).encode()
    req = urllib.request.Request(f"{API_URL}?id=eq.{lid}", data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req, context=CTX): pass

profile = Path(__file__).parent / ".whatsapp_business_profile"
for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    p = profile / lock
    if p.exists(): p.unlink()

from playwright.sync_api import sync_playwright

print(f"Enviando {len(leads)} leads - ate 17:45")
with sync_playwright() as pw:
    browser = pw.chromium.launch_persistent_context(user_data_dir=str(profile), channel="chrome", headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--new-instance"], viewport={"width": 800, "height": 900}, locale="pt-BR")
    page = browser.pages[0] if browser.pages else browser.new_page()
    for i, lead in enumerate(leads):
        nome = lead["nome"]
        tel = (lead.get("telefone_normalizado") or lead.get("telefone") or "").replace(")","").replace("(","").replace(" ","").replace("-","")
        if not tel.startswith("55"): tel = "55" + tel
        url = f"https://web.whatsapp.com/send?phone={tel}&text={quote(MSG.format(nome=nome))}"
        print(f"\n[{i+1}/7] {nome}")
        try: page.goto(url, wait_until="domcontentloaded", timeout=120000)
        except: print("   ❌ Erro"); continue
        time.sleep(8)
        bt = page.inner_text("body", timeout=5000).lower()[:200]
        if "escaneie" in bt or "conectar" in bt:
            print("   ⚠️ QR Code! Escaneie...")
            for _ in range(36):
                time.sleep(5)
                bt = page.inner_text("body", timeout=5000).lower()[:200]
                if "escaneie" not in bt and "conectar" not in bt: break
            else: print("   ❌ QR nao escaneado"); continue
        if "inválido" in bt or "invalid" in bt: print("   ⚠️ Invalido"); marcar(lead["id"], "perdido"); continue
        try: page.wait_for_selector('div[contenteditable="true"]', timeout=35000)
        except: print("   ⚠️ Campo nao apareceu"); continue
        time.sleep(2)
        btn = page.locator('button[aria-label="Enviar"], button[aria-label="Send"]')
        if btn.count() > 0: btn.first.click(); print("   ✅ Enviado!")
        else:
            ed = page.locator('div[contenteditable="true"]')
            if ed.count() > 0: ed.first.click(); time.sleep(1); page.keyboard.press("Enter"); print("   ✅ Enviado via Enter!")
            else: print("   ❌ Botao nao encontrado"); continue
        time.sleep(4); marcar(lead["id"], "abordado"); print("   ✅ Marcado")
        if i < len(leads) - 1:
            print("   ⏳ 7min...")
            for s in range(420, 0, -1):
                if s % 60 == 0 or s <= 10: print(f"   {s//60}min {s%60:02d}s", end="\r")
                time.sleep(1)
            print()
    browser.close()
print(f"\n✅ Concluido!")
