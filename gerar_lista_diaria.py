#!/usr/bin/env python3
"""
Gerador de Lista Diária de Prospecção
======================================
Lê a campanha mais recente, filtra os melhores leads,
melhora as mensagens de WhatsApp, gera links wa.me,
define status e follow-up, e salva dados para o painel.
"""
import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from config.regioes import resolve_regiao, get_output_dir
from config.mensagens import gerar_mensagem_whatsapp, gerar_followup_1, gerar_followup_2

try:
    from openpyxl import load_workbook
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    from openpyxl import load_workbook

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PAINEL_DIR = OUTPUT_DIR / "painel"
CAMPANHAS_DIR = OUTPUT_DIR / "campanhas"
PROSPECCAO_DIR = OUTPUT_DIR / "prospeccao"

# ═══════════════════════════════════════════════════════════════════
# NICHOS PRIORITÁRIOS (ordem de prioridade para conversão)
# ═══════════════════════════════════════════════════════════════════

NICHOS_ESTETICA = ["estética", "estetica", "salão", "salao", "beleza", "manicure",
    "sobrancelha", "cílios", "cilios", "depilação", "depilacao", "spa",
    "clínica estética", "clinica estetica", "cabeleireiro", "cabeleireira",
    "maquiagem", "nail"]

NICHOS_BARBEARIA = ["barbearia", "barbeiro", "barber", "barbershop", "masculino"]

NICHOS_COMIDA = ["restaurante", "marmitaria", "pizzaria", "lanchonete", "açaí",
    "açai", "confeitaria", "padaria", "churrascaria", "comida", "delivery",
    "hambúrguer", "hamburguer", "hot dog", "sushi", "cardápio", "cardapio",
    "doces", "bolo"]

NICHOS_SERVICOS = ["assistência", "assistencia", "eletricista", "encanador",
    "manutenção", "manutencao", "serralheria", "marcenaria", "pintor",
    "vidraçaria", "vidracaria", "informática", "informatica", "técnico", "tecnico"]

NICHOS_DENTISTA = ["dentista", "odontológ", "odontolog", "clínica médica", "clinica medica"]

NICHOS_ADVOCACIA = ["advogado", "advocacia", "jurídico", "juridico"]

NICHOS_PRIORITARIOS = (
    NICHOS_ESTETICA + NICHOS_BARBEARIA + NICHOS_COMIDA +
    NICHOS_SERVICOS + NICHOS_DENTISTA + NICHOS_ADVOCACIA
)

# ═══════════════════════════════════════════════════════════════════
# MAPEAMENTO DE COLUNAS
# ═══════════════════════════════════════════════════════════════════

MAPEAMENTO = {
    "Nome": "nome", "Nicho": "nicho", "Categoria": "nicho", "Cidade": "cidade",
    "Bairro": "bairro", "Telefone": "telefone", "WhatsApp": "whatsapp",
    "Site": "site", "Tem Site?": "site", "URL Site": "url_site",
    "URL do Site": "url_site", "Nota": "nota_google", "Avaliação": "nota_google",
    "Nota Google": "nota_google", "Avaliações": "qtd_avaliacoes",
    "Nº Avaliações": "qtd_avaliacoes", "Score": "score",
    "Prioridade": "prioridade", "Oferta Sugerida": "oferta_sugerida",
    "Motivo Prioridade": "motivo_prioridade",
    "Mensagem WhatsApp": "mensagem_whatsapp",
    "Link WhatsApp": "link_whatsapp", "Endereço": "endereco",
    "Endereco": "endereco", "Email": "email", "Link Maps": "link_maps",
    "Ação Recomendada": "acao_recomendada", "Tipo de Material": "tipo_de_material",
    "Status": "status", "Data Abordagem": "data_abordagem",
    "Data Follow-up": "data_followup", "Observações": "observacoes",
}

# ═══════════════════════════════════════════════════════════════════
# LEITURA
# ═══════════════════════════════════════════════════════════════════

def ler_excel(caminho, aba=None):
    """Lê planilha Excel e retorna lista de dicts."""
    wb = load_workbook(caminho, read_only=True, data_only=True)
    if aba and aba in wb.sheetnames:
        ws = wb[aba]
    else:
        ws = wb[wb.sheetnames[0]]

    cabecalhos = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]
    col_map = {}
    for idx, cab in enumerate(cabecalhos):
        nome_interno = MAPEAMENTO.get(cab, cab.lower().strip())
        col_map[nome_interno] = idx

    leads = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        lead = {}
        for nome_interno, idx in col_map.items():
            lead[nome_interno] = str(row[idx]) if idx < len(row) and row[idx] is not None else ""
        if lead.get("nome"):
            leads.append(lead)
    wb.close()
    return leads


