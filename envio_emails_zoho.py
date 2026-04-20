#!/usr/bin/env python3
"""
Envio Automatico de Emails via Zoho Mail
========================================
Envia emails personalizados por categoria usando SMTP do Zoho Mail.
Cada categoria tem template proprio com dor e upsell especificos.

Uso: python envio_emails_zoho.py
"""

import csv
import json
import smtplib
import random
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# Diretorios
OUTPUT_DIR = Path(__file__).parent / "output"
TEMPLATES_DIR = Path(__file__).parent / "templates"
PROGRESS_FILE = OUTPUT_DIR / "progresso_envio.json"
LEADS_FILE = OUTPUT_DIR / "todos_comercios.csv"
EMAILS_FILE = OUTPUT_DIR / "progresso_emails.json"

# Zoho Mail SMTP
SMTP_HOST = "smtppro.zoho.com"
SMTP_PORT = 465
SMTP_USER = "contato@vandersonavellar.com"

# Limites
DELAY_MIN = 120   # 2 minutos
DELAY_MAX = 300    # 5 minutos
LIMITE_DIA = 50   # emails por dia

# Mapeamento de categoria -> template
# Chave = categoria normalizada (lowercase, sem acento)
CATEGORIA_TEMPLATE = {
    "restaurante": "restaurante.html",
    "pizzaria": "restaurante.html",
    "lanchonete": "restaurante.html",
    "confeitaria": "restaurante.html",
    "churrascaria": "restaurante.html",
    "bar": "restaurante.html",
    "academia": "academia.html",
    "estudio de pilates": "academia.html",
    "barbearia": "barbearia.html",
    "salao de beleza": "salao.html",
    "estetica": "salao.html",
    "dentista": "dentista.html",
    "pet shop": "petshop.html",
    "advogado": "advogado.html",
    "oficina mecanica": "oficina.html",
    "auto escola": "oficina.html",
}


