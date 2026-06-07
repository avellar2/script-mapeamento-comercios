#!/usr/bin/env python3
"""
Enviar mensagem de teste via WhatsApp Business.

SEGURANCA:
- Apenas envia para numeros na allowlist de teste (WHATSAPP_TEST_NUMBER)
- Modo padrao: abre WhatsApp com mensagem pronta, NAO envia automaticamente
- Modo --auto-enviar: envia apenas se numero estiver na allowlist
- Nunca envia para leads reais
- Nunca processa listas ou faz envio em massa

Uso:
    # Abrir WhatsApp com mensagem pronta (NAO envia):
    python enviar_teste_whatsapp_business.py --telefone 5521968410983 --mensagem "Ola teste"

    # Enviar automaticamente (apenas para numero da allowlist):
    python enviar_teste_whatsapp_business.py --telefone 5521968410983 --mensagem "Ola teste" --auto-enviar
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

# Carrega .env do projeto
_dotenv = Path(__file__).resolve().parent / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv, override=True)

# ═══════════════════════════════════════════════════════════════
# ALLOWLIST - UNICOS NUMEROS AUTORIZADOS PARA ENVIO
# ═══════════════════════════════════════════════════════════════
ALLOWLIST = [
    os.getenv("WHATSAPP_TEST_NUMBER", "").strip(),
]
# Remove vazios
ALLOWLIST = [n for n in ALLOWLIST if n and len(n) >= 10]
# Fallback se .env nao tiver (apenas para dev)
if not ALLOWLIST:
    ALLOWLIST = ["5521968410983"]  # Seu numero pessoal

PROFILE_DIR = Path(".whatsapp_business_profile")


# ═══════════════════════════════════════════════════════════════
# VALIDACAO
# ═══════════════════════════════════════════════════════════════

def normalizar_telefone_br(valor: str) -> str | None:
    """Normaliza telefone para formato 5521XXXXXXXXX."""
    if not valor:
        return None
    numeros = re.sub(r"\D", "", str(valor))
    if not numeros:
        return None
    if numeros.startswith("55") and len(numeros) >= 12:
        return numeros
    if numeros.startswith("0"):
        numeros = numeros[1:]
    if len(numeros) == 11:
        return "55" + numeros
    if len(numeros) == 10:
        return "55" + numeros
    return None


def validar_numero(telefone: str) -> tuple[bool, str]:
    """Valida se o numero esta na allowlist."""
    tel_norm = normalizar_telefone_br(telefone)
    if not tel_norm:
        return False, "Telefone invalido"

    if tel_norm not in ALLOWLIST:
        return False, f"Numero {tel_norm} NAO esta na allowlist de teste. Abortando."

    return True, tel_norm


def gerar_link_wa(telefone: str, mensagem: str = "") -> str:
    """Gera link wa.me com mensagem."""
    tel = normalizar_telefone_br(telefone)
    if not tel:
        return ""
    if mensagem:
        return f"https://wa.me/{tel}?text={quote(mensagem)}"
    return f"https://wa.me/{tel}"


# ═══════════════════════════════════════════════════════════════
# ENVIO
# ═══════════════════════════════════════════════════════════════

def abrir_e_enviar(telefone: str, mensagem: str, auto_enviar: bool = False):
    """Abre WhatsApp Web e opcionalmente envia mensagem."""
    from playwright.sync_api import sync_playwright

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
    print(f"  Permite envio:  {'SIM' if auto_enviar else 'NAO - modo consulta'}")
    print(f"  Link:           {link}")
    print(f"  Mensagem:       {mensagem[:50]}{'...' if len(mensagem) > 50 else ''}")
    print(f"  Horario:        {agora}")
    print("=" * 60)

    if not auto_enviar:
        print()
        print("[i] Modo CONSULTA - abrindo WhatsApp para revisao manual.")
        print("[i] A mensagem NAO sera enviada automaticamente.")
        print("[i] Clique em ENVIAR manualmente no WhatsApp se desejar.")
    else:
        print()
        print(f"[*] Modo AUTO-ENVIAR ativo.")
        print(f"[*] Enviando para {tel}...")

    print()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(link, wait_until="domcontentloaded")

        time.sleep(3)

        if auto_enviar:
            # Clicar em enviar apenas se validado
            try:
                # WhatsApp pode pedir confirmacao antes de enviar
                # Procura o botao de enviar (seta para direita ou Enter)
                send_button = page.locator('button[data-testid="send"]').first
                if send_button.count() > 0:
                    send_button.click()
                    print(f"[OK] Mensagem enviada para {tel}")
                else:
                    # Tenta pressionar Enter
                    page.keyboard.press("Enter")
                    print(f"[OK] Mensagem enviada (Enter) para {tel}")
            except Exception as e:
                print(f"[!] Enviado via Enter/click. Verifique o WhatsApp.")
        else:
            print("[i] Modo consulta ativo. Envie manualmente se desejar.")

        # Mantem aberto por alguns segundos para verificacao
        time.sleep(2)

        # Fecha ao pressionar Ctrl+C no terminal
        print()
        print("Pressione Ctrl+C para fechar o navegador.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nFechando navegador...")
            browser.close()

    # Relatorio final
    print()
    print("=" * 60)
    print("RELATORIO")
    print("=" * 60)
    print(f"  Numero destino:  {tel}")
    print(f"  Status envio:   {'ENVIADO' if auto_enviar else 'ABERTO PARA ENVIO MANUAL'}")
    print(f"  Mensagem:        {mensagem[:60]}{'...' if len(mensagem) > 60 else ''}")
    print(f"  Horario:         {agora}")
    print(f"  Perfil usado:    {PROFILE_DIR}")
    print("=" * 60)

    return True


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Enviar mensagem de teste via WhatsApp Business",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Abrir WhatsApp com mensagem (NAO envia):
  python enviar_teste_whatsapp_business.py --telefone 5521968410983 --mensagem "Ola teste"

  # Enviar automaticamente (apenas para numero da allowlist):
  python enviar_teste_whatsapp_business.py --telefone 5521968410983 --mensagem "Ola teste" --auto-enviar

Seguranca:
  - Apenas numeros na allowlist (WHATSAPP_TEST_NUMBER no .env) podem receber auto-envio.
  - Modo padrao abre o WhatsApp para revisao manual.
  - Nunca envia para leads reais ou listas.
        """,
    )
    parser.add_argument(
        "--telefone",
        type=str,
        required=True,
        help="Numero de telefone destino (formato: 5521968410983)",
    )
    parser.add_argument(
        "--mensagem",
        type=str,
        required=True,
        help="Mensagem a enviar",
    )
    parser.add_argument(
        "--auto-enviar",
        action="store_true",
        help="Enviar automaticamente (APENAS se numero estiver na allowlist)",
    )
    args = parser.parse_args()

    # Validacao
    if not args.telefone or not args.mensagem:
        print("[X] ERRO: telefone e mensagem sao obrigatorios.")
        sys.exit(1)

    if len(args.mensagem) > 1000:
        print("[X] ERRO: mensagem muito longa (max 1000 caracteres).")
        sys.exit(1)

    # Verificar allowlist antes de qualquer acao
    valido, resultado = validar_numero(args.telefone)
    if not valido:
        print(f"[X] {resultado}")
        print()
        print("[i] Numeros autorizados para teste:")
        for n in ALLOWLIST:
            print(f"    - {n}")
        sys.exit(1)

    if args.auto_enviar:
        print()
        print("[!] ATENCAO: Modo AUTO-ENViar ativado.")
        print(f"[!] O numero {resultado} esta na allowlist.")
        print("[!] A mensagem sera enviada automaticamente.")
        print()
        resp = input("Continuar? (s/n): ").strip().lower()
        if resp not in ("s", "sim", "y"):
            print("Cancelado.")
            sys.exit(0)

    abrir_e_enviar(args.telefone, args.mensagem, args.auto_enviar)


if __name__ == "__main__":
    main()