#!/usr/bin/env python3
"""
Reproduz e inspeciona o popup "As etiquetas agora sao as Listas" do WhatsApp Web.
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
logger = logging.getLogger("inspect-popup3")

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "avgestao" / "popup-inspect"


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

    for pg in list(context.pages):
        if pg is not wa_page and getattr(pg, "url", "") == "about:blank":
            try:
                await pg.close()
            except Exception:
                pass

    try:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        logger.info("WhatsApp carregado")
    except Exception:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=240000)
        logger.info("WhatsApp carregado")

    await asyncio.sleep(2)

    # Verifica se ja existe dialog
    dialog = wa_page.locator('[role="dialog"][aria-modal="true"]')
    count = await dialog.count()
    logger.info("Dialogs visiveis inicialmente: %d", count)

    if count == 0:
        # Tenta forcar o popup abrindo uma conversa existente
        logger.info("Tentando abrir primeiro chat para forcar popup...")
        first_chat = wa_page.locator('div[data-testid="chat-list"] div[role="row"]').first
        if await first_chat.count() > 0:
            await first_chat.click()
            await asyncio.sleep(3)
            count = await dialog.count()
            logger.info("Dialogs apos abrir chat: %d", count)

    if count == 0:
        # Tenta limpar localStorage para forcar o popup
        logger.info("Tentando limpar localStorage para forcar popup...")
        await wa_page.evaluate("""
            () => {
                // Remove chaves relacionadas a popups/labels/lists
                const keys = Object.keys(localStorage);
                for (const k of keys) {
                    if (k.toLowerCase().includes('label') || 
                        k.toLowerCase().includes('list') || 
                        k.toLowerCase().includes('popup') ||
                        k.toLowerCase().includes('dialog') ||
                        k.toLowerCase().includes('confirm') ||
                        k.toLowerCase().includes('etiqueta') ||
                        k.toLowerCase().includes('nux')) {
                        localStorage.removeItem(k);
                    }
                }
            }
        """)
        await wa_page.reload()
        await asyncio.sleep(5)
        try:
            await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=30000)
        except Exception:
            pass
        count = await dialog.count()
        logger.info("Dialogs apos reload: %d", count)

    if count > 0:
        # Inspecao detalhada do popup
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
                        aria_describedby: d.getAttribute('aria-describedby') || '',
                        tabindex: d.getAttribute('tabindex') || '',
                        class: (d.className || '').substring(0, 200),
                        style: d.getAttribute('style') || '',
                    };
                    info.text_content = (d.textContent || '').substring(0, 1000);

                    // Todos os elementos clicaveis dentro do dialog
                    const clicaveis = d.querySelectorAll(
                        'button, [role="button"], a, input, select, textarea, ' +
                        '[tabindex]:not([tabindex="-1"]), ' +
                        'svg, [data-testid], [aria-label], [title]'
                    );
                    info.elementos_clicaveis = [];
                    const seen = new Set();
                    for (const el of clicaveis) {
                        const key = el.tagName + '|' + (el.getAttribute('data-testid') || '') + '|' + (el.textContent || '').trim().substring(0, 30);
                        if (seen.has(key)) continue;
                        seen.add(key);
                        
                        const rect = el.getBoundingClientRect();
                        const dialog_rect = d.getBoundingClientRect();
                        
                        info.elementos_clicaveis.push({
                            tag: el.tagName,
                            role: el.getAttribute('role') || '',
                            aria_label: el.getAttribute('aria-label') || '',
                            title: el.getAttribute('title') || '',
                            data_testid: el.getAttribute('data-testid') || '',
                            tabindex: el.getAttribute('tabindex') || '',
                            type: el.getAttribute('type') || '',
                            disabled: el.hasAttribute('disabled'),
                            text: (el.textContent || '').trim().substring(0, 80),
                            visible: rect.width > 0 && rect.height > 0,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            rel_x: Math.round(rect.x - dialog_rect.x),
                            rel_y: Math.round(rect.y - dialog_rect.y),
                            parent_tag: el.parentElement ? el.parentElement.tagName : '',
                            parent_data_testid: el.parentElement ? el.parentElement.getAttribute('data-testid') || '' : '',
                            parent_role: el.parentElement ? el.parentElement.getAttribute('role') || '' : '',
                        });
                    }

                    // Hierarquia de elementos com data-testid
                    info.hierarquia = [];
                    const all_with_testid = d.querySelectorAll('[data-testid]');
                    for (const el of all_with_testid) {
                        const testid = el.getAttribute('data-testid');
                        if (testid && !info.hierarquia.some(h => h.data_testid === testid)) {
                            const rect = el.getBoundingClientRect();
                            info.hierarquia.push({
                                data_testid: testid,
                                tag: el.tagName,
                                role: el.getAttribute('role') || '',
                                text: (el.textContent || '').trim().substring(0, 50),
                                visible: rect.width > 0 && rect.height > 0,
                            });
                        }
                    }

                    results.push(info);
                }
                return JSON.stringify(results, null, 2);
            }
        """)

        estrutura_json = json.loads(estrutura)
        logger.info("=" * 60)
        logger.info("ESTRUTURA DO POPUP")
        logger.info("=" * 60)
        logger.info(json.dumps(estrutura_json, indent=2, ensure_ascii=False))

        # Salva diagnostico sanitizado
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        diag_path = OUTPUT_DIR / "popup_structure.json"
        with open(diag_path, "w", encoding="utf-8") as f:
            json.dump(estrutura_json, f, indent=2, ensure_ascii=False)
        logger.info("Diagnostico salvo em: %s", diag_path)

        # Tenta fechar com cada botao visivel
        logger.info("=" * 60)
        logger.info("TENTATIVAS DE FECHAMENTO")
        logger.info("=" * 60)

        for i, btn in enumerate(estrutura_json[0]["elementos_clicaveis"]):
            if not btn["visible"] or btn["disabled"]:
                continue
            logger.info("Tentativa %d: %s | data-testid=%s | text=%s | role=%s | aria-label=%s",
                         i+1, btn["tag"], btn["data_testid"], btn["text"], btn["role"], btn["aria_label"])

            # Tenta clicar pelo seletor mais especifico
            if btn["data_testid"]:
                selector = f'[data-testid="{btn["data_testid"]}"]'
            elif btn["aria_label"]:
                selector = f'[aria-label="{btn["aria_label"]}"]'
            elif btn["text"]:
                selector = f'text="{btn["text"]}"'
            else:
                selector = f'{btn["tag"]}:nth-of-type({i+1})'

            try:
                el = wa_page.locator(selector).first
                if await el.is_visible(timeout=1000):
                    await el.click()
                    await asyncio.sleep(1)
                    count_after = await dialog.count()
                    logger.info("  Dialog apos clique: %d", count_after)
                    if count_after == 0:
                        logger.info("  ✓ POPUP FECHADO com: %s", selector)
                        break
                    else:
                        logger.info("  ✗ Dialog ainda presente")
            except Exception as e:
                logger.info("  ✗ Erro: %s", str(e)[:100])
    else:
        logger.info("Popup nao apareceu apos todas as tentativas")
        logger.info("O popup pode ja ter sido fechado permanentemente neste perfil")

    await asyncio.sleep(2)
    await context.close()
    await p.stop()
    logger.info("Fim da inspecao")


if __name__ == "__main__":
    asyncio.run(run())
