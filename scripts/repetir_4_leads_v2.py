#!/usr/bin/env python3
"""
Repete os 4 leads inconclusivos com extracao em camadas e modal fixo.
Nao envia mensagens. Nao escreve no Supabase.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import requests
import logging
logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

LEADS = [
    ("Erica Freire - Estetica", "51d1a2ba-1944-45ee-93f1-d51519b2b437"),
    ("Danielle Lopes Pilates", "a39427c6-66a6-46f4-9444-6d4c212351ac"),
    ("Lift Life", "da373706-ad67-4377-a16c-7833761fdda4"),
    ("Betapetsbr Banho e Tosa", "7ae99928-9fd3-4455-8ddd-b33f206f70a8"),
]

PROFILE_PATH = str(Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Profile 4")
CHROME_ARGS = [
    "--no-first-run", "--no-service-runner", "--no-default-browser-check",
    "--disable-background-networking", "--disable-client-side-phishing-detection",
    "--disable-crash-reporter", "--disable-extensions",
    "--disable-features=TranslateUI", "--disable-hang-monitor",
    "--disable-popup-blocking", "--disable-prompt-on-repost",
    "--disable-sync", "--disable-translate", "--metrics-recording-only",
    "--no-crash-upload", "--password-store=basic", "--start-maximized",
]


def get_lead(lead_id):
    """Busca lead no Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/leads?select=id,nome,telefone&id=eq.{lead_id}"
    r = requests.get(url, headers={
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    })
    if r.ok and r.json():
        return r.json()[0]
    return None


async def run():
    from playwright.async_api import async_playwright
    from whatsapp_match.matcher import fazer_match_completo, _fechar_modal

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            channel="chrome",
            headless=False,
            args=CHROME_ARGS,
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        print(f"  [DEBUG] page.url = {page.url!r}")
        print(f"  [DEBUG] browser.pages count = {len(browser.pages)}")
        # Se a primeira pagina nao for WhatsApp, usa a que for
        if page.url and "web.whatsapp.com" not in page.url:
            whatsapp_page = None
            for p in browser.pages:
                print(f"  [DEBUG]   page url = {p.url!r}")
                if "web.whatsapp.com" in p.url:
                    whatsapp_page = p
                    break
            if whatsapp_page:
                page = whatsapp_page
                print(f"  [DEBUG] Usando pagina WhatsApp: {page.url!r}")
            else:
                print(f"  [DEBUG] Nenhuma pagina WhatsApp encontrada!")
                # Tenta navegar e aguarda autenticação
                await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                print(f"  [DEBUG] Navegou para: {page.url!r}")
                print(f"  [INFO] Se QR code visivel, escaneie em 30s...")
                try:
                    # Aguarda até detectar que está autenticado (side不放,chat-list aparece)
                    await page.wait_for_selector("#side", timeout=30000)
                    print(f"  [INFO] WhatsApp autenticado!")
                except Exception as e:
                    print(f"  [ERRO] Timeout aguardando autenticacao: {e}")

        # Fecha modal ANTES de tudo
        modal_fechado = await _fechar_modal(page)
        print(f"[MODAL] {'Fechado com exito' if modal_fechado else 'Nenhum modal encontrado'}")

        for nome, lead_id in LEADS:
            print(f"\n{'='*60}")
            print(f"Lead: {nome}")

            lead = get_lead(lead_id)
            if not lead:
                print(f"  ERRO: Lead nao encontrado no Supabase")
                continue

            telefone_raw = lead.get("telefone", "")
            from utils.phone_utils import normalizar_telefone_br
            telefone = normalizar_telefone_br(telefone_raw)
            print(f"  ID:   {lead_id}")
            print(f"  Tel:  {telefone[:6]}***{telefone[-4:]}")

            result = await fazer_match_completo(
                page=page,
                lead_id=lead_id,
                phone_normalized=telefone,
                campaign_key="avgestao:assistencias:primeiro_contato:v1",
            )

            print(f"  Status:     {result.status.value}")
            print(f"  Chat found: {result.chat_found}")
            print(f"  Outbound:   {result.outbound_found}")
            print(f"  Campaign:   {result.campaign_match}")
            print(f"  Tempo:      { {k: f'{v:.1f}s' for k, v in result.timings.items()} }")
            if result.error_message:
                print(f"  Erro:      {result.error_message}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
