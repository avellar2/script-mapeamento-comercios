#!/usr/bin/env python3
"""
dry-run-lifecycle.py — Valida ciclo de vida do navegador com 5 leads.

Objetivo exclusivo: validar que o browser é aberto uma vez e reutilizado.
NAO envia mensagens. NAO escreve no Supabase. NAO usa service role.
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from playwright.async_api import async_playwright

from utils.phone_utils import normalizar_telefone_br, variantes_busca_telefone
from whatsapp_match import fazer_match_completo, limpar_campo_busca

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lifecycle-dryrun")

PROFILE_DIR = PROJECT_ROOT / "profiles" / "whatsapp_match"
OUTPUT_DIR = PROJECT_ROOT / "output" / "avgestao" / "lifecycle"
CAMPAIGN_KEY = "primeiro_contato_v1"

# ============================================================
# MÉTRICAS DE CICLO DE VIDA
# ============================================================
metrics = {
    "launch_persistent_context_calls": 0,
    "new_page_calls": 0,
    "pages_created": [],
    "about_blank_closed": False,
    "context_close_calls": 0,
    "playwright_stop_calls": 0,
    "leads_processed": [],
}


async def run():
    p = await async_playwright().start()
    profile_path = str(PROFILE_DIR.resolve())
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. ÚNICO launch_persistent_context
    metrics["launch_persistent_context_calls"] += 1
    context = await p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )

    # 2. Procura página já aberta em web.whatsapp.com
    wa_page = None
    for pg in context.pages:
        url = getattr(pg, "url", "")
        logger.info("  Página existente: %s", url)
        if "web.whatsapp.com" in url:
            wa_page = pg
            logger.info("  → Reutilizando página existente do WhatsApp")

    if wa_page is None:
        # Cria única página do WhatsApp
        metrics["new_page_calls"] += 1
        wa_page = await context.new_page()
        metrics["pages_created"].append({
            "id": id(wa_page),
            "url": "about:blank (antes da navegação)",
        })
        await wa_page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        logger.info("  Nova página do WhatsApp aberta")

    # 3. Fecha about:blank
    for pg in list(context.pages):
        if pg is not wa_page and getattr(pg, "url", "") == "about:blank":
            try:
                await pg.close()
                metrics["about_blank_closed"] = True
                logger.info("  Página about:blank fechada")
            except Exception:
                pass

    # Registra ID da page para rastrear reuso
    page_id = id(wa_page)
    logger.info("Page ID do WhatsApp: %d", page_id)

    # 4. Aguarda login
    try:
        await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        logger.info("WhatsApp Web carregado com sessão ativa")
    except Exception:
        logger.info("Aguardando QR code...")
        try:
            await wa_page.wait_for_selector('div[data-testid="chat-list"]', timeout=240000)
            logger.info("WhatsApp Web carregado")
        except Exception:
            logger.error("Timeout ao aguardar login do WhatsApp")
            await context.close()
            metrics["context_close_calls"] += 1
            await p.stop()
            metrics["playwright_stop_calls"] += 1
            return

    # Verifica estado das páginas após login
    pages_before = len(context.pages)
    logger.info("Páginas após login: %d", pages_before)

    # 5. Carrega 5 leads do Supabase
    from supabase import create_client
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    result = (
        client.table("leads")
        .select("id,nome,telefone,whatsapp,telefone_normalizado,cidade,bairro,categoria,nicho,produto,grupo,status")
        .in_("status", ["novo", "pronto_para_enviar"])
        .limit(5)
        .order("created_at")
        .execute()
    )
    leads = result.data if result.data else []
    logger.info("Leads carregados: %d", len(leads))

    if not leads:
        logger.error("Nenhum lead encontrado")
        await context.close()
        metrics["context_close_calls"] += 1
        await p.stop()
        metrics["playwright_stop_calls"] += 1
        return

    # 6. Processa cada lead com a mesma page
    diagnostic_dir = str(OUTPUT_DIR / f"lifecycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}" / "diagnosticos")

    for i, lead in enumerate(leads):
        lead_id = lead.get("id", "")
        nome = lead.get("nome", "sem nome")
        tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""
        phone_normalized = normalizar_telefone_br(tel)

        if not phone_normalized:
            logger.warning("[%d/%d] %s — telefone inválido, pulando", i+1, len(leads), nome)
            continue

        tel_mask = phone_normalized[:4] + "****" + phone_normalized[-4:]
        logger.info("=" * 50)
        logger.info("[%d/%d] %s (%s)", i+1, len(leads), nome, tel_mask)

        # Registra page_id ANTES do match
        current_page_id = id(wa_page)
        current_pages_count = len(context.pages)

        start = time.time()
        result = await fazer_match_completo(
            wa_page,
            lead_id=lead_id,
            phone_normalized=phone_normalized,
            campaign_key=CAMPAIGN_KEY,
            diagnostic_dir=diagnostic_dir,
        )
        elapsed = time.time() - start

        # Registra page_id DEPOIS do match
        after_page_id = id(wa_page)
        after_pages_count = len(context.pages)

        lead_metric = {
            "index": i + 1,
            "nome": nome,
            "telefone_mascarado": tel_mask,
            "page_id_antes": current_page_id,
            "page_id_depois": after_page_id,
            "mesma_page": current_page_id == after_page_id,
            "pages_count_antes": current_pages_count,
            "pages_count_depois": after_pages_count,
            "status": result.status.value,
            "chat_found": result.chat_found,
            "outbound_found": result.outbound_found,
            "campaign_match": result.campaign_match,
            "tempo_seg": round(elapsed, 2),
        }
        metrics["leads_processed"].append(lead_metric)

        logger.info("  Status: %s | Chat: %s | Saída: %s | Match: %s | Tempo: %.2fs",
                     result.status.value,
                     "sim" if result.chat_found else "nao",
                     "sim" if result.outbound_found else "nao",
                     "sim" if result.campaign_match else "nao" if result.campaign_match is False else "n/a",
                     elapsed)
        logger.info("  page_id: %d → %d | pages: %d → %d | mesma_page: %s",
                     current_page_id, after_page_id,
                     current_pages_count, after_pages_count,
                     current_page_id == after_page_id)

        # 7. Limpa campo de busca entre leads
        try:
            await limpar_campo_busca(wa_page)
            logger.info("  Campo de busca limpo entre leads ✓")
        except Exception as e:
            logger.warning("  Erro ao limpar campo: %s", e)

        # Intervalo
        await asyncio.sleep(3)

    # 8. Verifica estado final
    final_pages = len(context.pages)
    logger.info("=" * 50)
    logger.info("ESTADO FINAL DO NAVEGADOR")
    logger.info("Páginas abertas: %d", final_pages)
    for pg in context.pages:
        logger.info("  - %s (id=%d)", getattr(pg, "url", "?"), id(pg))

    # 9. Fecha context e playwright (somente no final)
    logger.info("Fechando context e playwright...")
    await context.close()
    metrics["context_close_calls"] += 1
    await p.stop()
    metrics["playwright_stop_calls"] += 1

    # 10. Relatório final
    logger.info("=" * 60)
    logger.info("RELATÓRIO DE CICLO DE VIDA")
    logger.info("=" * 60)
    logger.info("launch_persistent_context_calls: %d", metrics["launch_persistent_context_calls"])
    logger.info("new_page_calls: %d", metrics["new_page_calls"])
    logger.info("about_blank_closed: %s", metrics["about_blank_closed"])
    logger.info("context_close_calls: %d", metrics["context_close_calls"])
    logger.info("playwright_stop_calls: %d", metrics["playwright_stop_calls"])
    logger.info("leads processados: %d", len(metrics["leads_processed"]))
    logger.info("")

    all_same_page = all(lm["mesma_page"] for lm in metrics["leads_processed"])
    logger.info("mesma_page em TODOS os leads: %s", "✓ SIM" if all_same_page else "✗ NÃO")

    page_ids = set(lm["page_id_antes"] for lm in metrics["leads_processed"])
    logger.info("page_ids distintos: %s", page_ids)
    logger.info("")

    for lm in metrics["leads_processed"]:
        logger.info("  [%d] %s | page_id=%d | mesma=%s | status=%s | %.2fs",
                     lm["index"], lm["telefone_mascarado"],
                     lm["page_id_antes"], lm["mesma_page"],
                     lm["status"], lm["tempo_seg"])

    # Salva JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / f"lifecycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Relatório salvo em: %s", report_path)

    # Verificação final de processos Chrome
    logger.info("=" * 60)
    logger.info("FIM DO DRY-RUN DE CICLO DE VIDA")


if __name__ == "__main__":
    asyncio.run(run())