#!/usr/bin/env python3
"""
Reprocessa os 11 leads que terminaram como modal_blocked no run sync_20260704_115332.
NAO envia mensagens. NAO escreve no Supabase. NAO altera checkpoint.
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
logger = logging.getLogger("retest-11-blocked")

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "avgestao" / "retest-11-blocked"
CAMPAIGN_KEY = "avgestao:assistencias:primeiro_contato:v1"

# 11 leads modal_blocked do run sync_20260704_115332
LEADS = [
    ("ae54047e-a463-4452-8c3a-3f1fb59edbef", "Barbearia pai e filho", "5521****0852"),
    ("0f3a0af6-d912-4101-ad41-0f82f8d7134f", "Uni-Duni-Tê", "5521****2333"),
    ("62702419-9ec9-4c5b-b3ae-b41ae955ef65", "Spa Novo Visual", "5521****9229"),
    ("110f358e-ad3a-4f19-9b2a-4280ef26f089", "Ragu's Lanches e Petiscos", "5521****4678"),
    ("f3ebac15-fa9e-4ec4-a3c4-1b88bacbfc53", "Ravís Sucos & Lanches", "5521****3777"),
    ("e3f5f78f-e6a4-406e-87b4-b86affd835cf", "Isaque Autocenter", "5521****1932"),
    ("b7d9d1b5-3a10-4a7a-8534-6fdf086f913a", "Point das Pizzas", "5521****4540"),
    ("685b3cc3-51fe-4032-95c2-0b44c7dcb2d4", "Neiva Bastos - Loiros Platinados", "5521****7730"),
    ("b2416ee3-0b48-4e40-9740-7eb346507c1a", "Salão Dellas", "5521****4350"),
    ("8126decb-2530-440e-b9d2-f10941c4376c", "Ben's açaí Engenheiro Pedreira", "5521****3464"),
    ("7c56abea-abbc-43d0-86ca-bf23e2a36fb3", "Xodó Auto Mecânica Geral", "5521****8682"),
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
    resultados = []

    for i, (lead_id, nome, tel_mask) in enumerate(LEADS):
        # Busca telefone real no Supabase
        from supabase import create_client
        client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        r = client.table("leads").select("id,nome,whatsapp,telefone").eq("id", lead_id).execute()
        if not r.data:
            logger.warning("[%d/%d] %s — lead nao encontrado no Supabase", i+1, len(LEADS), nome)
            continue
        lead = r.data[0]
        tel_raw = lead.get("whatsapp") or lead.get("telefone") or ""
        phone_normalized = normalizar_telefone_br(tel_raw)
        if not phone_normalized:
            logger.warning("[%d/%d] %s — telefone invalido", i+1, len(LEADS), nome)
            continue
        tel_masked = phone_normalized[:4] + "****" + phone_normalized[-4:]

        logger.info("=" * 50)
        logger.info("[%d/%d] %s (%s)", i+1, len(LEADS), nome, tel_masked)
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

        logger.info("  Status: %s", result.status.value)
        logger.info("  Chat: %s | Outbound: %s | Match: %s",
                     "sim" if result.chat_found else "nao",
                     "sim" if result.outbound_found else "nao",
                     "sim" if result.campaign_match else "nao" if result.campaign_match is False else "n/a")
        logger.info("  Tempo: %.2fs | Detalhes: %s", elapsed, result.details)

        resultados.append({
            "lead_id": lead_id,
            "nome": nome,
            "telefone_mascarado": tel_masked,
            "status": result.status.value,
            "chat_found": result.chat_found,
            "outbound_found": result.outbound_found,
            "campaign_match": result.campaign_match,
            "tempo_seg": round(elapsed, 2),
        })

        await limpar_campo_busca(wa_page)
        await asyncio.sleep(3)

    await context.close()
    await p.stop()

    # Relatorio
    logger.info("=" * 60)
    logger.info("RELATORIO FINAL - 11 LEADS MODAL_BLOCKED")
    logger.info("=" * 60)
    for r in resultados:
        logger.info("  %s | %s | status=%s | chat=%s | outbound=%s | match=%s | %.2fs",
                     r["telefone_mascarado"], r["nome"][:30],
                     r["status"],
                     "sim" if r["chat_found"] else "nao",
                     "sim" if r["outbound_found"] else "nao",
                     r["campaign_match"],
                     r["tempo_seg"])

    resolvidos = sum(1 for r in resultados if r["status"] != "modal_blocked")
    ainda_blocked = sum(1 for r in resultados if r["status"] == "modal_blocked")
    logger.info("")
    logger.info("Resolvidos: %d/%d", resolvidos, len(resultados))
    logger.info("Ainda modal_blocked: %d/%d", ainda_blocked, len(resultados))
    logger.info("Zero escrita: ✅ | Zero envio: ✅")


if __name__ == "__main__":
    asyncio.run(run())
