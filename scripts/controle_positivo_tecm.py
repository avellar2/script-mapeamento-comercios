#!/usr/bin/env python3
"""
Abre WhatsApp Web, aguarda autenticação, executa controle positivo TECM.
NÃO envia mensagens. Apenas leitura.
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from whatsapp_match import fazer_match_completo, MatchStatus
from utils.phone_utils import normalizar_telefone_br
from utils.campaign_key import PRIMEIRO_CONTATO_V1

PHONE = "21989299770"
PHONE_CANONICO = normalizar_telefone_br(PHONE)
CAMPAIGN_KEY = PRIMEIRO_CONTATO_V1
PROFILE_DIR = Path("profiles/whatsapp_match").resolve()


async def main():
    print("=" * 60)
    print("  CONTROLE POSITIVO — TECM TECNOLOGIA")
    print("=" * 60)
    print(f"  Telefone: +{PHONE_CANONICO[:2]}*****{PHONE_CANONICO[-4:]}")
    print(f"  Campaign: {CAMPAIGN_KEY}")
    print()

    t_total = time.time()

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

        # Verifica se já está autenticado (campo de busca visível)
        # ou se precisa de QR code
        authed = False
        for attempt in range(60):  # 60 x 5s = 5 min
            await page.wait_for_timeout(5000)
            # Tenta detectar campo de busca (autenticado)
            try:
                search = page.locator('#side input[role="textbox"]')
                count = await search.count()
                if count > 0:
                    authed = True
                    print(f"Autenticado! (tentativa {attempt+1})")
                    break
            except Exception:
                pass

            # Tenta detectar QR code
            try:
                qr = page.locator('canvas, div[data-ref], div[data-testid="qrcode"]')
                qr_count = await qr.count()
                if qr_count > 0 and attempt == 0:
                    print("QR Code visivel. Escaneie agora!")
            except Exception:
                pass

        if not authed:
            print("NAO AUTENTICADO apos 5 minutos. Saindo.")
            await context.close()
            return 1

        # Aguarda 3s para estabilizar
        await page.wait_for_timeout(3000)

        # Executa o match
        print("Executando match...")
        result = await fazer_match_completo(
            page,
            lead_id="tecm_controle_positivo",
            phone_normalized=PHONE_CANONICO,
            campaign_key=CAMPAIGN_KEY,
        )

        await context.close()

    t_total = time.time() - t_total

    print()
    print("=" * 60)
    print("  RESULTADO")
    print("=" * 60)
    print(f"  Status:           {result.status.value}")
    print(f"  Chat encontrado:  {result.chat_found}")
    print(f"  Outbound:         {result.outbound_found}")
    print(f"  Campaign match:   {result.campaign_match}")
    print(f"  Fingerprint:      {result.message_fingerprint[:16] if result.message_fingerprint else 'N/A'}...")
    print(f"  Timestamp:        {result.message_timestamp or 'N/A'}")
    print(f"  Erro:             {result.error_message or 'Nenhum'}")
    print()
    print("  TEMPOS:")
    for etapa, t in sorted(result.timings.items()):
        print(f"    {etapa:20s}: {t:.2f}s")
    print(f"    {'TOTAL':20s}: {t_total:.2f}s")
    print()

    if result.status == MatchStatus.MATCHED:
        print("  ✅ CONTROLE POSITIVO: MATCHED")
    elif result.status == MatchStatus.AMBIGUOUS:
        print("  ⚠️  AMBIGUOUS (outbound encontrado, campanha nao corresponde)")
    elif result.status == MatchStatus.NO_OUTBOUND:
        print("  ❌ NO_OUTBOUND")
    else:
        print(f"  ❌ Status inesperado: {result.status.value}")

    return 0 if result.status in (MatchStatus.MATCHED, MatchStatus.AMBIGUOUS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))