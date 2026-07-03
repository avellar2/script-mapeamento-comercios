#!/usr/bin/env python3
"""Inspeciona o DOM real para encontrar marcadores de outbound."""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from playwright.async_api import async_playwright
from config.whatsapp_selectors import SEARCH_BOX_SELECTORS, CHAT_ITEM_SELECTORS, encontrar_seletor_rapido
from utils.phone_utils import normalizar_telefone_br

PHONE = "21989299770"
PHONE_CANONICO = normalizar_telefone_br(PHONE)
PROFILE_DIR = Path("profiles/whatsapp_match")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR.resolve()), headless=False, channel="chromium", args=["--no-sandbox"])
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        search_sel = await encontrar_seletor_rapido(page, SEARCH_BOX_SELECTORS, 3000)
        search = page.locator(search_sel)
        await search.click(); await search.fill(""); await page.wait_for_timeout(200)
        await search.fill(PHONE_CANONICO); await page.wait_for_timeout(2000)

        chat_sel = await encontrar_seletor_rapido(page, CHAT_ITEM_SELECTORS, 3000)
        chat = page.locator(chat_sel).first
        await chat.click(); await page.wait_for_timeout(4000)

        # Inspeção profunda: pseudo-elementos, computed styles, estrutura
        info = await page.evaluate("""() => {
            const panel = document.querySelector('div[data-testid="conversation-panel-messages"]');
            if (!panel) return {error: 'panel not found'};

            const children = panel.children;
            const result = {totalChildren: children.length, samples: []};

            for (let i = 0; i < Math.min(children.length, 10); i++) {
                const child = children[i];
                const sample = {
                    index: i,
                    tagName: child.tagName,
                    // Verifica pseudo-elementos
                    beforeContent: window.getComputedStyle(child, '::before').content,
                    afterContent: window.getComputedStyle(child, '::after').content,
                    // Computed styles do container
                    justifyContent: window.getComputedStyle(child).justifyContent,
                    alignItems: window.getComputedStyle(child).alignItems,
                    flexDirection: window.getComputedStyle(child).flexDirection,
                    // Texto completo (inclui pseudo-elementos)
                    textContent: child.textContent?.substring(0, 100) || '',
                    // data-testid
                    dataTestid: child.getAttribute('data-testid') || '',
                    // Classes
                    className: child.className?.substring(0, 200) || '',
                };

                // Procura msg-container dentro
                const msgContainers = child.querySelectorAll('[data-testid="msg-container"]');
                sample.msgContainers = [];
                for (const mc of msgContainers) {
                    sample.msgContainers.push({
                        beforeContent: window.getComputedStyle(mc, '::before').content,
                        afterContent: window.getComputedStyle(mc, '::after').content,
                        textContent: mc.textContent?.substring(0, 100) || '',
                        className: mc.className?.substring(0, 200) || '',
                    });
                }

                result.samples.push(sample);
            }
            return result;
        }""")

        print(json.dumps(info, indent=2, ensure_ascii=False))
        await context.close()

asyncio.run(main())