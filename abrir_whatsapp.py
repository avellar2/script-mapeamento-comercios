#!/usr/bin/env python3
"""Abre WhatsApp Business Web e mantem aberto. Apenas para escanear QR Code."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent))
from config.lock_whatsapp_sender import LockWhatsAppSender

PROFILE_DIR = Path(".whatsapp_business_profile")

print("Abrindo WhatsApp Business Web...")
print(f"Perfil: {PROFILE_DIR}")
print()
print("Na primeira vez: escaneie o QR Code com o WhatsApp Business.")
print("Apos escanear, feche esta janela manualmente (Ctrl+C).")
print()

# Adquire lock global do perfil dos senders
with LockWhatsAppSender() as lock:
    if not lock.acquired:
        print("ERRO: Já existe um sender ativo usando o perfil WhatsApp.")
        print("Feche o outro processo antes de abrir novamente.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        # Espera ate o usuario fechar
        print("WhatsApp Business aberto. Pressione Ctrl+C para fechar.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("\nFechando...")
            browser.close()