def normalize_categoria(cat):
    """Normaliza categoria para mapear ao template."""
    if not cat:
        return ""
    return (
        cat.lower()
        .replace("á", "a").replace("ã", "a").replace("â", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("õ", "o").replace("ô", "o")
        .replace("ú", "u")
        .replace("ç", "c")
        .strip()
    )


def get_template_file(categoria):
    """Retorna o arquivo de template para a categoria."""
    cat_norm = normalize_categoria(categoria)

    # Busca exata
    if cat_norm in CATEGORIA_TEMPLATE:
        return TEMPLATES_DIR / CATEGORIA_TEMPLATE[cat_norm]

    # Busca parcial
    for key, template in CATEGORIA_TEMPLATE.items():
        if key in cat_norm or cat_norm in key:
            return TEMPLATES_DIR / template

    # Fallback: template base
    return TEMPLATES_DIR / "base.html"


def carregar_template(categoria):
    """Carrega template HTML para a categoria."""
    template_file = get_template_file(categoria)
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"    [!] Erro ao carregar template {template_file.name}: {e}")
        # Fallback para base
        try:
            with open(TEMPLATES_DIR / "base.html", 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None


def carregar_emails_capturados():
    """Carrega emails do progresso_emails.json."""
    emails = {}  # key = "nome|cidade" -> {email_cnpj, email_comercial}
    try:
        if EMAILS_FILE.exists():
            with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for r in data.get("resultados", []):
                    key = f"{r['nome'].lower().strip()}|{r.get('cidade', '').lower().strip()}"
                    emails[key] = {
                        "email_cnpj": r.get("email_cnpj", ""),
                        "email_comercial": r.get("email_comercial", ""),
                    }
    except Exception as e:
        print(f"  [!] Erro ao carregar emails capturados: {e}")
    return emails


def carregar_leads():
    """Carrega leads do CSV + emails capturados."""
    comercios = []

    try:
        with open(LEADS_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                comercios.append(row)
    except Exception as e:
        print(f"  [!] Erro ao carregar CSV: {e}")
        return []

    # Merge com emails capturados
    emails_map = carregar_emails_capturados()

    leads = []
    for c in comercios:
        nome = c.get("nome", "")
        cidade = c.get("cidade", "")
        key = f"{nome.lower().strip()}|{cidade.lower().strip()}"
        em = emails_map.get(key, {})

        email_cnpj = em.get("email_cnpj", "")
        email_comercial = em.get("email_comercial", "")

        # Limpa telefone
        telefone = c.get("telefone", "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")

        if email_cnpj or email_comercial:
            leads.append({
                "nome": nome,
                "categoria": c.get("categoria", ""),
                "cidade": cidade,
                "telefone": telefone,
                "email_cnpj": email_cnpj,
                "email_comercial": email_comercial,
                "tem_site": c.get("tem_site", "False") == "True",
            })

    return leads


def carregar_progresso():
    """Carrega progresso de envio."""
    try:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"enviados": [], "data_ultimo": None}


def salvar_progresso(progresso):
    """Salva progresso de envio."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progresso, f, ensure_ascii=False, indent=2)


def personalizar_template(html, lead):
    """Substitui placeholders no template."""
    cidade_clean = lead["cidade"].replace(", RJ", "").replace(",RJ", "").strip()
    telefone_limpo = lead["telefone"]

    html = html.replace("{nome}", lead["nome"])
    html = html.replace("{categoria}", lead["categoria"])
    html = html.replace("{cidade}", lead["cidade"])
    html = html.replace("{telefone}", telefone_limpo)

    return html


def criar_email(to_email, nome, categoria, cidade, html_content):
    """Cria mensagem email multipart."""
    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_USER
    msg['To'] = f"{nome} <{to_email}>"
    msg['Subject'] = f"Oportunidade para o seu {categoria} em {cidade}"

    # Versao texto (fallback)
    text = f"""Oi {nome},

Aqui e da Equipe Vanderson, desenvolvimento web em Duque de Caxias.

Vi seu {categoria} no Google Maps.
Quando o cliente quer saber mais, nao encontra um site.

81% dos consumidores pesquisam online antes de comprar localmente.
Sem site, essas pessoas vao pro concorrente que tem.

Veja exemplos em: vandersonavellar.com

---
Equipe Vanderson
CNPJ: 65.999.597/0001-75
(21) 9XXXX-XXXX
"""
    msg.attach(MIMEText(text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    return msg


def enviar_email(smtp_pass, to_email, msg):
    """Envia email via Zoho SMTP."""
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"    [X] Erro: {str(e)[:60]}")
        return False


def pode_enviar():
    """Verifica horario comercial (seg-sex, 9h-18h)."""
    agora = datetime.now()
    return agora.weekday() < 6 and 9 <= agora.hour < 18


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("  ENVIO DE EMAILS POR CATEGORIA - ZOHO MAIL")
    print("=" * 60)
    print(f"  SMTP: {SMTP_HOST}:{SMTP_PORT}")
    print(f"  Limite: {LIMITE_DIA}/dia | Horario: 9h-18h (seg-sex)")
    print("=" * 60)

    smtp_pass = input(f"\nApp Password do Zoho ({SMTP_USER}): ").strip()
    if not smtp_pass:
        print("  [X] Senha nao informada. Saindo.")
        return

    # Carregar dados
    print("\n[1/4] Carregando leads...")
    leads = carregar_leads()
    print(f"  -> {len(leads)} leads com email")

    # Carregar progresso
    print("\n[2/4] Carregando progresso...")
    progresso = carregar_progresso()
    ja_enviados = {e["email"] for e in progresso["enviados"]}
    print(f"  -> {len(ja_enviados)} emails ja enviados")

    # Filtrar pendentes
    print("\n[3/4] Filtrando pendentes...")
    pendentes = []
    for lead in leads:
        emails_lead = []
        if lead["email_cnpj"] and lead["email_cnpj"] not in ja_enviados:
            emails_lead.append(("cnpj", lead["email_cnpj"]))
        if lead["email_comercial"] and lead["email_comercial"] not in ja_enviados:
            emails_lead.append(("comercial", lead["email_comercial"]))

        for tipo, email in emails_lead:
            pendentes.append({**lead, "email_destino": email, "tipo_email": tipo})

    random.shuffle(pendentes)
    print(f"  -> {len(pendentes)} emails pendentes")

    if not pendentes:
        print("\n  Todos os emails ja foram enviados!")
        return

    if not pode_enviar():
        print("\n  Fora do horario comercial (9h-18h, seg-sex)")
        return

    # Limitar por dia
    enviar_agora = pendentes[:LIMITE_DIA]
    print(f"\n[4/4] Enviando {len(enviar_agora)} emails...\n")

    enviados = 0
    for i, lead in enumerate(enviar_agora):
        template = carregar_template(lead["categoria"])
        if not template:
            continue

        html = personalizar_template(template, lead)
        msg = criar_email(
            lead["email_destino"],
            lead["nome"],
            lead["categoria"],
            lead["cidade"],
            html
        )

        print(f"  [{i+1}/{len(enviar_agora)}] {lead['nome'][:35]} -> {lead['email_destino'][:35]} ({lead['categoria']})")

        if enviar_email(smtp_pass, lead["email_destino"], msg):
            enviados += 1
            progresso["enviados"].append({
                "email": lead["email_destino"],
                "nome": lead["nome"],
                "categoria": lead["categoria"],
                "cidade": lead["cidade"],
                "tipo": lead["tipo_email"],
                "template": get_template_file(lead["categoria"]).name,
                "data": datetime.now().isoformat(),
            })

            # Salvar progresso a cada 5
            if enviados % 5 == 0:
                salvar_progresso(progresso)
                print(f"  [progresso salvo] {enviados} enviados")
        else:
            print(f"    falhou - pulando")

        # Delay entre emails
        if i < len(enviar_agora) - 1:
            delay = random.randint(DELAY_MIN, DELAY_MAX)
            print(f"  [aguarde {delay}s...]")
            time.sleep(delay)

    # Salvar progresso final
    progresso["data_ultimo"] = datetime.now().isoformat()
    salvar_progresso(progresso)

    print(f"\n{'=' * 60}")
    print(f"  RESUMO")
    print(f"{'=' * 60}")
    print(f"  Enviados agora: {enviados}")
    print(f"  Total historico: {len(progresso['enviados'])}")
    print(f"  Pendentes restantes: {len(pendentes) - enviados}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
