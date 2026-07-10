#!/usr/bin/env python3
"""
Forca aparecimento do popup "As etiquetas agora sao as Listas" e inspeciona.
NAO registra conversas, telefones ou mensagens. Apenas estrutura do popup.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("inspect-popup")

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"


async def run():
    from playwright.async_api import async_playwright

    p = await async_playwright().start()
    context = await p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR.resolve()),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    wa_page = None
    for pg in context.pages:
        if "web.whatsapp.com" in getattr(pg, "url", ""):
            wa_page = pg
            break
    if not wa_page:
        wa_page = await context.new_page()
        await wa_page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    try:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        logger.info("WhatsApp carregado")
    except Exception:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=240000)
        logger.info("WhatsApp carregado")

    for pg in list(context.pages):
        if pg is not wa_page and getattr(pg, "url", "") == "about:blank":
            try:
                await pg.close()
            except Exception:
                pass

    await asyncio.sleep(2)

    # Verifica se existe dialog
    dialog = wa_page.locator('[role="dialog"][aria-modal="true"]')
    count = await dialog.count()
    logger.info("Dialogs visiveis: %d", count)

    # Procura no DOM inteiro por elementos com texto "etiquetas" ou "Listas"
    estrutura_oculta = await wa_page.evaluate("""
        () => {
            // Procura por texto "etiquetas" ou "Listas" em qualquer elemento
            const all = document.querySelectorAll('*');
            const matches = [];
            for (const el of all) {
                if (el.children.length > 0) continue; // so folhas
                const text = (el.textContent || '').trim();
                if (text.includes('etiquetas') || text.includes('Listas')) {
                    // Sobe ate achar um dialog ou container
                    let parent = el;
                    for (let i = 0; i < 10; i++) {
                        if (!parent) break;
                        if (parent.getAttribute('role') === 'dialog' || parent.getAttribute('aria-modal') === 'true') {
                            matches.push({
                                text: text.substring(0, 200),
                                parent_role: parent.getAttribute('role') || '',
                                parent_aria_modal: parent.getAttribute('aria-modal') || '',
                                parent_data_testid: parent.getAttribute('data-testid') || '',
                                parent_class: (parent.className || '').substring(0, 100),
                                parent_tabindex: parent.getAttribute('tabindex') || '',
                                depth: i,
                            });
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
            }
            return JSON.stringify(matches, null, 2);
        }
    """)
    logger.info("Elementos com 'etiquetas' ou 'Listas' no DOM:")
    logger.info(estrutura_oculta)

    # Tenta forcar o popup abrindo uma conversa existente
    # Clica no primeiro chat da lista
    logger.info("Tentando abrir primeiro chat da lista para forcar popup...")
    first_chat = wa_page.locator('div[data-testid="chat-list"] div[role="row"]').first
    if await first_chat.count() > 0:
        await first_chat.click()
        await asyncio.sleep(3)

        # Verifica dialog novamente
        count2 = await dialog.count()
        logger.info("Dialogs apos abrir chat: %d", count2)

        if count2 > 0:
            estrutura = await wa_page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('[role="dialog"][aria-modal="true"]');
                    const results = [];
                    for (const d of dialogs) {
                        const info = {
                            data_testid: d.getAttribute('data-testid') || '',
                            role: d.getAttribute('role') || '',
                            aria_modal: d.getAttribute('aria-modal') || '',
                            aria_label: d.getAttribute('aria-label') || '',
                            tabindex: d.getAttribute('tabindex') || '',
                            class: (d.className || '').substring(0, 200),
                        };
                        info.text_content = (d.textContent || '').substring(0, 500);
                        const botoes = d.querySelectorAll('button, [role="button"]');
                        info.botoes = [];
                        for (const b of botoes) {
                            info.botoes.push({
                                text: (b.textContent || '').trim().substring(0, 100),
                                data_testid: b.getAttribute('data-testid') || '',
                                aria_label: b.getAttribute('aria-label') || '',
                                title: b.getAttribute('title') || '',
                                tag: b.tagName,
                                type: b.getAttribute('type') || '',
                                disabled: b.hasAttribute('disabled'),
                            });
                        }
                        results.push(info);
                    }
                    return JSON.stringify(results, null, 2);
                }
            """)
            logger.info("ESTRUTURA DO POPUP:")
            logger.info(estrutura)
        else:
            logger.info("Popup nao apareceu mesmo apos abrir chat")
    else:
        logger.info("Nenhum chat na lista")

    await asyncio.sleep(2)
    await context.close()
    await p.stop()
    logger.info("Fim da inspecao")


if __name__ == "__main__":
    asyncio.run(run())