def ler_todas_abas(caminho):
    """Lê todas as abas e retorna leads únicos."""
    wb = load_workbook(caminho, read_only=True, data_only=True)
    todos = []
    vistos = set()
    for nome_aba in wb.sheetnames:
        if nome_aba.lower() == "resumo":
            continue
        ws = wb[nome_aba]
        cabecalhos = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]
        col_map = {}
        for idx, cab in enumerate(cabecalhos):
            nome_interno = MAPEAMENTO.get(cab, cab.lower().strip())
            col_map[nome_interno] = idx
        for row in ws.iter_rows(min_row=2, values_only=True):
            lead = {}
            for nome_interno, idx in col_map.items():
                lead[nome_interno] = str(row[idx]) if idx < len(row) and row[idx] is not None else ""
            if lead.get("nome"):
                chave = (lead.get("nome", "").strip().lower(), lead.get("cidade", "").strip().lower())
                if chave not in vistos:
                    vistos.add(chave)
                    todos.append(lead)
    wb.close()
    return todos


def encontrar_planilha():
    """Encontra planilha mais recente."""
    campanha = CAMPANHAS_DIR / "campanha_diaria.xlsx"
    if campanha.exists():
        return campanha, "campanha"
    prospeccao = PROSPECCAO_DIR / "leads_prospeccao.xlsx"
    if prospeccao.exists():
        return prospeccao, "prospeccao"
    for d in [CAMPANHAS_DIR, PROSPECCAO_DIR]:
        xlsx_files = list(d.glob("*.xlsx"))
        if xlsx_files:
            return xlsx_files[0], "fallback"
    return None, None

# ═══════════════════════════════════════════════════════════════════
# NORMALIZAÇÃO E FILTRO
# ═══════════════════════════════════════════════════════════════════

def normalizar_lead(lead):
    """Normaliza campos do lead."""
    n = {}
    n["nome"] = str(lead.get("nome", "")).strip()
    n["nicho"] = str(lead.get("nicho", lead.get("categoria", ""))).strip().lower()
    n["cidade"] = str(lead.get("cidade", "")).strip()
    n["bairro"] = str(lead.get("bairro", "")).strip()
    n["telefone"] = str(lead.get("telefone", "")).strip()
    n["whatsapp"] = str(lead.get("whatsapp", "")).strip()

    # Site
    site_val = str(lead.get("site", "")).strip().lower()
    n["tem_site"] = site_val in ("true", "sim", "1", "yes", "verdadeiro")

    n["url_site"] = str(lead.get("url_site", "")).strip()

    # Nota
    nota = str(lead.get("nota_google", lead.get("avaliacao", "0"))).strip()
    try:
        n["nota_google"] = float(nota.replace(",", "."))
    except (ValueError, TypeError):
        n["nota_google"] = 0.0

    # Qtd avaliações
    qtd = str(lead.get("qtd_avaliacoes", lead.get("num_avaliacoes", "0"))).strip()
    try:
        n["qtd_avaliacoes"] = int(re.sub(r"\D", "", qtd))
    except (ValueError, TypeError):
        n["qtd_avaliacoes"] = 0

    # Score
    try:
        n["score"] = int(float(str(lead.get("score", 0))))
    except (ValueError, TypeError):
        n["score"] = 0

    n["prioridade"] = str(lead.get("prioridade", "")).strip()
    n["oferta_sugerida"] = str(lead.get("oferta_sugerida", "")).strip()
    n["motivo_prioridade"] = str(lead.get("motivo_prioridade", "")).strip()
    n["email"] = str(lead.get("email", "")).strip()
    n["endereco"] = str(lead.get("endereco", "")).strip()
    n["link_maps"] = str(lead.get("link_maps", "")).strip()
    n["instagram"] = str(lead.get("instagram", "")).strip()
    n["status"] = str(lead.get("status", "")).strip().lower()
    n["observacoes"] = str(lead.get("observacoes", "")).strip()

    return n


def tem_whatsapp(lead):
    """Verifica se o lead tem número de WhatsApp utilizável."""
    tel = lead.get("whatsapp", "") or lead.get("telefone", "")
    numeros = re.sub(r"\D", "", tel)
    return len(numeros) >= 10


