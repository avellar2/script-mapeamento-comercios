#!/usr/bin/env python3
"""
Envia 1 email teste para o Vanderson e salva no Supabase
"""
import os
import sys
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

SMTP_HOST = "smtppro.zoho.com"
SMTP_PORT = 465
SMTP_USER = "contato@vandersonavellar.com"
SMTP_PASS = os.getenv("ZOHO_SMTP_APP_PASSWORD", "")

TO_EMAIL = "vandersonavellar1997@gmail.com"

# Dados do teste
NOME = "Avellar Digital"
CATEGORIA = "restaurante"
CIDADE = "Duque de Caxias, RJ"
TEMPLATE = "restaurante.html"

def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("  TESTE: Enviar 1 email + salvar no Supabase")
    print("=" * 60)

    if not SMTP_PASS:
        print("  [X] Senha do Zoho nao encontrada no .env")
        return

    # Carregar template
    template_path = Path(__file__).parent / "templates" / TEMPLATE
    html = template_path.read_text(encoding="utf-8")

    # Gerar tracking ID
    tracking_id = str(uuid.uuid4())
    print(f"  Tracking ID: {tracking_id}")

    # Personalizar
    html = html.replace("{nome}", NOME)
    html = html.replace("{categoria}", CATEGORIA)
    html = html.replace("{cidade}", CIDADE)
    html = html.replace("{telefone}", "21968410983")
    html = html.replace("{TRACKING_ID}", tracking_id)

    # Criar email
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"Oportunidade para o seu restaurante em {CIDADE}"
    msg.attach(MIMEText(f"Teste de email para {NOME}", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    # Enviar
    print(f"\n  Enviando para: {TO_EMAIL}")
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("  [OK] Email enviado!")
    except Exception as e:
        print(f"  [X] Erro ao enviar: {e}")
        return

    # Salvar no Supabase
    if HAS_SUPABASE:
        try:
            url = os.getenv("SUPABASE_URL", "https://ivqaccppqcchqshaplao.supabase.co")
            key = os.getenv("SUPABASE_ANON_KEY", "")
            sb = create_client(url, key)
            sb.table("emails_enviados").insert({
                "nome": NOME,
                "email": TO_EMAIL,
                "categoria": CATEGORIA,
                "cidade": CIDADE,
                "telefone": "21968410983",
                "tipo_email": "comercial",
                "template": TEMPLATE,
                "data_envio": datetime.now().isoformat(),
                "email_aberto": False,
                "qtd_aberturas": 0,
                "tracking_id": tracking_id,
            }).execute()
            print("  [OK] Salvo no Supabase!")
        except Exception as e:
            print(f"  [X] Erro Supabase: {e}")
    else:
        print("  [!] Supabase client nao instalado")

    print(f"\n{'=' * 60}")
    print(f"  Agora abre o email e clica em 'Exibir imagens'")
    print(f"  Depois verifica o dashboard!")
    print(f"  Tracking URL: https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id={tracking_id}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
