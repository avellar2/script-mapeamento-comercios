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
import re
import smtplib
import random
import sys
import time
import unicodedata
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
LEADS_FILE = OUTPUT_DIR / "playwright" / "leads_sem_site.csv"
EMAILS_FILE = OUTPUT_DIR / "playwright" / "progresso_emails.json"
PREVIEW_FILE = OUTPUT_DIR / "envios" / "ultima_previa_envio.csv"

# Zoho Mail SMTP
SMTP_HOST = os.getenv("ZOHO_SMTP_HOST", "smtppro.zoho.com")
SMTP_PORT = int(os.getenv("ZOHO_SMTP_PORT", "465"))
SMTP_USER = os.getenv("ZOHO_SMTP_USER", "contato@vandersonavellar.com")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ivqaccppqcchqshaplao.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2cWFjY3BwcWNjaHFzaGFwbGFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3Mjg4MDMsImV4cCI6MjA5MjMwNDgwM30.jXVgYGRCH5MFXtKvqQ2Y_dcUfoY0DY-CBBTu_iKMt60")

# Limites
# Defaults mais conservadores para reduzir bloqueio por reputacao.
DELAY_MIN = int(os.getenv("EMAIL_DELAY_MIN", "90"))
DELAY_MAX = int(os.getenv("EMAIL_DELAY_MAX", "180"))
LIMITE_DIA = int(os.getenv("EMAIL_LIMITE_DIA", "40"))
SMTP_TIMEOUT = int(os.getenv("ZOHO_SMTP_TIMEOUT", "30"))

EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
INVALID_EMAILS = {
    "x@x.com.br",
    "teste@teste.com",
    "test@test.com",
    "nao@informado.com",
}
INVALID_DOMAIN_SUFFIXES = (
    ".gov.br",
    ".jus.br",
    ".leg.br",
)

MODO_ENVIO = os.getenv("EMAIL_MODO", "seguro").strip().lower()
SAFE_MODE_LIMIT = int(os.getenv("EMAIL_SAFE_MODE_LIMIT", "5"))
TEST_MODE_LIMIT = int(os.getenv("EMAIL_TEST_MODE_LIMIT", "3"))

# Mapeamento de categoria -> template
# Chave = categoria normalizada (lowercase, sem acento)
CATEGORIA_TEMPLATE = {
    # Food
    "restaurante": "restaurante.html",
    "pizzaria": "pizzaria.html",
    "lanchonete": "lanchonete.html",
    "confeitaria": "confeitaria.html",
    "churrascaria": "restaurante.html",
    "bar": "bar.html",
    "padaria": "padaria.html",
    # Saude
    "academia": "academia.html",
    "estudio de pilates": "estudio_de_pilates.html",
    "dentista": "dentista.html",
    "clinica medica": "clinica_medica.html",
    "clinica veterinaria": "clinica_veterinaria.html",
    "estetica": "estetica.html",
    "farmacia": "farmacia.html",
    "otica": "otica.html",
    # Beleza
    "barbearia": "barbearia.html",
    "salao de beleza": "salao.html",
    # Servicos
    "advogado": "advogado.html",
    "contador": "contador.html",
    "oficina mecanica": "oficina.html",
    "auto escola": "auto_escola.html",
    "pet shop": "petshop.html",
    "eletricista": "eletricista.html",
    "encanador": "encanador.html",
    "pintor": "pintor.html",
    "marcenaria": "marcenaria.html",
    "serralheria": "serralheria.html",
    "vidracaria": "vidracaria.html",
    # Lojas
    "loja de roupas": "loja_de_roupas.html",
    "loja de moveis": "loja_de_moveis.html",
    "loja de celulares": "loja_de_celulares.html",
    "loja de bicicleta": "loja_de_bicicleta.html",
    "joalheria": "joalheria.html",
    "floricultura": "floricultura.html",
    "papelaria": "papelaria.html",
    "material de construcao": "material_de_construcao.html",
    "supermercado": "supermercado.html",
    "lavanderia": "lavanderia.html",
    # Educacao
    "escola de idiomas": "escola_de_idiomas.html",
    "curso pre vestibular": "curso_pre_vestibular.html",
    # Imoveis
    "imobiliaria": "imobiliaria.html",
}