def extrair_numero(lead):
    """Extrai número formatado para wa.me."""
    tel = lead.get("whatsapp", "") or lead.get("telefone", "")
    numeros = re.sub(r"\D", "", tel)
    if not numeros:
        return ""
    if numeros.startswith("55") and len(numeros) >= 12:
        return numeros
    elif len(numeros) in (10, 11):
        return "55" + numeros
    return ""


def calcular_prioridade_nicho(lead):
    """Retorna peso de prioridade baseado no nicho (1-6)."""
    nicho = lead.get("nicho", "").lower()
    if any(n in nicho for n in NICHOS_ESTETICA):
        return 1
    if any(n in nicho for n in NICHOS_BARBEARIA):
        return 2
    if any(n in nicho for n in NICHOS_COMIDA):
        return 3
    if any(n in nicho for n in NICHOS_SERVICOS):
        return 4
    if any(n in nicho for n in NICHOS_DENTISTA):
        return 5
    if any(n in nicho for n in NICHOS_ADVOCACIA):
        return 6
    return 7


def filtrar_melhores_leads(leads, limite=15, regiao_key=None):
    """Filtra e ordena os melhores leads para prospecção."""
    # Filtrar: sem site, com WhatsApp, score >= 70
    candidatos = []
    for lead in leads:
        n = normalizar_lead(lead)
        # Deve ter nome
        if not n["nome"]:
            continue
        # Deve ter WhatsApp ou telefone
        if not tem_whatsapp(n):
            continue
        # Preferir sem site
        # Score mínimo 65 (um pouco flexível pra pegar mais leads)
        if n["score"] < 65:
            continue
        # Ignorar leads já perdidos
        if n["status"] in ("perdido", "não abordar", "fechado"):
            continue
        # Filtrar por origem/regiao se especificado
        if regiao_key and regiao_key != "todas":
            origem = str(lead.get("origem", "")).strip().lower()
            if origem and origem != regiao_key:
                continue
        candidatos.append(n)

    # Ordenar: nicho prioritário > score > nota google > sem site
    candidatos.sort(key=lambda x: (
        calcular_prioridade_nicho(x),    # nicho prioritário primeiro
        -x["score"],                       # score maior primeiro
        -x["nota_google"],                 # nota google maior
        x["tem_site"],                     # sem site primeiro (False < True)
    ))

    return candidatos[:limite]


# ═══════════════════════════════════════════════════════════════════
# MENSAGENS MELHORADAS (humanas, curtas, consultivas)
# ═══════════════════════════════════════════════════════════════════

