#!/usr/bin/env python3
"""Envia mensagens para os 5 leads aprovados da campanha assistencias"""
import os, json, time, ssl, urllib.request
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

NOMES = [
    "Nick Cell - Assistência Técnica",
    "WR Smart (Conserto de Celular)",
    "Assistência técnica Freitas Cell",
    "MSC ASSISTÊNCIA TÉCNICA",
    "SWATCELL CONSERTOS DE CELULARES",
]

TEL = {
    "Nick Cell - Assistência Técnica": "5521990170874",
    "WR Smart (Conserto de Celular)": "5521985755184",
    "Assistência técnica Freitas Cell": "5521981780019",
    "MSC ASSISTÊNCIA TÉCNICA": "5521981209833",
    "SWATCELL CONSERTOS DE CELULARES": "5521970007855",
}

MSG = (
    "Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
    "Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.\n\n"
    "Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação "
    "e o cliente acompanha o reparo pelo próprio link.\n\n"
    "Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\n"
    "Posso liberar e configurar o acesso de vocês?"
)

def marcar(nome, status):
    from urllib.parse import quote as q
    ne = q(nome)
    body = json.dumps({"status": status, "ultimo_contato_em": datetime.now().isoformat()}).encode()
    req = urllib.request.Request(f"{API_URL}?nome=eq.{ne}", data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req, context=CTX): pass

profile = Path(__file__).parent / ".whatsapp_business_profile"
for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    p = profile / lock
    if p.exists(): p.unlink()

from playwright.sync_api import sync_playwright

print("=" * 60)
print(f"  Enviando 5 leads - Assistencias")
print(f"  {datetime.now().strftime('%H:%M')}")
print("=" * 60)

with sync_playwright() as pw:
    browser = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile), channel="chrome",
        headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--new-instance"],
        viewport={"width": 800, "height": 900}, locale="pt-BR",
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    for i, nome in enumerate(NOMES, 1):
        tel = TEL[nome]
        msg = MSG.format(nome=nome)
        url = f"https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}"

        print(f"\n[{i}/5] {nome}")
        print(f"   📞 {tel}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
        except:
            print("   ❌ Erro ao navegar")
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
                continue

        if "inválido" in bt or "invalid" in bt:
            print("   ⚠️ Número inválido")
            marcar(nome, "perdido")
            continue

        try:
            page.wait_for_selector('div[contenteditable="true"]', timeout=35000)
        except:
            print("   ⚠️ Campo nao apareceu")
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
                continue

        time.sleep(4)
        marcar(nome, "abordado")
        print("   ✅ Marcado no Supabase")

        if i < len(NOMES):
            print("   ⏳ 7min...")
            for s in range(420, 0, -1):
                if s % 60 == 0 or s <= 10:
                    print(f"   {s//60}min {s%60:02d}s", end="\r")
                time.sleep(1)
            print()

    browser.close()

print(f"\n✅ Envio concluido!")
