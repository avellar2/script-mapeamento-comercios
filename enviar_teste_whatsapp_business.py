#!/usr/bin/env python3
"""Enviar mensagem de teste via WhatsApp Business - versao debug."""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from config.lock_whatsapp_sender import LockWhatsAppSender
from sender_int import (
    normalizar_telefone_lead,
    obter_campaign_key,
    reserve_lead,
    settle_lead,
)
from utils.phone_utils import normalizar_telefone_br

PROJECT_DIR = Path(__file__).parent.resolve()
PROFILE_DIR = PROJECT_DIR / ".whatsapp_business_profile"

ALLOWLIST = [os.getenv("WHATSAPP_TEST_NUMBER", "").strip()]
ALLOWLIST = [n for n in ALLOWLIST if n and len(n) >= 10]
if not ALLOWLIST:
    ALLOWLIST = ["5521968410983"]


def validar_numero(telefone: str) -> tuple:
    tel_norm = normalizar_telefone_br(telefone)
    if not tel_norm:
        return False, "Numero invalido"
    if tel_norm not in ALLOWLIST:
        return False, f"Numero {tel_norm} nao esta na allowlist"
    return True, tel_norm


def abrir_e_enviar(telefone: str, mensagem: str, auto_enviar: bool = False):
    from playwright.sync_api import sync_playwright

    valido, tel_resultado = validar_numero(telefone)
    if not valido:
        print(f"[X] ERRO: {tel_resultado}")
        return False

    tel = tel_resultado
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("=" * 60)
    print("ENVIAR TESTE WHATSAPP BUSINESS")
    print("=" * 60)
    print(f"  Numero destino: {tel}")
    print(f"  Auto-enviar:    {auto_enviar}")
    print(f"  Horario:        {agora}")
    print("=" * 60)

    # Adquire lock global do perfil dos senders
    with LockWhatsAppSender() as lock:
        if not lock.acquired:
            print("ERRO: Já existe um sender ativo usando o perfil WhatsApp.")
            return False

        # Remove locks do Chromium
        for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            p = PROFILE_DIR / lock_file
            if p.exists(): p.unlink()

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                args=["--no-sandbox"],
                viewport={"width": 1280, "height": 800},
            )
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Reserva atômica (apenas se auto_enviar)
            reservation_id = None
            reservation_token = None
            if auto_enviar:
                campaign_key = obter_campaign_key({"produto": "avgestao", "grupo": "assistencias"})
                reserve = reserve_lead(tel, campaign_key, "teste", "sender:test")
                if reserve and reserve.get("outcome") == "reserved":
                    reservation_id = reserve.get("reservation_id")
                    reservation_token = reserve.get("reservation_token")
                    print(f"[OK] Reserva: {reserve.get('outcome')}")
                else:
                    print(f"[!] Reserva: {reserve.get('outcome', 'erro')}")

            # Navegar para o link
            print("\n[*] Abrindo WhatsApp Web...")
            link = f"https://web.whatsapp.com/send?phone={tel}&text={quote(mensagem)}"
            page.goto(link, wait_until="domcontentloaded")

            print("[*] Aguardando carregamento (8s)...")
            time.sleep(8)

            if auto_enviar:
                print("[*] Aguardando chat abrir...")
                try:
                    msg_input = page.locator('div[contenteditable="true"]').first
                    msg_input.wait_for(state="visible", timeout=15000)
                    print("[OK] Chat aberto!")
                    time.sleep(2)
                except Exception:
                    print("[!] Chat pode nao ter aberto.")
                    if reservation_id:
                        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="chat_nao_abriu")
                    browser.close()
                    return False

                try:
                    send_btn = page.locator('button[aria-label="Enviar"]').first
                    if send_btn.count() > 0:
                        send_btn.click()
                        time.sleep(2)
                        print(f"[OK] Mensagem enviada para {tel}")
                    else:
                        page.keyboard.press("Enter")
                        time.sleep(2)
                        print(f"[OK] Mensagem enviada (Enter) para {tel}")
                except Exception:
                    print("[!] Enviado. Verifique o WhatsApp.")

                time.sleep(4)
                if reservation_id:
                    settle = settle_lead(
                        reservation_id, reservation_token, "sent",
                        message_timestamp=datetime.now().isoformat(),
                        obs="teste_whatsapp_business",
                    )
                    if settle and settle.get("outcome") == "settled":
                        print("[OK] Confirmado no Supabase")
                    else:
                        print(f"[!] Falha ao finalizar: {settle}")
            else:
                print("[i] Modo consulta. Envie manualmente.")
                print("[i] Fechando em 30s automaticamente...")
                time.sleep(30)

            browser.close()

    print("\n" + "=" * 60)
    print("RELATORIO")
    print("=" * 60)
    print(f"  Numero:  {tel}")
    print(f"  Status:  {'ENVIADO' if auto_enviar else 'CONSULTA'}")
    print(f"  Hora:    {agora}")
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(description="Enviar teste WhatsApp Business")
    parser.add_argument("--telefone", type=str, required=True)
    parser.add_argument("--mensagem", type=str, required=True)
    parser.add_argument("--auto-enviar", action="store_true")
    args = parser.parse_args()
    abrir_e_enviar(args.telefone, args.mensagem, args.auto_enviar)


if __name__ == "__main__":
    main()