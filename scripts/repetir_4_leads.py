#!/usr/bin/env python3
"""
Repete individualmente os 4 leads inconclusivos do run sync_20260704_001948.
NÃO envia mensagens. NÃO escreve no Supabase. Apenas leitura.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from whatsapp_match import fazer_match_completo, MatchStatus
from utils.phone_utils import normalizar_telefone_br
from utils.campaign_key import PRIMEIRO_CONTATO_V1
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from supabase import create_client

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles" / "whatsapp_match"
CAMPAIGN_KEY = PRIMEIRO_CONTATO_V1

# lead_ids do run sync_20260704_001948
LEADS_INCONCLUSIVOS = [
    ("51d1a2ba-1944-45ee-93f1-d51519b2b437", "Érica Freire - Estética"),
    ("a39427c6-66a6-46f4-9444-6d4c212351ac", "Danielle Lopes Pilates"),
    ("da373706-ad67-4377-a16c-7833761fdda4", "Lift Life"),
    ("7ae99928-9fd3-4455-8ddd-b33f206f70a8", "Betapetsbr Banho e Tosa"),
]


async def main():
    print("=" * 60)
    print("  REPETIÇÃO DE 4 LEADS INCONCLUSIVOS")
    print("=" * 60)

    # Busca telefones no Supabase
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    leads = []
    for lid, nome in LEADS_INCONCLUSIVOS:
        resp = client.table("leads").select("nome,telefone,telefone_normalizado").eq("id", lid).execute()
        if resp.data:
            d = resp.data[0]
            tel = d.get("telefone_normalizado") or normalizar_telefone_br(d.get("telefone", ""))
            leads.append((lid, d["nome"], tel))
        else:
            print(f"  {nome} ({lid[:8]}) — NAO ENCONTRADO no Supabase")

    print(f"  Leads a processar: {len(leads)}")
    print()

    resultados = []

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            channel="chromium",
            args=["--no-sandbox"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        print("WhatsApp Web carregado. Verificando autenticacao...")

        # Aguarda autenticacao
        authed = False
        for attempt in range(60):
            await page.wait_for_timeout(5000)
            try:
                search = page.locator('#side input[role="textbox"]')
                count = await search.count()
                if count > 0:
                    authed = True
                    print(f"Autenticado! (tentativa {attempt+1})")
                    break
            except Exception:
                pass
            try:
                qr = page.locator('canvas, div[data-ref], div[data-testid="qrcode"]')
                qr_count = await qr.count()
                if qr_count > 0 and attempt == 0:
                    print("QR Code visivel. Escaneie agora!")
            except Exception:
                pass

        if not authed:
            print("NAO AUTENTICADO. Saindo.")
            await context.close()
            return 1

        await page.wait_for_timeout(3000)

        for i, (lid, nome, tel) in enumerate(leads, 1):
            tel_mask = f"+{tel[:2]}*****{tel[-4:]}" if tel and len(tel) > 6 else "N/A"
            print(f"\n[{i}/{len(leads)}] {nome} ({tel_mask})")

            t_start = time.time()
            result = await fazer_match_completo(
                page,
                lead_id=lid,
                phone_normalized=tel,
                campaign_key=CAMPAIGN_KEY,
            )
            t_total = time.time() - t_start

            # Verifica se havia modal
            modal_encontrado = False
            modal_fechado = False
            try:
                dialog = page.locator('[role="dialog"][aria-modal="true"]')
                dcount = await dialog.count()
                modal_encontrado = dcount > 0
            except Exception:
                pass

            # Verifica se o campo de busca foi encontrado
            campo_encontrado = result.selector_used is not None

            resultado = {
                "nome": nome,
                "tel_mask": tel_mask,
                "modal_encontrado": modal_encontrado,
                "modal_fechado": not modal_encontrado,
                "campo_encontrado": campo_encontrado,
                "chat_encontrado": result.chat_found,
                "telefone_confirmado": result.details.get("phone_found") is not None or result.status == MatchStatus.MATCHED,
                "outbound": result.outbound_found,
                "campaign_match": result.campaign_match,
                "estado": result.status.value,
                "tempo": f"{t_total:.1f}s",
                "timings": result.timings,
            }
            resultados.append(resultado)

            print(f"  Estado: {result.status.value}")
            print(f"  Chat: {result.chat_found} | Outbound: {result.outbound_found} | Match: {result.campaign_match}")
            print(f"  Tempo: {t_total:.1f}s")

            # Intervalo entre leads
            if i < len(leads):
                await page.wait_for_timeout(3000)

        await context.close()

    # Relatorio final
    print("\n" + "=" * 60)
    print("  RELATORIO FINAL")
    print("=" * 60)
    for r in resultados:
        print(f"\n  {r['nome']}")
        print(f"    Telefone: {r['tel_mask']}")
        print(f"    Modal: {'sim' if r['modal_encontrado'] else 'nao'} | Fechado: {'sim' if r['modal_fechado'] else 'nao'}")
        print(f"    Campo: {'sim' if r['campo_encontrado'] else 'nao'} | Chat: {'sim' if r['chat_encontrado'] else 'nao'}")
        print(f"    Tel confirmado: {'sim' if r['telefone_confirmado'] else 'nao'} | Outbound: {'sim' if r['outbound'] else 'nao'}")
        print(f"    Campaign match: {r['campaign_match']}")
        print(f"    Estado: {r['estado']}")
        print(f"    Tempo: {r['tempo']}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))