def gerar_mensagem_melhorada(lead):
    """Gera mensagem de WhatsApp humana, curta e consultiva."""
    nome = lead.get("nome", "").strip()
    # Pegar só o primeiro nome ou o nome do negócio curto
    nome_curto = nome.split(" - ")[0].split(" | ")[0].strip()
    if len(nome_curto) > 30:
        nome_curto = nome_curto[:30].rsplit(" ", 1)[0].strip()

    nicho = lead.get("nicho", "").lower()
    nota = lead.get("nota_google", 0)
    qtd_av = lead.get("qtd_avaliacoes", 0)
    oferta = lead.get("oferta_sugerida", "").lower()

    # Estética / Salão
    if any(n in nicho for n in NICHOS_ESTETICA):
        if nota >= 4.5 and qtd_av >= 20:
            return (
                f"Oi! Vi o {nome_curto} no Google, viu? {nota:.1f} estrelas com {qtd_av} avaliações, "
                f"isso é muito bom. Queria te mostrar rapidinho como fica uma página de agendamento "
                f"pro seu salão — com WhatsApp direto, serviços e localização. Posso mandar uma prévia?"
            )
        return (
            f"Oi, tudo bem? Vi o {nome_curto} no Google e pensei comigo: um salão com esse "
            f"trabalho merece uma página bonita com agendamento direto pelo WhatsApp. "
            f"Posso te mostrar como ficaria? É rapidinho."
        )

    # Barbearia
    if any(n in nicho for n in NICHOS_BARBEARIA):
        if nota >= 4.5 and qtd_av >= 20:
            return (
                f"Oi! Vi a {nome_curto} no Google — {nota:.1f} estrelas, "
                f"{qtd_av} avaliações. Cara, imagine só o cliente te achando no Google "
                f"e agendando o corte direto pelo WhatsApp, sem precisar ligar. "
                f"Posso te mandar como ficaria a página?"
            )
        return (
            f"Oi, tudo bem? Vi a {nome_curto} e pensei: uma página de agendamento "
            f"com os cortes, horário e WhatsApp direto facilitaria muito pro cliente. "
            f"Quer ver como ficaria?"
        )

    # Comida / Cardápio
    if any(n in nicho for n in NICHOS_COMIDA):
        if nota >= 4.5 and qtd_av >= 20:
            return (
                f"Oi! Com {nota:.1f} estrelas e {qtd_av} avaliações, o {nome_curto} "
                f"já é destaque na região. Imagine o cliente abrindo um cardápio digital "
                f"bonitão e pedindo direto pelo WhatsApp. Posso te mostrar como fica?"
            )
        return (
            f"Oi, tudo bem? Vi o {nome_curto} no Google. Um cardápio digital com as fotos "
            f"dos pratos e o botão de pedido direto no WhatsApp faz o cliente pedir sem "
            f"ficar perguntando tudo. Quer ver como ficaria?"
        )

    # Dentista / Clínica
    if any(n in nicho for n in NICHOS_DENTISTA):
        return (
            f"Olá, tudo bem? Vi a {nome_curto} e notei que uma página profissional com "
            f"os tratamentos, fotos da clínica e agendamento pelo WhatsApp transmitiria "
            f"mais confiança pra quem procura. Posso mostrar como ficaria?"
        )

    # Advocacia
    if any(n in nicho for n in NICHOS_ADVOCACIA):
        return (
            f"Olá! Vi o escritório e pensei: uma página institucional organizada com as "
            f"áreas de atuação e WhatsApp direto transmite mais credibilidade pra quem "
            f"está buscando orientação. Posso te mandar uma prévia?"
        )

    # Serviços técnicos
    if any(n in nicho for n in NICHOS_SERVICOS):
        return (
            f"Oi, tudo bem? Vi o {nome_curto} no Google. Quando alguém precisa de um "
            f"serviço com urgência, quer encontrar rápido — serviços, região atendida e "
            f"botão de orçamento no WhatsApp. Posso te mostrar como ficaria uma página assim?"
        )

    # Geral
    return (
        f"Oi, tudo bem? Vi o {nome_curto} no Google e percebi que uma página simples "
        f"com informações claras e WhatsApp direto facilitaria pra quem te procura. "
        f"Quer ver como ficaria?"
    )


def gerar_link_wame(lead, mensagem=None):
    """Gera link wa.me com mensagem preenchida."""
    numero = extrair_numero(lead)
    if not numero:
        return ""
    if not mensagem:
        mensagem = gerar_mensagem_melhorada(lead)
    msg_encoded = quote(mensagem)
    return f"https://wa.me/{numero}?text={msg_encoded}"


def gerar_followup_msg(lead, tentativa=2):
    """Gera mensagem de follow-up (2ª ou 3ª abordagem)."""
    nome = lead.get("nome", "").strip()
    nome_curto = nome.split(" - ")[0].split(" | ")[0].strip()[:30]

    if tentativa == 2:
        return (
            f"Oi! Tentei te contatar sobre o {nome_curto}. Sem pressa, mas se tiver "
            f"curiosidade pra ver como ficaria uma página digital, é só me chamar. 👋"
        )
    elif tentativa == 3:
        return (
            f"Oi! Última tentativa rs. Posso montar uma prévia da página do {nome_curto} "
            f"sem compromisso. Se não for o momento, tudo bem. Abraço!"
        )
    return ""


# ═══════════════════════════════════════════════════════════════════
# SAÍDA E SALVAMENTO
# ═══════════════════════════════════════════════════════════════════

