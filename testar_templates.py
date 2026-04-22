#!/usr/bin/env python3
"""
Teste de Templates de Email
===========================
Envia 9 emails de teste (um por categoria) para vandersonavellar1997@gmail.com
Uso: python testar_templates.py
"""

import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Zoho Mail SMTP
SMTP_HOST = "smtppro.zoho.com"
SMTP_PORT = 465
SMTP_USER = "contato@vandersonavellar.com"

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Dados ficticios por categoria
EMPRESA = "Avellar Digital"

TESTES = [
    {
        "template": "base.html",
        "nome": EMPRESA,
        "categoria": "comercio",
        "cidade": "Duque de Caxias, RJ",
        "telefone": "21999990001",
        "assunto": "Oportunidade para o seu comercio em Duque de Caxias, RJ",
    },
    {
        "template": "restaurante.html",
        "nome": EMPRESA,
        "categoria": "restaurante",
        "cidade": "Nova Iguacu, RJ",
        "telefone": "21999990002",
        "assunto": "Oportunidade para o seu restaurante em Nova Iguacu, RJ",
    },
    {
        "template": "academia.html",
        "nome": EMPRESA,
        "categoria": "academia",
        "cidade": "Belford Roxo, RJ",
        "telefone": "21999990003",
        "assunto": "Oportunidade para a sua academia em Belford Roxo, RJ",
    },
    {
        "template": "barbearia.html",
        "nome": EMPRESA,
        "categoria": "barbearia",
        "cidade": "Sao Joao de Meriti, RJ",
        "telefone": "21999990004",
        "assunto": "Oportunidade para a sua barbearia em Sao Joao de Meriti, RJ",
    },
    {
        "template": "dentista.html",
        "nome": EMPRESA,
        "categoria": "dentista",
        "cidade": "Mesquita, RJ",
        "telefone": "21999990005",
        "assunto": "Oportunidade para o seu consultorio em Mesquita, RJ",
    },
    {
        "template": "petshop.html",
        "nome": EMPRESA,
        "categoria": "pet shop",
        "cidade": "Queimados, RJ",
        "telefone": "21999990006",
        "assunto": "Oportunidade para o seu pet shop em Queimados, RJ",
    },
    {
        "template": "advogado.html",
        "nome": EMPRESA,
        "categoria": "advogado",
        "cidade": "Duque de Caxias, RJ",
        "telefone": "21999990007",
        "assunto": "Oportunidade para o seu escritorio em Duque de Caxias, RJ",
    },
    {
        "template": "salao.html",
        "nome": EMPRESA,
        "categoria": "salao de beleza",
        "cidade": "Nova Iguacu, RJ",
        "telefone": "21999990008",
        "assunto": "Oportunidade para o seu salao em Nova Iguacu, RJ",
    },
    {
        "template": "oficina.html",
        "nome": EMPRESA,
        "categoria": "oficina mecanica",
        "cidade": "Belford Roxo, RJ",
        "telefone": "21999990009",
        "assunto": "Oportunidade para a sua oficina em Belford Roxo, RJ",
    },
]


def personalizar(html, dados):
    html = html.replace("{nome}", dados["nome"])
    html = html.replace("{categoria}", dados["categoria"])
    html = html.replace("{cidade}", dados["cidade"])
    html = html.replace("{telefone}", dados["telefone"])
    return html


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    TO_EMAIL = "vandersonavellar1997@gmail.com"

    print("=" * 60)
    print("  TESTE DE TEMPLATES DE EMAIL")
    print("=" * 60)
    print(f"  De: {SMTP_USER}")
    print(f"  Para: {TO_EMAIL}")
    print(f"  Templates: {len(TESTES)}")
    print("=" * 60)

    smtp_pass = input(f"\nApp Password do Zoho ({SMTP_USER}): ").strip()
    if not smtp_pass:
        print("  [X] Senha nao informada. Saindo.")
        return

    enviados = 0
    for i, teste in enumerate(TESTES):
        template_path = TEMPLATES_DIR / teste["template"]
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            print(f"  [{i+1}] ERRO ao ler {teste['template']}: {e}")
            continue

        html = personalizar(html, teste)

        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = TO_EMAIL
        msg["Subject"] = teste["assunto"]
        msg.attach(MIMEText(f"Versao texto do email para {teste['nome']} - {teste['categoria']}", "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            server.login(SMTP_USER, smtp_pass)
            server.send_message(msg)
            server.quit()
            enviados += 1
            print(f"  [{i+1}/{len(TESTES)}] OK - {teste['template']:25s} -> {teste['nome']}")
        except Exception as e:
            print(f"  [{i+1}/{len(TESTES)}] FALHOU - {teste['template']}: {str(e)[:80]}")

        # Delay de 10s entre testes
        if i < len(TESTES) - 1:
            print(f"  ... aguardando 10s ...")
            time.sleep(10)

    print(f"\n{'=' * 60}")
    print(f"  Enviados: {enviados}/{len(TESTES)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
