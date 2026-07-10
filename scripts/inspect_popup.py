#!/usr/bin/env python3
"""
Inspeciona o popup de marketing "As etiquetas agora sao as Listas" do WhatsApp Web.
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

    # Reusa pagina existente ou cria
    wa_page = None
    for pg in context.pages:
        if "web.whatsapp.com" in getattr(pg, "url", ""):
            wa_page = pg
            break
    if not wa_page:
        wa_page = await context.new_page()
        await wa_page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    # Aguarda login
    try:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        logger.info("WhatsApp carregado")
    except Exception:
        logger.info("Aguardando QR...")
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=240000)
        logger.info("WhatsApp carregado")

    # Fecha about:blank
    for pg in list(context.pages):
        if pg is not wa_page and getattr(pg, "url", "") == "about:blank":
            try:
                await pg.close()
            except Exception:
                pass

    # Aguarda um pouco para o popup aparecer
    await asyncio.sleep(3)

    # Verifica se existe dialog
    dialog = wa_page.locator('[role="dialog"][aria-modal="true"]')
    count = await dialog.count()
    logger.info("Dialogs encontrados: %d", count)

    if count > 0:
        # Extrai estrutura do popup via evaluate
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
                        aria_labelledby: d.getAttribute('aria-labelledby') || '',
                        tabindex: d.getAttribute('tabindex') || '',
                        class: d.className || '',
                    };

                    // Texto do dialog
                    info.text_content = (d.textContent || '').substring(0, 500);

                    // Botoes dentro do dialog
                    const botoes = d.querySelectorAll('button, [role="button"], a[role="button"]');
                    info.botoes = [];
                    for (const b of botoes) {
                        info.botoes.push({
                            text: (b.textContent || '').trim().substring(0, 100),
                            data_testid: b.getAttribute('data-testid') || '',
                            aria_label: b.getAttribute('aria-label') || '',
                            title: b.getAttribute('title') || '',
                            class: b.className || '',
                            tag: b.tagName,
                            type: b.getAttribute('type') || '',
                            disabled: b.hasAttribute('disabled'),
                        });
                    }

                    // SVGs de fechar
                    const svgs = d.querySelectorAll('svg, [data-icon="close"], [data-testid*="close"], [data-testid*="x"], [data-testid*="exit"]');
                    info.svgs_fechar = [];
                    for (const s of svgs) {
                        info.svgs_fechar.push({
                            data_testid: s.getAttribute('data-testid') || '',
                            data_icon: s.getAttribute('data-icon') || '',
                            aria_hidden: s.getAttribute('aria-hidden') || '',
                            parent_tag: s.parentElement ? s.parentElement.tagName : '',
                            parent_data_testid: s.parentElement ? s.parentElement.getAttribute('data-testid') || '' : '',
                        });
                    }

                    // Elementos com tabindex (foco)
                    const focusable = d.querySelectorAll('[tabindex], input, button, select, textarea');
                    info.focusable = [];
                    for (const f of focusable) {
                        info.focusable.push({
                            tag: f.tagName,
                            tabindex: f.getAttribute('tabindex') || '',
                            data_testid: f.getAttribute('data-testid') || '',
                            text: (f.textContent || '').trim().substring(0, 50),
                        });
                    }

                    results.push(info);
                }
                return JSON.stringify(results, null, 2);
            }
        """)

        estrutura_json = json.loads(estrutura)
        logger.info("ESTRUTURA DO POPUP:")
        logger.info(json.dumps(estrutura_json, indent=2, ensure_ascii=False))

        # Tenta fechar com Escape
        logger.info("Tentando fechar com Escape...")
        await wa_page.keyboard.press("Escape")
        await asyncio.sleep(1)
        count_after = await dialog.count()
        logger.info("Dialog apos Escape: %d", count_after)

        if count_after > 0:
            # Tenta clicar no primeiro botao visivel
            for btn_info in estrutura_json[0]["botoes"]:
                logger.info("Tentando clicar em: %s (data-testid=%s)", btn_info["text"], btn_info["data_testid"])
                if btn_info["data_testid"]:
                    btn = wa_page.locator(f'[data-testid="{btn_info["data_testid"]}"]')
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await asyncio.sleep(1)
                        count_after2 = await dialog.count()
                        logger.info("Dialog apos clique em %s: %d", btn_info["data_testid"], count_after2)
                        if count_after2 == 0:
                            logger.info("Popup fechado com sucesso!")
                            break
    else:
        logger.info("Nenhum dialog encontrado. Tentando forcar aparecimento...")
        # Tenta navegar para uma conversa para ver se o popup aparece
        logger.info("Popup nao apareceu - pode ser que ja tenha sido fechado anteriormente")

    await asyncio.sleep(2)
    await context.close()
    await p.stop()
    logger.info("Fim da inspecao")


if __name__ == "__main__":
    asyncio.run(run())
