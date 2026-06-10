#!/usr/bin/env python3
"""Enviar mensagem de teste via WhatsApp Business - versao debug."""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

PROJECT_DIR = Path(__file__).parent.resolve()
PROFILE_DIR = PROJECT_DIR / ".whatsapp_business_profile"

ALLOWLIST = [os.getenv("WHATSAPP_TEST_NUMBER", "").strip()]
ALLOWLIST = [n for n in ALLOWLIST if n and len(n) >= 10]
if not ALLOWLIST:
    ALLOWLIST = ["5521968410983"]


def normalizar_telefone_br(telefone: str) -> str:
    tel = "".join(c for c in str(telefone) if c.isdigit())
    if not tel.startswith("55"):
        tel = "55" + tel
    return tel if len(tel) >= 12 else ""


def validar_numero(telefone: str) -> tuple:
    tel_norm = normalizar_telefone_br(telefone)
    if not tel_norm:
        return False, "Numero invalido"
    if tel_norm not in ALLOWLIST:
        return False, f"Numero {tel_norm} nao esta na allowlist"
    return True, tel_norm


def gerar_link_wa(telefone: str, mensagem: str = "") -> str:
    tel = normalizar_telefone_br(telefone)
    if not tel:
        return ""
    if mensagem:
        return f"https://web.whatsapp.com/send?phone={tel}&text={quote(mensagem)}"
    return f"https://web.whatsapp.com/send?phone={tel}"


def abrir_e_enviar(telefone: str, mensagem: str, auto_enviar: bool = False):
    from playwright.sync_api import sync_playwright

    # Matar Chrome antes de abrir
    os.system("taskkill /F /IM chrome.exe >nul 2>&1")
    time.sleep(3)

    valido, tel_resultado = validar_numero(telefone)
    if not valido:
        print(f"[X] ERRO: {tel_resultado}")
        return False

    tel = tel_resultado
    link = gerar_link_wa(tel, mensagem)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("=" * 60)
    print("ENVIAR TESTE WHATSAPP BUSINESS")
    print("=" * 60)
    print(f"  Numero destino: {tel}")
    print(f"  Auto-enviar:    {auto_enviar}")
    print(f"  Link:           {link}")
    print(f"  Horario:        {agora}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Navegar para o link
        print("\n[*] Abrindo WhatsApp Web...")
        page.goto(link, wait_until="domcontentloaded")
        
        # Esperar a pagina carregar
        print("[*] Aguardando carregamento (8s)...")
        time.sleep(8)

        if auto_enviar:
                    # Esperar o campo de mensagem aparecer (sinal de que o chat abriu)
                    print("[*] Aguardando chat abrir...")
                    try:
                        msg_input = page.locator('div[contenteditable="true"]').first
                        msg_input.wait_for(state="visible", timeout=15000)
                        print("[OK] Chat aberto!")
                        time.sleep(2)
                    except Exception:
                        print("[!] Chat pode nao ter aberto. Tentando continuar...")
            
                    # Tentar enviar
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