def gerar_lista_diaria(leads_filtrados, regiao=None):
    """Gera a lista diária formatada."""
    from config.regioes import BAIXADA
    if regiao is None:
        regiao = BAIXADA

    hoje = date.today().strftime("%Y-%m-%d")
    followup_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    lista = []
    for i, lead in enumerate(leads_filtrados, 1):
        nome = lead.get("nome", "")
        nicho = lead.get("nicho", "")
        cidade = lead.get("cidade", "")
        bairro = lead.get("bairro", "")
        score = lead.get("score", 0)
        nota = lead.get("nota_google", 0)
        qtd_av = lead.get("qtd_avaliacoes", 0)
        telefone = lead.get("telefone", "")
        whatsapp = lead.get("whatsapp", "")
        oferta = lead.get("oferta_sugerida", "")
        motivo = lead.get("motivo_prioridade", "")
        tem_site = lead.get("tem_site", False)
        numero_whatsapp = extrair_numero(lead)
        msg = gerar_mensagem_whatsapp(lead, regiao)
        link = gerar_link_wame(lead, msg)
        followup_msg = gerar_followup_1(lead, regiao)

        entry = {
            "posição": i,
            "nome": nome,
            "nicho": nicho.upper(),
            "cidade": cidade,
            "bairro": bairro,
            "score": score,
            "nota_google": nota,
            "qtd_avaliacoes": qtd_av,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "tem_site": "Sim" if tem_site else "Não",
            "oferta_sugerida": oferta,
            "motivo": motivo,
            "status": "pronto_para_enviar",
            "data_lista": hoje,
            "data_followup": followup_date,
            "mensagem_whatsapp": msg,
            "link_wame": link,
            "numero_formatado": numero_whatsapp,
            "followup_mensagem": followup_msg,
        }
        lista.append(entry)
    return lista


def salvar_para_painel(lista, regiao_key="baixada"):
    """Salva dados no formato do painel (status_leads.json e prospeccao.db)."""
    # Salvar JSON para o painel
    status_dict = {}
    for item in lista:
        lead_id = re.sub(r"[^a-z0-9]+", "-", f"{item['nome'].lower().strip()}|{item['cidade'].lower().strip()}")[:60]
        status_dict[lead_id] = {
            "lead_id": lead_id,
            "nome": item["nome"],
            "status": "pronto_para_enviar",
            "data_abordagem": "",
            "data_followup": item["data_followup"],
            "observacoes": "",
        }

    painel_dir = get_output_dir(regiao_key, "painel")
    json_path = painel_dir / "lista_diaria_status.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(status_dict, f, ensure_ascii=False, indent=2)

    # Upsert no SQLite
    try:
        sys.path.insert(0, str(PAINEL_DIR))
        import db
        db.init_db()
        conn = db.get_conn()
        rodada = db.get_rodada_atual(conn) + 1
        count = 0
        for item in lista:
            lead_id = re.sub(r"[^a-z0-9]+", "-", f"{item['nome'].lower().strip()}|{item['cidade'].lower().strip()}")[:60]
            db.upsert_lead_full(conn,
                lead_id=lead_id,
                nome=item.get("nome", ""),
                status="pronto_para_enviar",
                nicho=item.get("nicho", ""),
                cidade=item.get("cidade", ""),
                bairro=item.get("bairro", ""),
                telefone=item.get("telefone", ""),
                whatsapp=item.get("whatsapp", ""),
                score=item.get("score", 0),
                prioridade="Alta" if item.get("score", 0) >= 70 else "Media" if item.get("score", 0) >= 40 else "Baixa",
                mensagem_whatsapp=item.get("mensagem_whatsapp", ""),
                link_whatsapp=item.get("link_wame", ""),
                rodada=rodada,
                tem_site=item.get("tem_site", "Não"),
                nota_google=item.get("nota_google", 0),
                qtd_avaliacoes=item.get("qtd_avaliacoes", 0),
                oferta_sugerida=item.get("oferta_sugerida", ""),
                motivo_prioridade=item.get("motivo", ""),
                followup_mensagem=item.get("followup_mensagem", ""),
                numero_formatado=item.get("numero_formatado", ""),
                categoria=item.get("nicho", ""),
                proximo_followup=item.get("data_followup", ""),
            )
            count += 1
        db.recalcular_metricas(conn)
        conn.close()
        print(f"💾 {count} leads inseridos/atualizados no SQLite (rodada {rodada})")
    except Exception as e:
        print(f"⚠️ Erro ao salvar no SQLite: {e}")

    return json_path