def normalize_categoria(cat):
    """Normaliza categoria para mapear ao template."""
    if not cat:
        return ""
    cat = unicodedata.normalize("NFKD", cat)
    cat = "".join(ch for ch in cat if not unicodedata.combining(ch))
    return cat.lower().strip()


def normalize_email(email):
    """Normaliza email para deduplicacao e validacao."""
    return (email or "").strip().lower()


def validar_email_destino(email):
    """Valida se o email parece seguro para outreach comercial."""
    email = normalize_email(email)
    if not email:
        return False, "vazio"
    if email in INVALID_EMAILS:
        return False, "placeholder"
    if not EMAIL_REGEX.match(email):
        return False, "formato-invalido"

    domain = email.split("@", 1)[1]
    if domain.endswith(INVALID_DOMAIN_SUFFIXES):
        return False, "dominio-publico"

    return True, "ok"




def obter_dominio_email(email):
    """Extrai dominio do email para limitar repeticao por empresa."""
    email = normalize_email(email)
    return email.split("@", 1)[1] if "@" in email else ""


def obter_modo_envio():
    """Normaliza o modo de envio suportado."""
    if MODO_ENVIO in {"teste", "seguro", "normal"}:
        return MODO_ENVIO
    return "seguro"


def aplicar_modo_envio(pendentes, modo):
    """Aplica regras do modo de envio antes de disparar."""
    if modo == "normal":
        return pendentes, {}

    if modo == "teste":
        destino_teste = normalize_email(os.getenv("EMAIL_TEST_DESTINO", SMTP_USER))
        ajustados = []
        for lead in pendentes[:TEST_MODE_LIMIT]:
            copia = dict(lead)
            copia["email_real_destino"] = lead["email_destino"]
            copia["email_destino"] = destino_teste
            ajustados.append(copia)
        return ajustados, {"destino_teste": destino_teste, "limite": TEST_MODE_LIMIT}

    dominios_vistos = set()
    ajustados = []
    descartados_dominio = 0
    for lead in pendentes:
        dominio = obter_dominio_email(lead["email_destino"])
        if dominio in dominios_vistos:
            descartados_dominio += 1
            continue
        dominios_vistos.add(dominio)
        ajustados.append(lead)
        if len(ajustados) >= SAFE_MODE_LIMIT:
            break

    return ajustados, {"descartados_dominio": descartados_dominio, "limite": SAFE_MODE_LIMIT}


def salvar_previa_envio(modo, pendentes):
    """Salva uma previa do lote para revisao manual."""
    PREVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREVIEW_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'modo', 'nome', 'categoria', 'cidade', 'email_destino', 'email_real_destino', 'tipo_email'
        ])
        writer.writeheader()
        for lead in pendentes:
            writer.writerow({
                'modo': modo,
                'nome': lead.get('nome', ''),
                'categoria': lead.get('categoria', ''),
                'cidade': lead.get('cidade', ''),
                'email_destino': lead.get('email_destino', ''),
                'email_real_destino': lead.get('email_real_destino', ''),
                'tipo_email': lead.get('tipo_email', ''),
            })


