#!/usr/bin/env python3
"""
Smoke test isolado: consulta "assistência de impressoras em Barra Mansa, RJ"
Valida que as correções de timeout/robustez funcionam com o Maps real.
NÃO escreve no run estadual.
"""
import asyncio
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Garantir que o diretório do projeto está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Importar módulo principal para usar buscar_categoria com as correções
from mapear_comercios import (
    _avaliar_saude_pagina,
    _TIMEOUT_NAVEGACAO_MS,
    _TIMEOUT_SELETOR_MS,
)

LOG_DIR = Path("output/avgestao/diagnosticos")
LOG_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"smoke_test_{TIMESTAMP}.log"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def main():
    log(f"=== SMOKE TEST ISOLADO ===")
    log(f"Consulta: assistência de impressoras em Barra Mansa, RJ")
    log(f"Timeout navegação: {_TIMEOUT_NAVEGACAO_MS}ms")
    log(f"Timeout seletor: {_TIMEOUT_SELETOR_MS}ms")
    log(f"Log: {LOG_FILE}")
    log("")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        log("1. Lançando Chromium bundled...")
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        log(f"   browser.is_connected() = {browser.is_connected()}")

        # Instrumentação de eventos
        disconnected_time = None
        def on_disconnect():
            nonlocal disconnected_time
            disconnected_time = time.time()
            log("EVENTO: browser.on('disconnected')!")
        browser.on("disconnected", on_disconnect)

        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        # Timeouts como no código corrigido
        page.set_default_navigation_timeout(_TIMEOUT_NAVEGACAO_MS)
        page.set_default_timeout(_TIMEOUT_SELETOR_MS)
        log(f"   timeouts configurados: nav={_TIMEOUT_NAVEGACAO_MS}ms sel={_TIMEOUT_SELETOR_MS}ms")

        page_close_time = None
        def on_page_close():
            nonlocal page_close_time
            page_close_time = time.time()
            log("EVENTO: page.on('close')!")
        page.on("close", on_page_close)

        page_crash_time = None
        def on_page_crash():
            nonlocal page_crash_time
            page_crash_time = time.time()
            log("EVENTO: page.on('crash')!")
        page.on("crash", on_page_crash)

        log("")
        log("2. Navegando para Google Maps...")
        t0 = time.time()
        try:
            await page.goto("https://www.google.com/maps",
                           wait_until="domcontentloaded",
                           timeout=_TIMEOUT_NAVEGACAO_MS)
            dt = time.time() - t0
            log(f"   Maps carregado em {dt:.1f}s")
        except PlaywrightTimeoutError as e:
            dt = time.time() - t0
            log(f"   TIMEOUT ao carregar Maps após {dt:.1f}s: {e}")
            saude = _avaliar_saude_pagina(browser, ctx, page)
            log(f"   Saúde após timeout: {saude}")
            if saude in ("browser_morto", "context_morto"):
                log("FALHA: navegador morto após timeout no Maps inicial")
                return 1
            # Tentar commit
            try:
                await page.goto("https://www.google.com/maps",
                               wait_until="commit", timeout=30000)
                log("   Maps carregado com commit (2a tentativa)")
            except Exception as e2:
                log(f"   Falha total: {e2}")
                return 1

        await asyncio.sleep(3)

        # Aceitar cookies se necessário
        try:
            consent_btn = page.locator('button[aria-label*="Aceitar"], button[aria-label*="Accept"]')
            if await consent_btn.count() > 0:
                await consent_btn.first.click()
                log("   Cookies aceitos")
                await asyncio.sleep(1)
        except Exception:
            pass

        log("")
        log("3. Consultando: assistência de impressoras em Barra Mansa, RJ")
        query = "assistência de impressoras em Barra Mansa, RJ"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

        t0 = time.time()
        try:
            await page.goto(url, wait_until="domcontentloaded",
                           timeout=_TIMEOUT_NAVEGACAO_MS)
            dt = time.time() - t0
            log(f"   Consulta carregada em {dt:.1f}s")
        except PlaywrightTimeoutError as e:
            dt = time.time() - t0
            log(f"   TIMEOUT na consulta após {dt:.1f}s: {e}")
            saude = _avaliar_saude_pagina(browser, ctx, page)
            log(f"   Saúde após timeout: {saude}")
            if saude in ("browser_morto", "context_morto"):
                log("FALHA: navegador morto após timeout na consulta")
                return 1
            # Retry uma vez
            log("   Tentando retry com commit...")
            try:
                await page.goto(url, wait_until="commit", timeout=30000)
                log("   Retry OK")
            except Exception as e2:
                log(f"   Retry falhou: {e2}")
                saude2 = _avaliar_saude_pagina(browser, ctx, page)
                if saude2 in ("browser_morto", "context_morto"):
                    log("FALHA: navegador morto após retry")
                    return 1
                log("   Browser vivo, mas consulta falhou — continuando")

        await asyncio.sleep(3)

        # Verificar saúde
        saude = _avaliar_saude_pagina(browser, ctx, page)
        log(f"   Saúde após consulta: {saude}")
        log(f"   browser.is_connected() = {browser.is_connected()}")
        log(f"   page.is_closed() = {page.is_closed()}")
        log(f"   URL atual = {page.url[:100]}")

        if saude in ("browser_morto", "context_morto"):
            log("FALHA: navegador morto após consulta")
            return 1

        # Contar resultados
        log("")
        log("4. Contando resultados...")
        try:
            await page.wait_for_selector('div[role="feed"]', timeout=10000)
            items = page.locator('div[role="feed"] > div > div[jsaction]')
            count = await items.count()
            log(f"   {count} resultados encontrados")
        except Exception as e:
            log(f"   Não encontrou feed de resultados: {e}")
            # Verificar se é resultado único
            try:
                single = page.locator('[data-entityid]')
                sc = await single.count()
                log(f"   {sc} resultado(s) único(s)")
            except Exception:
                log("   0 resultados (página sem resultados)")

        # Verificar CAPTCHA
        current_url = page.url
        if "sorry" in current_url or "Captcha" in current_url:
            log("   ⚠️ CAPTCHA detectado na URL")
        else:
            log("   Sem CAPTCHA")

        # Scroll
        log("")
        log("5. Scrolling para carregar mais...")
        for i in range(3):
            await page.evaluate("document.querySelector('div[role=\"feed\"]')?.scrollBy(0, 1000)")
            await asyncio.sleep(1)
            log(f"   Scroll {i+1}/3")

        await asyncio.sleep(2)

        # Saúde final
        saude_final = _avaliar_saude_pagina(browser, ctx, page)
        log("")
        log("6. Verificação final:")
        log(f"   Saúde: {saude_final}")
        log(f"   browser.is_connected() = {browser.is_connected()}")
        log(f"   page.is_closed() = {page.is_closed()}")
        log(f"   disconnected_time = {disconnected_time}")
        log(f"   page_close_time = {page_close_time}")
        log(f"   page_crash_time = {page_crash_time}")

        # Cleanup
        log("")
        log("7. Fechando navegador...")
        await page.close()
        await ctx.close()
        if browser.is_connected():
            await browser.close()

        if saude_final == "page_valida":
            log("")
            log("✅ SMOKE TEST PASSOU — navegação completa, página saudável, nenhum erro")
            return 0
        else:
            log("")
            log(f"❌ SMOKE TEST FALHOU — saúde final: {saude_final}")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)