#!/usr/bin/env python3
"""
Diagnostico DOM: inspeciona painel de informacoes de conversas reais.
Busca telefones do Supabase. Fecha modal primeiro. Nao envia mensagens.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from utils.phone_utils import normalizar_telefone_br
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from supabase import create_client

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"

LEADS = [
    ("TECM TECNOLOGIA", "65bc876e-9836-4d7d-ab94-e54873ea4d5e"),
    ("Erica Freire", "51d1a2ba-1944-45ee-93f1-d51519b2b437"),
    ("Danielle Lopes", "a39427c6-66a6-46f4-9444-6d4c212351ac"),
    ("Lift Life", "da373706-ad67-4377-a16c-7833761fdda4"),
    ("Betapetsbr", "7ae99928-9fd3-4455-8ddd-b33f206f70a8"),
]


async def fechar_modal(page):
    """Tenta fechar o modal confirm-popup de varias formas."""
    modal = page.locator('div[data-testid="confirm-popup"]')
    count = await modal.count()
    if count == 0:
        return True

    print(f"\n  Modal confirm-popup detectado! Fechando...")

    # 1. Escape
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(1000)
    if await modal.count() == 0:
        print("  Fechado com Escape")
        return True

    # 2. Botao dentro do modal
    buttons = modal.locator("button, [role='button']")
    btn_count = await buttons.count()
    print(f"  Botoes no modal: {btn_count}")
    for i in range(btn_count):
        aria = await buttons.nth(i).get_attribute("aria-label")
        testid = await buttons.nth(i).get_attribute("data-testid")
        text = await buttons.nth(i).text_content()
        print(f"    [{i}] aria={aria} testid={testid} text={(text or '').strip()[:50]}")
        # Clica no primeiro botao seguro
        if i == 0:
            await buttons.nth(i).click()
            await page.wait_for_timeout(1000)
            if await modal.count() == 0:
                print(f"  Fechado com botao [{i}]")
                return True

    # 3. Click fora
    await page.mouse.click(10, 10)
    await page.wait_for_timeout(1000)
    if await modal.count() == 0:
        print("  Fechado click fora")
        return True

    print("  NAO foi possivel fechar o modal")
    return False


async def diagnosticar_painel(page, nome, telefone_canonico):
    tel_mask = f"+{telefone_canonico[:2]}*****{telefone_canonico[-4:]}" if telefone_canonico and len(telefone_canonico) > 6 else "N/A"
    print(f"\n=== {nome} ({tel_mask}) ===")

    # 1. Clica header
    print("\n1. HEADER:")
    try:
        header = page.locator('div[data-testid="conversation-header"]')
        count = await header.count()
        print(f"  conversation-header: {count}")
        if count > 0:
            await header.first.click()
            await page.wait_for_timeout(500)
    except Exception as e:
        print(f"  Erro: {e}")

    # 2. Painel
    print("\n2. PAINEL DE INFO:")
    try:
        # span[title*="+"]
        phone_spans = page.locator('span[title*="+"]')
        count = await phone_spans.count()
        print(f"  span[title*='+']: {count}")
        for i in range(count):
            title = await phone_spans.nth(i).get_attribute("title")
            text = await phone_spans.nth(i).text_content()
            if title:
                tel = normalizar_telefone_br(title)
                print(f"    [{i}] title={title} -> norm={tel} match={tel == telefone_canonico if tel else False}")
            if text and text.strip():
                tel = normalizar_telefone_br(text)
                print(f"    [{i}] text={text.strip()[:40]} -> norm={tel}")

        # a[href*="tel:"]
        tel_links = page.locator('a[href*="tel:"]')
        count = await tel_links.count()
        print(f"  a[href*='tel:']: {count}")
        for i in range(count):
            href = await tel_links.nth(i).get_attribute("href")
            text = await tel_links.nth(i).text_content()
            print(f"    [{i}] href={href} text={text.strip()[:30] if text else ''}")

        # data-testid com phone
        phone_testids = page.locator('[data-testid*="phone"], [data-testid*="Phone"]')
        count = await phone_testids.count()
        print(f"  [data-testid*='phone']: {count}")
        for i in range(count):
            testid = await phone_testids.nth(i).get_attribute("data-testid")
            text = await phone_testids.nth(i).text_content()
            print(f"    [{i}] testid={testid} text={text.strip()[:30] if text else ''}")

        # aria-label com telefone
        aria_phone = page.locator('[aria-label*="+55"], [aria-label*="55"]')
        count = await aria_phone.count()
        print(f"  [aria-label*='+55'/'55']: {count}")
        for i in range(count):
            label = await aria_phone.nth(i).get_attribute("aria-label")
            print(f"    [{i}] aria-label={label}")

        # title com +55
        all_titles = page.locator('[title*="+55"], [title*="55"]')
        count = await all_titles.count()
        print(f"  [title*='+55'/'55']: {count}")
        for i in range(min(count, 10)):
            title = await all_titles.nth(i).get_attribute("title")
            tag = await all_titles.nth(i).evaluate("el => el.tagName")
            print(f"    [{i}] <{tag}> title={title}")

        # JID
        jid_elements = page.locator('[data-id*="@s.whatsapp.net"]')
        count = await jid_elements.count()
        print(f"  [data-id*='@s.whatsapp.net']: {count}")
        for i in range(min(count, 5)):
            data_id = await jid_elements.nth(i).get_attribute("data-id")
            print(f"    [{i}] data-id={data_id}")

    except Exception as e:
        print(f"  Erro: {e}")

    # 3. Voltar
    try:
        back = page.locator('button[aria-label*="voltar" i], button[aria-label*="back" i]')
        if await back.count() > 0:
            await back.first.click()
            await page.wait_for_timeout(300)
    except Exception:
        pass


async def pesquisar_e_abrir(page, telefone):
    """Pesquisa telefone e abre a conversa."""
    search_box = page.locator('#side input[role="textbox"]')
    await search_box.click()
    await search_box.fill("")
    await page.wait_for_timeout(200)
    await search_box.fill(telefone)
    await page.wait_for_timeout(1500)

    # Verifica se apareceu chat
    chat_item = page.locator('div[data-testid="chat-list-item"]').first
    count = await chat_item.count()
    if count > 0:
        await chat_item.click()
        await page.wait_for_timeout(2000)
        return True
    return False


async def main():
    print("=" * 60)
    print("  DIAGNOSTICO DOM - PAINEL DE INFORMACOES")
    print("=" * 60)

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    leads_info = []
    for nome, lid in LEADS:
        resp = client.table("leads").select("telefone_normalizado,telefone").eq("id", lid).execute()
        if resp.data:
            d = resp.data[0]
            tel = d.get("telefone_normalizado") or normalizar_telefone_br(d.get("telefone", ""))
            leads_info.append((nome, tel))
            print(f"  {nome}: +{tel[:2]}*****{tel[-4:]}" if tel and len(tel) > 6 else f"  {nome}: SEM TELEFONE")
        else:
            print(f"  {nome}: NAO ENCONTRADO")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            channel="chromium",
            args=["--no-sandbox"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        print("\nAguardando autenticacao...")

        authed = False
        for attempt in range(60):
            await page.wait_for_timeout(5000)
            try:
                search = page.locator('#side input[role="textbox"]')
                count = await search.count()
                if count > 0:
                    authed = True
                    print(f"Autenticado! (tentativa {attempt+1})")
                    break
            except Exception:
                pass
            if attempt == 0:
                print("QR Code visivel? Escaneie agora!")

        if not authed:
            print("NAO AUTENTICADO")
            await context.close()
            return

        await page.wait_for_timeout(3000)

        # Fecha modal
        await fechar_modal(page)

        # Para cada lead
        for nome, tel in leads_info:
            if not tel:
                continue
            ddd_numero = tel[2:] if tel.startswith("55") else tel
            print(f"\n--- Pesquisando: {ddd_numero} ---")
            encontrou = await pesquisar_e_abrir(page, ddd_numero)
            if encontrou:
                await diagnosticar_painel(page, nome, tel)
            else:
                print(f"  Nenhum chat encontrado")
                # Verifica se modal reapareceu
                modal = page.locator('div[data-testid="confirm-popup"]')
                if await modal.count() > 0:
                    print("  MODAL REAPARECEU!")
                    await fechar_modal(page)
            await page.wait_for_timeout(1000)

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
