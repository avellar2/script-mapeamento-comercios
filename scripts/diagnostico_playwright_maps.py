#!/usr/bin/env python3
"""
Diagnóstico isolado do Playwright + Google Maps.
Independente do run, não escreve em fila/checkpoint/CSV.
Testa se o Chromium bundled consegue abrir e manter o Maps estável.
"""
import asyncio, sys, time, os
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("output/avgestao/diagnosticos")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"playwright_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def main():
    from playwright.async_api import async_playwright

    log("=== INÍCIO DO DIAGNÓSTICO PLAYWRIGHT + MAPS ===")
    log(f"PID: {os.getpid()}")
    log(f"Playwright importado com sucesso")

    async with async_playwright() as p:
        log("async_playwright() iniciado")

        # Coletar info do Chromium
        try:
            exe_path = p.chromium.executable_path
            log(f"chromium.executable_path: {exe_path}")
        except Exception as e:
            log(f"ERRO ao obter executable_path: {e}")

        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        log(f"chromium.launch() OK | browser.is_connected(): {browser.is_connected()}")

        # Eventos de diagnóstico
        browser.on("disconnected", lambda: log("EVENTO: browser.disconnected"))
        log("Registrado: browser.on('disconnected')")

        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        log("browser.new_context() OK")

        page = await ctx.new_page()
        log("ctx.new_page() OK")

        # Eventos da página
        page.on("close", lambda: log("EVENTO: page.close"))
        page.on("crash", lambda: log("EVENTO: page.crash"))
        log("Registrado: page.on('close') e page.on('crash')")

        # Navegar para o Maps
        log("Navegando para https://www.google.com/maps ...")
        try:
            await page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=45000)
            log("page.goto() OK - domcontentloaded")
        except Exception as e:
            log(f"Timeout no primeiro goto: {e}")
            try:
                await page.goto("https://www.google.com/maps", wait_until="commit", timeout=30000)
                log("page.goto() OK no segundo try (commit)")
            except Exception as e2:
                log(f"ERRO FATAL no page.goto: {e2}")
                await browser.close()
                log("browser.close() após erro fatal")
                return 1

        await asyncio.sleep(3)
        log("Aguardou 3s após navegação")

        # Monitoramento por 30 segundos
        log("=== INÍCIO DO MONITORAMENTO DE 30s ===")
        for i in range(6):
            await asyncio.sleep(5)
            status = (
                f"browser.is_connected(): {browser.is_connected()} | "
                f"page.is_closed(): {page.is_closed()} | "
                f"url: {page.url[:80]}"
            )
            log(f"[{i+1}/6] {status}")

            if not browser.is_connected():
                log("ERRO: browser desconectado durante monitoramento!")
                break
            if page.is_closed():
                log("ERRO: page fechada durante monitoramento!")
                break

        log("=== FIM DO MONITORAMENTO ===")

        # Fechamento normal
        log("Iniciando fechamento normal...")
        try:
            await page.close()
            log("page.close() OK")
        except Exception as e:
            log(f"page.close() exceção: {e}")

        try:
            await browser.close()
            log("browser.close() OK")
        except Exception as e:
            log(f"browser.close() exceção: {e}")

    log("async_playwright() context manager encerrado")
    log("=== DIAGNÓSTICO CONCLUÍDO - EXIT CODE 0 ===")
    return 0

if __name__ == "__main__":
    from pathlib import Path
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
