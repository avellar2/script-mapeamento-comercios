#!/usr/bin/env python3
"""
Debug: testa busca WhatsApp com logging detalhado.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from dotenv import load_dotenv
from supabase import create_client
from utils.phone_utils import normalizar_telefone_br

DOTENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(DOTENV)

PROFILE_DIR = Path(r"C:\projetos\script-mapear-comercios-whatsapp-dedup\profiles\whatsapp_match")
LEAD_ID = "51d1a2ba-1944-45ee-93f1-d51519b2b437"  # Erica Freire

async def main():
    print(f"Abrindo perfil: {PROFILE_DIR}")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        
        page = await context.new_page()
        
        print("Navegando para WhatsApp Web...")
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded", timeout=15000)
        
        # Verifica se ha QR code
        qr = page.locator('canvas[aria-label*="QR code"], img[alt="QR code"]')
        if await qr.count() > 0:
            print("QR Code presente! Aguardando escaneamento...")
            try:
                await qr.wait_for(state="hidden", timeout=120000)
                print("QR Code escaneado.")
            except:
                print("QR Code ainda presente.")
                await page.screenshot(path="output/debug_qr.png")
                await context.close()
                return
        else:
            print("Ja autenticado.")
        
        # Aguarda carregamento
        print("Aguardando #side...")
        try:
            await page.wait_for_selector("#side", timeout=30000)
            print("  #side OK")
        except Exception as e:
            print(f"  #side NAO encontrado: {e}")
            await page.screenshot(path="output/debug_no_side.png")
            await context.close()
            return
        
        print("Aguardando campo de busca...")
        try:
            await page.wait_for_selector('#side input[role="textbox"]', timeout=30000)
            print("  Campo de busca OK")
        except Exception as e:
            print(f"  Campo de busca NAO encontrado: {e}")
            await page.screenshot(path="output/debug_no_search.png")
            await context.close()
            return
        
        # Busca lead no Supabase
        print(f"\nBuscando lead {LEAD_ID[:8]}... no Supabase...")
        supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        resp = supabase.table("leads").select("id,nome,telefone").eq("id", LEAD_ID).execute()
        
        if not resp.data:
            print("  Lead nao encontrado!")
            await context.close()
            return
        
        lead = resp.data[0]
        telefone_raw = lead.get("telefone", "")
        telefone_canonico = normalizar_telefone_br(telefone_raw)
        print(f"  Nome: {lead['nome']}")
        print(f"  Telefone raw: {telefone_raw}")
        print(f"  Telefone canonico: {telefone_canonico}")
        
        # Preenche busca
        print(f"\nPreenchendo busca com: {telefone_canonico[:6]}...")
        search_box = page.locator('#side input[role="textbox"]')
        await search_box.fill(telefone_canonico)
        print("  Preenchido.")
        
        print("Aguardando 3s...")
        await page.wait_for_timeout(3000)
        
        # Conta resultados
        print("Contando chat-list-item...")
        chat_items = page.locator('[data-testid="chat-list-item"]')
        count = await chat_items.count()
        print(f"  Resultados: {count}")
        
        if count > 0:
            print("  ABRINDO conversa...")
            await chat_items.first.click()
            await page.wait_for_timeout(2000)
            
            # Captura painel info
            print("  Clicando header para painel...")
            header = page.locator('div[data-testid="conversation-panel-header"]')
            if await header.count() > 0:
                await header.first.click()
                await page.wait_for_timeout(1000)
                
                print("  Salvando screenshot do painel...")
                await page.screenshot(path="output/debug_painel.png")
                
                # Volta
                back = page.locator('[data-testid="btn-back"]')
                if await back.count() > 0:
                    await back.first.click()
                    await page.wait_for_timeout(300)
            else:
                print("  Header NAO encontrado")
        else:
            print("  Sem resultados - tentando screenshot")
            await page.screenshot(path="output/debug_no_results.png")
        
        await context.close()
        print("\nFeito.")

if __name__ == "__main__":
    asyncio.run(main())