def confirmar_envio(modo, pendentes, info_modo):
    """Mostra previa e pede confirmacao explicita."""
    salvar_previa_envio(modo, pendentes)

    print(f"\n  Modo ativo: {modo.upper()}")
    if modo == "teste":
        print(f"  Destino de teste: {info_modo.get('destino_teste', SMTP_USER)}")
        print("  Os leads reais NAO serao marcados como enviados.")
    elif modo == "seguro":
        print(f"  Limite seguro deste lote: {info_modo.get('limite', SAFE_MODE_LIMIT)}")
        if info_modo.get('descartados_dominio'):
            print(f"  Dominios repetidos descartados: {info_modo['descartados_dominio']}")

    print(f"  Previa salva em: {PREVIEW_FILE}")
    print("  Primeiros destinos:")
    for lead in pendentes[:5]:
        extra = f" | original={lead['email_real_destino']}" if lead.get('email_real_destino') else ""
        print(f"    - {lead['nome'][:28]} -> {lead['email_destino']}{extra}")

    confirmar = input("\n  Confirmar envio? (digite SIM para continuar): ").strip()
    return confirmar.upper() == "SIM"

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
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
        server.login(SMTP_USER, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except smtplib.SMTPResponseException as e:
        detalhe = e.smtp_error.decode(errors="ignore") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        print(f"    [X] SMTP {e.smtp_code}: {detalhe[:120]}")
        return False
    except Exception as e:
        print(f"    [X] {type(e).__name__}: {str(e)[:120]}")
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
    modo = obter_modo_envio()

    print(f"  SMTP: {SMTP_HOST}:{SMTP_PORT}")
    print(f"  Modo: {modo} | Limite base: {LIMITE_DIA}/dia | Horario: 9h-18h (seg-sex)")
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
    ja_enviados = {normalize_email(e["email"]) for e in progresso["enviados"]}
    print(f"  -> {len(ja_enviados)} emails ja enviados")

    # Filtrar pendentes
    print("\n[4/5] Filtrando pendentes...")
    pendentes = []
    emails_desta_execucao = set()
    motivos_skip = {}
    for lead in leads:
        emails_lead = []
        if lead["email_cnpj"]:
            emails_lead.append(("cnpj", lead["email_cnpj"]))
        if lead["email_comercial"]:
            emails_lead.append(("comercial", lead["email_comercial"]))

        for tipo, email in emails_lead:
            email_norm = normalize_email(email)
            valido, motivo = validar_email_destino(email_norm)
            if not valido:
                motivos_skip[motivo] = motivos_skip.get(motivo, 0) + 1
                continue
            if email_norm in ja_enviados or email_norm in emails_desta_execucao:
                motivos_skip["duplicado"] = motivos_skip.get("duplicado", 0) + 1
                continue

            pendentes.append({**lead, "email_destino": email_norm, "tipo_email": tipo})
            emails_desta_execucao.add(email_norm)

    random.shuffle(pendentes)
    print(f"  -> {len(pendentes)} emails pendentes")
    if motivos_skip:
        resumo_skip = ", ".join(f"{k}={v}" for k, v in sorted(motivos_skip.items()))
        print(f"  -> descartados: {resumo_skip}")

    if not pendentes:
        print("\n  Todos os emails ja foram enviados!")
        return

    pendentes, info_modo = aplicar_modo_envio(pendentes, modo)
    print(f"  -> lote preparado: {len(pendentes)} emails")

    if not pendentes:
        print("\n  Nenhum email sobrou apos aplicar o modo de envio.")
        return

    if not confirmar_envio(modo, pendentes, info_modo):
        print("\n  Envio cancelado. Ajuste os filtros e tente novamente.")
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

        extra = f" | original={lead['email_real_destino'][:35]}" if lead.get('email_real_destino') else ""
        print(f"  [{i+1}/{len(enviar_agora)}] {lead['nome'][:35]} -> {lead['email_destino'][:35]} ({lead['categoria']}){extra}")

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
        if modo == "teste" and lead.get("email_real_destino"):
            msg.replace_header('Subject', f"[TESTE] {msg['Subject']}")
            msg['X-Original-Destino'] = lead['email_real_destino']

        if enviar_email(smtp_pass, lead["email_destino"], msg):
            enviados += 1
            if modo != "teste":
                ja_enviados.add(lead["email_destino"])
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
                print("    [teste] enviado sem gravar progresso real")
        else:
            print(f"    falhou - pulando")

        # Delay entre emails
        if i < len(enviar_agora) - 1:
            delay = random.randint(DELAY_MIN, DELAY_MAX)
            print(f"  [aguarde {delay}s...]")
            time.sleep(delay)

    # Salvar progresso final
    if modo != "teste":
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
