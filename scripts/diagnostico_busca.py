#!/usr/bin/env python3
"""
Diagnostico rapido: testa se o campo de busca funciona apos fechar modal.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"


async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            channel="chromium",
            args=["--no-sandbox"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        print("Aguardando autenticacao...")

        for attempt in range(60):
            await page.wait_for_timeout(5000)
            try:
                search = page.locator('#side input[role="textbox"]')
                count = await search.count()
                if count > 0:
                    print(f"Autenticado! (tentativa {attempt+1})")
                    break
            except Exception:
                pass
            if attempt == 0:
                print("QR Code? Escaneie!")

        await page.wait_for_timeout(3000)

        # 1. Verifica modal
        modal = page.locator('div[data-testid="confirm-popup"]')
        print(f"\n1. Modal confirm-popup: {await modal.count()}")

        # 2. Tenta fechar
        if await modal.count() > 0:
            print("Fechando modal...")
            # Tenta encontrar o botao exato
            buttons = modal.locator("button, [role='button']")
            btn_count = await buttons.count()
            print(f"  Botoes: {btn_count}")
            for i in range(btn_count):
                aria = await buttons.nth(i).get_attribute("aria-label")
                testid = await buttons.nth(i).get_attribute("data-testid")
                text = await buttons.nth(i).text_content()
                print(f"  [{i}] aria={aria} testid={testid} text={(text or '').strip()[:60]}")

            # Tenta Escape
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)
            print(f"  Apos Escape: {await modal.count()}")

            if await modal.count() > 0:
                # Tenta botao
                if btn_count > 0:
                    await buttons.first.click()
                    await page.wait_for_timeout(1000)
                    print(f"  Apos click botao: {await modal.count()}")

            if await modal.count() > 0:
                # Tenta click fora
                await page.mouse.click(5, 5)
                await page.wait_for_timeout(1000)
                print(f"  Apos click fora: {await modal.count()}")

        # 3. Testa busca
        print("\n3. Testando campo de busca...")
        search_box = page.locator('#side input[role="textbox"]')
        await search_box.click()
        print("  Click OK")
        await search_box.fill("")
        print("  Clear OK")
        await page.wait_for_timeout(200)
        await search_box.fill("21989299770")
        print("  Preenchido: 21989299770")
        await page.wait_for_timeout(2000)

        # Verifica se apareceu resultado
        chat_list = page.locator('div[data-testid="chat-list"]')
        print(f"  chat-list: {await chat_list.count()}")

        chat_items = page.locator('div[data-testid="chat-list-item"]')
        print(f"  chat-list-item: {await chat_items.count()}")

        # Verifica se o campo ainda tem o valor
        value = await search_box.input_value()
        print(f"  Valor no campo: {value}")

        # Tenta com Enter
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)
        chat_items2 = page.locator('div[data-testid="chat-list-item"]')
        print(f"  Apos Enter - chat-list-item: {await chat_items2.count()}")

        # Verifica se modal reapareceu
        print(f"  Modal apos busca: {await modal.count()}")

        # Screenshot
        await page.screenshot(path="output/diagnostico_busca.png")
        print("  Screenshot salvo em output/diagnostico_busca.png")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
