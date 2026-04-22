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
import os
import smtplib
import random
import sys
import time
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# Carrega variaveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv eh opcional

# Supabase
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("  [!] Supabase client nao instalado. Instale: pip install supabase")

# Diretorios
OUTPUT_DIR = Path(__file__).parent / "output"
TEMPLATES_DIR = Path(__file__).parent / "templates"
PROGRESS_FILE = OUTPUT_DIR / "envios" / "progresso_envio.json"
LEADS_FILE = OUTPUT_DIR / "playwright" / "todos_comercios.csv"
EMAILS_FILE = OUTPUT_DIR / "playwright" / "progresso_emails.json"

# Zoho Mail SMTP
SMTP_HOST = os.getenv("ZOHO_SMTP_HOST", "smtppro.zoho.com")
SMTP_PORT = int(os.getenv("ZOHO_SMTP_PORT", "465"))
SMTP_USER = os.getenv("ZOHO_SMTP_USER", "contato@vandersonavellar.com")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ivqaccppqcchqshaplao.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2cWFjY3BwcWNjaHFzaGFwbGFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3Mjg4MDMsImV4cCI6MjA5MjMwNDgwM30.jXVgYGRCH5MFXtKvqQ2Y_dcUfoY0DY-CBBTu_iKMt60")

# Limites
DELAY_MIN = 30    # 30 segundos
DELAY_MAX = 60    # 60 segundos
LIMITE_DIA = 250  # emails por dia (Zoho Mail Lite)

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
    "contador": "contador.html",
    "oficina mecanica": "oficina.html",
    "auto escola": "auto_escola.html",
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

        tem_site = c.get("tem_site", "False") == "True"
        if not tem_site and (email_cnpj or email_comercial):
            leads.append({
                "nome": nome,
                "categoria": c.get("categoria", ""),
                "cidade": cidade,
                "telefone": telefone,
                "email_cnpj": email_cnpj,
                "email_comercial": email_comercial,
                "tem_site": tem_site,
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


def salvar_no_supabase(lead, tracking_id):
    """Salva registro de envio no Supabase."""
    if not HAS_SUPABASE:
        return False
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        data = {
            "nome": lead["nome"],
            "email": lead["email_destino"],
            "categoria": lead["categoria"],
            "cidade": lead["cidade"],
            "telefone": lead.get("telefone", ""),
            "tipo_email": lead["tipo_email"],
            "template": get_template_file(lead["categoria"]).name,
            "data_envio": datetime.now().isoformat(),
            "email_aberto": False,
            "qtd_aberturas": 0,
            "tracking_id": tracking_id,
        }
        result = supabase.table("emails_enviados").insert(data).execute()
        return True
    except Exception as e:
        print(f"    [!] Erro ao salvar no Supabase: {e}")
        return False


def personalizar_template(html, lead, tracking_id=None):
    """Substitui placeholders no template."""
    cidade_clean = lead["cidade"].replace(", RJ", "").replace(",RJ", "").strip()
    telefone_limpo = lead["telefone"]

    html = html.replace("{nome}", lead["nome"])
    html = html.replace("{categoria}", lead["categoria"])
    html = html.replace("{cidade}", lead["cidade"])
    html = html.replace("{telefone}", telefone_limpo)
    if tracking_id:
        html = html.replace("{TRACKING_ID}", tracking_id)

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


def escolher_opcoes(lista, label):
    """Permite usuario escolher multiplas opcoes de uma lista."""
    print(f"\n  {label}:")
    print(f"  0. TODOS")
    for i, item in enumerate(lista, 1):
        print(f"  {i}. {item}")
    print()
    escolha = input(f"  Escolha (ex: 0 para todos, ou 1,3,5 para multiplos): ").strip()
    if not escolha or escolha == "0":
        return None  # None = todos
    try:
        indices = [int(x.strip()) - 1 for x in escolha.split(",")]
        return [lista[i] for i in indices if 0 <= i < len(lista)]
    except (ValueError, IndexError):
        print("  [!] Opcao invalida, usando TODOS")
        return None


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

    smtp_pass = os.getenv("ZOHO_SMTP_APP_PASSWORD", "")
    if not smtp_pass:
        smtp_pass = input(f"\nApp Password do Zoho ({SMTP_USER}): ").strip()
    if not smtp_pass:
        print("  [X] Senha nao informada. Saindo.")
        return

    # Carregar dados
    print("\n[1/5] Carregando leads...")
    leads = carregar_leads()
    print(f"  -> {len(leads)} leads sem site com email")

    # Filtros interativos
    cidades_disponiveis = sorted(set(l["cidade"] for l in leads))
    categorias_disponiveis = sorted(set(l["categoria"] for l in leads))

    print("\n[2/5] Filtros:")
    cidades_escolhidas = escolher_opcoes(cidades_disponiveis, "Cidades")
    categorias_escolhidas = escolher_opcoes(categorias_disponiveis, "Categorias")

    # Aplicar filtros
    if cidades_escolhidas:
        leads = [l for l in leads if l["cidade"] in cidades_escolhidas]
        print(f"\n  Cidades: {len(cidades_escolhidas)} selecionadas")
    else:
        print(f"\n  Cidades: TODAS ({len(cidades_disponiveis)})")

    if categorias_escolhidas:
        leads = [l for l in leads if l["categoria"] in categorias_escolhidas]
        print(f"  Categorias: {len(categorias_escolhidas)} selecionadas")
    else:
        print(f"  Categorias: TODAS ({len(categorias_disponiveis)})")

    print(f"  -> {len(leads)} leads apos filtros")

    # Carregar progresso
    print("\n[3/5] Carregando progresso...")
    progresso = carregar_progresso()
    ja_enviados = {e["email"] for e in progresso["enviados"]}
    print(f"  -> {len(ja_enviados)} emails ja enviados")

    # Filtrar pendentes
    print("\n[4/5] Filtrando pendentes...")
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
    print(f"\n[5/5] Enviando {len(enviar_agora)} emails...\n")

    enviados = 0
    for i, lead in enumerate(enviar_agora):
        template = carregar_template(lead["categoria"])
        if not template:
            continue

        print(f"  [{i+1}/{len(enviar_agora)}] {lead['nome'][:35]} -> {lead['email_destino'][:35]} ({lead['categoria']})")

        # Gerar tracking ID unico
        tracking_id = str(uuid.uuid4())
        html = personalizar_template(template, lead, tracking_id)
        msg = criar_email(
            lead["email_destino"],
            lead["nome"],
            lead["categoria"],
            lead["cidade"],
            html
        )

        if enviar_email(smtp_pass, lead["email_destino"], msg):
            enviados += 1
            # Salvar no Supabase
            salvar_no_supabase(lead, tracking_id)
            # Salvar no progresso local
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