def gerar_relatorio_texto(lista, regiao_label="Baixada Fluminense"):
    """Gera relatório em texto formatado para exibição."""
    hoje = date.today().strftime("%d/%m/%Y")
    followup = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")

    linhas = []
    linhas.append("=" * 80)
    linhas.append(f"📋 LISTA DIÁRIA DE PROSPECÇÃO — {hoje} — {regiao_label}")
    linhas.append(f"Follow-up previsto: {followup}")
    linhas.append(f"Total de leads: {len(lista)}")
    linhas.append("=" * 80)
    linhas.append("")

    # Resumo por nicho
    nichos = {}
    for item in lista:
        n = item["nicho"]
        nichos[n] = nichos.get(n, 0) + 1
    linhas.append("Resumo por nicho:")
    for n, q in sorted(nichos.items(), key=lambda x: -x[1]):
        linhas.append(f"  • {n}: {q}")
    linhas.append("")

    # Resumo por cidade
    cidades = {}
    for item in lista:
        c = item["cidade"]
        cidades[c] = cidades.get(c, 0) + 1
    linhas.append("Resumo por cidade:")
    for c, q in sorted(cidades.items(), key=lambda x: -x[1]):
        linhas.append(f"  • {c}: {q}")
    linhas.append("")
    linhas.append("-" * 80)

    # Leads detalhados
    for item in lista:
        linhas.append("")
        linhas.append(f"#{item['posição']} — {item['nome']}")
        linhas.append(f"  Nicho: {item['nicho']} | Cidade: {item['cidade']} | Bairro: {item['bairro']}")
        linhas.append(f"  Score: {item['score']} | Nota: {item['nota_google']} ({item['qtd_avaliacoes']} avaliações)")
        linhas.append(f"  Sem site: {item['tem_site']} | Oferta: {item['oferta_sugerida']}")
        linhas.append(f"  WhatsApp: {item['numero_formatado']}")
        linhas.append(f"  Motivo: {item['motivo']}")
        linhas.append("")
        linhas.append(f"  📱 MENSAGEM:")
        linhas.append(f"  {item['mensagem_whatsapp']}")
        linhas.append("")
        linhas.append(f"  🔗 LINK DIRETO:")
        linhas.append(f"  {item['link_wame']}")
        linhas.append("")
        linhas.append(f"  📅 Follow-up em {followup}:")
        linhas.append(f"  {item['followup_mensagem']}")
        linhas.append("")
        linhas.append("-" * 80)

    return "\n".join(linhas)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Gerador de Lista Diaria de Prospeccao")
    parser.add_argument(
        "--regiao",
        choices=["baixada", "rio_premium", "todas"],
        default=None,
        help="Regiao de prospeccao (padrao: baixada)",
    )
    args = parser.parse_args()

    regioes = resolve_regiao(args.regiao)

    for regiao in regioes:
        regiao_key = regiao.key
        regiao_label = regiao.label

        print("=" * 60)
        print(f"🔧 Gerando lista diária de prospecção — {regiao_label}...")
        print("=" * 60)

        # 1. Encontrar planilha
        planilha, tipo = encontrar_planilha()
        if not planilha:
            print("❌ Nenhuma planilha encontrada!")
            continue
        print(f"📊 Planilha: {planilha.name} (tipo: {tipo})")

        # 2. Ler leads
        if tipo == "campanha":
            leads = ler_todas_abas(planilha)
        else:
            leads = ler_excel(planilha)
        print(f"📈 Total de leads na planilha: {len(leads)}")

        # 3. Filtrar melhores
        melhores = filtrar_melhores_leads(leads, limite=15, regiao_key=regiao_key)
        print(f"🎯 Leads filtrados ({regiao_label}, top 15): {len(melhores)}")

        if not melhores:
            print(f"❌ Nenhum lead elegível encontrado para {regiao_label}!")
            continue

        # 4. Gerar lista diária
        lista = gerar_lista_diaria(melhores, regiao=regiao)

        # 5. Salvar JSON para o painel
        json_path = salvar_para_painel(lista, regiao_key=regiao_key)
        print(f"💾 Status salvo em: {json_path}")

        # 6. Gerar relatório
        relatorio = gerar_relatorio_texto(lista, regiao_label=regiao_label)

        # Salvar relatório em arquivo
        hoje = date.today().strftime("%Y-%m-%d")
        painel_dir = get_output_dir(regiao_key, "painel")
        relatorio_path = painel_dir / f"lista_diaria_{regiao_key}_{hoje}.txt"
        with open(relatorio_path, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"📝 Relatório salvo em: {relatorio_path}")

        # 7. Salvar JSON completo da lista
        lista_path = painel_dir / f"lista_diaria_{regiao_key}_{hoje}.json"
        with open(lista_path, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
        print(f"📋 Lista completa salva em: {lista_path}")

        # Imprimir relatório
        print("\n")
        print(relatorio)

    return lista


if __name__ == "__main__":
    main()