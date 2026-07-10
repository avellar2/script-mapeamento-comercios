#!/usr/bin/env python3
"""
Validação real do matcher otimizado — controle positivo TECM TECNOLOGIA.
NÃO envia mensagens. Apenas leitura do WhatsApp Web.
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
PROFILE_DIR = Path("profiles/whatsapp_match")


async def main():
    print("=" * 60)
    print("  VALIDAÇÃO REAL — TECM TECNOLOGIA")
    print("=" * 60)
    print(f"  Telefone: +{PHONE_CANONICO[:2]}*****{PHONE_CANONICO[-4:]}")
    print(f"  Campaign: {CAMPAIGN_KEY}")
    print()

    t_total = time.time()

    async with async_playwright() as p:
        # Usa o perfil persistente do WhatsApp
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR.resolve()),
            headless=False,
            channel="chromium",
            args=["--no-sandbox"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # Navega para o WhatsApp Web
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
        print("Aguardando WhatsApp Web carregar...")
        await page.wait_for_timeout(3000)

        # Executa o match
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

    # Validação
    if result.status == MatchStatus.MATCHED:
        print("  ✅ CONTROLE POSITIVO: MATCHED (outbound detectado, campanha confirmada)")
    elif result.status == MatchStatus.AMBIGUOUS:
        print("  ⚠️  AMBIGUOUS (outbound encontrado mas não corresponde à campanha)")
    elif result.status == MatchStatus.NO_OUTBOUND:
        print("  ❌ NO_OUTBOUND (conversa existe mas sem mensagem de saída)")
    else:
        print(f"  ❌ Status inesperado: {result.status.value}")

    return 0 if result.status in (MatchStatus.MATCHED, MatchStatus.AMBIGUOUS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))