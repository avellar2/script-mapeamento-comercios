#!/usr/bin/env python3
"""
Debug: testa diferentes formatos de busca no WhatsApp Web.
NAO envia mensagens. NAO escreve no Supabase.
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
from utils.phone_utils import normalizar_telefone_br, variantes_busca_telefone

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
        
        qr = page.locator('canvas[aria-label*="QR code"], img[alt="QR code"]')
        if await qr.count() > 0:
            print("QR Code presente! Aguardando escaneamento...")
            try:
                await qr.wait_for(state="hidden", timeout=120000)
                print("QR Code escaneado.")
            except:
                print("QR Code ainda presente.")
                await context.close()
                return
        else:
            print("Ja autenticado.")
        
        await page.wait_for_selector("#side", timeout=30000)
        await page.wait_for_selector('#side input[role="textbox"]', timeout=30000)
        print("WhatsApp carregado.")
        
        # Busca lead no Supabase
        supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        resp = supabase.table("leads").select("id,nome,telefone").eq("id", LEAD_ID).execute()
        lead = resp.data[0]
        telefone_raw = lead.get("telefone", "")
        telefone_canonico = normalizar_telefone_br(telefone_raw)
        
        print(f"\nLead: {lead['nome']}")
        print(f"Telefone raw: {telefone_raw}")
        print(f"Telefone canonico: {telefone_canonico}")
        
        # Gera variantes
        variantes = variantes_busca_telefone(telefone_raw)
        print(f"Variantes: {variantes}")
        
        # Tenta cada variante
        for i, variante in enumerate(variantes):
            print(f"\n--- Variante {i+1}: {variante[:6]}... ---")
            
            # Limpa busca
            search_box = page.locator('#side input[role="textbox"]')
            await search_box.fill("")
            await page.wait_for_timeout(500)
            
            # Preenche
            await search_box.fill(variante)
            await page.wait_for_timeout(3000)
            
            # Conta resultados
            chat_items = page.locator('[data-testid="chat-list-item"]')
            count = await chat_items.count()
            print(f"  Resultados: {count}")
            
            if count > 0:
                # Pega nome do primeiro resultado
                first = chat_items.first
                title_el = first.locator('[data-testid="cell-title"] span, span[title]')
                if await title_el.count() > 0:
                    title = await title_el.first.text_content()
                    print(f"  Primeiro resultado: {title}")
                
                # Tenta abrir e verificar telefone
                await first.click()
                await page.wait_for_timeout(2000)
                
                # Tenta extrair telefone do header/painel
                # Verifica se ha outbound
                outgoing = page.locator('[data-testid="outgoing"]')
                outbound_count = await outgoing.count()
                print(f"  Outbound: {outbound_count}")
                
                # Clica no header para info
                header = page.locator('div[data-testid="conversation-panel-header"]')
                if await header.count() > 0:
                    await header.first.click()
                    await page.wait_for_timeout(1000)
                    
                    # Procura telefone
                    phone_spans = page.locator('span[title*="+"]')
                    phone_count = await phone_spans.count()
                    print(f"  span[title*='+'] count: {phone_count}")
                    for j in range(phone_count):
                        title = await phone_spans.nth(j).get_attribute("title")
                        if title:
                            print(f"    title: {title[:3]}***{title[-4:] if len(title)>7 else '***'}")
                    
                    # Procura tel: links
                    tel_links = page.locator('a[href*="tel:"]')
                    tel_count = await tel_links.count()
                    print(f"  a[href*='tel:'] count: {tel_count}")
                    for j in range(tel_count):
                        href = await tel_links.nth(j).get_attribute("href")
                        if href:
                            print(f"    href: {href[:10]}***")
                    
                    # Procura aria-label
                    aria_phone = page.locator('[aria-label*="+55"]')
                    aria_count = await aria_phone.count()
                    print(f"  [aria-label*='+55'] count: {aria_count}")
                    for j in range(min(3, aria_count)):
                        label = await aria_phone.nth(j).get_attribute("aria-label")
                        if label:
                            print(f"    aria-label: {label[:6]}***")
                    
                    # Procura data-id com JID
                    jid_els = page.locator('[data-id*="@s.whatsapp.net"]')
                    jid_count = await jid_els.count()
                    print(f"  [data-id*='@s.whatsapp.net'] count: {jid_count}")
                    for j in range(min(3, jid_count)):
                        data_id = await jid_els.nth(j).get_attribute("data-id")
                        if data_id:
                            # Mascarar: mostrar apenas ultimos 4 digitos
                            num = data_id.split("@")[0]
                            print(f"    JID: ...{num[-4:]}@s.whatsapp.net")
                    
                    # Volta
                    back = page.locator('[data-testid="btn-back"]')
                    if await back.count() > 0:
                        await back.first.click()
                        await page.wait_for_timeout(300)
                else:
                    print("  Header nao encontrado")
                
                break  # Encontrou resultado, para
        
        await context.close()
        print("\nFeito.")

if __name__ == "__main__":
    asyncio.run(main())