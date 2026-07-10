#!/usr/bin/env python3
"""
Testa os 2 leads que terminaram como modal_blocked no run anterior.
NAO envia mensagens. NAO escreve no Supabase.
"""
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retest-blocked")

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "avgestao" / "retest-blocked"
CAMPAIGN_KEY = "avgestao:assistencias:primeiro_contato:v1"

LEADS = [
    ("6d6845b5-51c5-43ba-a1ab-7b7f3db76e67", "PET SHOP PIAM BANHO E TOSA", "21) 98022-9235"),
    ("7fbcce50-acb2-4ef0-a194-643056060d72", "Pet Luxo", "21) 99474-5106"),
]


async def run():
    from playwright.async_api import async_playwright
    from utils.phone_utils import normalizar_telefone_br
    from whatsapp_match import fazer_match_completo, limpar_campo_busca

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

    diagnostic_dir = str(OUTPUT_DIR / "diagnosticos")

    for i, (lead_id, nome, tel_raw) in enumerate(LEADS):
        phone_normalized = normalizar_telefone_br(tel_raw)
        tel_mask = phone_normalized[:4] + "****" + phone_normalized[-4:] if phone_normalized else "***"

        logger.info("=" * 50)
        logger.info("[%d/2] %s (%s)", i+1, nome, tel_mask)
        logger.info("=" * 50)

        start = time.time()
        result = await fazer_match_completo(
            wa_page,
            lead_id=lead_id,
            phone_normalized=phone_normalized,
            campaign_key=CAMPAIGN_KEY,
            diagnostic_dir=diagnostic_dir,
        )
        elapsed = time.time() - start

        logger.info("Status: %s", result.status.value)
        logger.info("Chat encontrado: %s", "sim" if result.chat_found else "nao")
        logger.info("Outbound: %s", "sim" if result.outbound_found else "nao")
        logger.info("Campaign match: %s", result.campaign_match)
        logger.info("Tempo: %.2fs", elapsed)
        logger.info("Detalhes: %s", result.details)

        # Limpa campo entre leads
        await limpar_campo_busca(wa_page)
        await asyncio.sleep(3)

    await context.close()
    await p.stop()
    logger.info("Fim do reteste")


if __name__ == "__main__":
    asyncio.run(run())
