"""
Importador de leads via ZIP/XLSX para Supabase — AVGestão Assistências Técnicas.

Usado pelo comando `import-leads` do campanha_whatsapp.py.
Suporte: ZIP (contendo XLSX do mapeamento) ou XLSX direto.
"""

import argparse
import asyncio
import io
import json
import logging
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import openpyxl
except ImportError:
    openpyxl = None

from dotenv import load_dotenv, find_dotenv
from supabase import create_client

from utils.phone_utils import normalizar_telefone_br
from utils.campaign_key import gerar_campaign_key, validar_campaign_key

logger = logging.getLogger(__name__)

# Mapeamento de queries de captura → subnicho_key oficial
QUERY_PARA_SUBNICHO = {
    "assistência técnica de celular": "celular",
    "conserto de celular": "celular",
    "assistência técnica de computadores": "computadores",
    "assistência de computadores e notebooks": "computadores",
    "assistência técnica de impressoras": "impressoras",
    "assistência de impressoras": "impressoras",
    "assistência técnica de eletrodomésticos": "eletrodomesticos",
    "assistência de eletrodomésticos": "eletrodomesticos",
    "assistência técnica de eletrônicos": "eletronicos",
    "assistência de eletrônicos e videogames": "eletronicos",
}

# Mapeamento de colunas XLSX → campos Supabase
COL_MAP = {
    "Nome": "nome",
    "Nome curto": "nome_curto",
    "Cidade": "cidade",
    "Subnicho": "subnicho",
    "Telefone": "telefone",
    "WhatsApp": "whatsapp",
    "Instagram": "instagram",
    "Site": "url_site",
    "Avaliacao": "avaliacao",
    "Avaliação": "avaliacao",
    "Quantidade de avaliacoes": "num_avaliacoes",
    "Quantidade de avaliações": "num_avaliacoes",
    "Faz assistencia": "faz_assistencia",
    "Faz assistência": "faz_assistencia",
    "Score AVGESTAO": "score_avgestao",
    "Score AVGESTÃO": "score_avgestao",
    "Motivos do score": "motivos_score",
    "Mensagem inicial": "mensagem_whatsapp",
    "Link WhatsApp": "link_whatsapp",
    "Query de origem": "source_query",
    "Escopo de origem": "source_scope",
    "Run ID": "run_id",
    "Capturado em": "captured_at",
    "Place ID": "place_id",
    "URL Google Maps": "maps_url",
    "UF": "uf",
    "Estado": "estado",
    "Regiao": "regiao",
    "Nicho": "nicho",
    "Status": "status",
    "Data da abordagem": "data_abordagem",
    "Follow-up 1": "followup_1",
    "Follow-up 2": "followup_2",
}


def _get_supabase_client():
    """Obtem client Supabase autenticado."""
    load_dotenv(find_dotenv(usecwd=True))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_ANON_KEY sao necessarios.")
    return create_client(url, key)


def _extrair_xlsx_do_zip(zip_path: str) -> io.BytesIO:
    """Extrai o XLSX principal de um ZIP de captura."""
    zf = zipfile.ZipFile(zip_path)
    xlsx_names = [n for n in zf.namelist() if n.endswith(".xlsx") and "leads_assistencias" in n.lower()]
    if not xlsx_names:
        xlsx_names = [n for n in zf.namelist() if n.endswith(".xlsx")]
    if not xlsx_names:
        raise ValueError("Nenhum arquivo XLSX encontrado no ZIP.")
    return io.BytesIO(zf.read(xlsx_names[0]))


def _resolver_subnicho(source_query: str, subnicho_raw: str) -> str:
    """Resolve subnicho_key oficial a partir da query e/ou subnicho bruto."""
    import unicodedata
    ql = unicodedata.normalize('NFKD', source_query.lower().strip()).encode('ascii', 'ignore').decode('ascii')
    for padrao, key in QUERY_PARA_SUBNICHO.items():
        pn = unicodedata.normalize('NFKD', padrao).encode('ascii', 'ignore').decode('ascii')
        if pn in ql:
            return key
    # Fallback: tentar subnicho_raw
    if subnicho_raw and subnicho_raw.lower() in {"celular", "computadores", "impressoras", "eletrodomesticos", "eletronicos", "eletrônicos"}:
        return subnicho_raw.lower().replace("eletrônicos", "eletronicos")
    return ""


def _ler_xlsx_para_leads(xlsx_data: io.BytesIO) -> list[dict]:
    """Le um XLSX e retorna lista de leads normalizados."""
    if openpyxl is None:
        raise ImportError("openpyxl e necessario para ler XLSX. Instale com: pip install openpyxl")

    wb = openpyxl.load_workbook(xlsx_data, data_only=True)
    ws = wb[wb.sheetnames[0]]
    headers = [str(cell.value or "") for cell in ws[1]]

    # Mapear col indexes
    col_idx = {}
    for i, h in enumerate(headers):
        h_clean = h.strip()
        if h_clean in COL_MAP:
            col_idx[COL_MAP[h_clean]] = i

    leads = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < max(col_idx.values(), default=0) + 1:
            continue
        lead = {}
        for campo, idx in col_idx.items():
            val = row[idx] if idx < len(row) else None
            lead[campo] = str(val).strip() if val is not None and str(val) != "None" else ""

        if not lead.get("nome"):
            continue

        # Resolver subnicho
        source_query = lead.get("source_query", "")
        subnicho_raw = lead.get("subnicho", "")
        lead["subnicho"] = _resolver_subnicho(source_query, subnicho_raw)
        if not lead["subnicho"]:
            continue  # sem subnicho = nao e assistencia

        # Telefone: prioridade WhatsApp > Telefone
        tel_raw = lead.get("whatsapp") or lead.get("telefone") or ""
        lead["telefone"] = tel_raw
        lead["telefone_normalizado"] = normalizar_telefone_br(tel_raw)

        # Placeholder: message
        lead["mensagem_whatsapp"] = lead.get("mensagem_whatsapp", "")

        leads.append(lead)

    wb.close()
    return leads


def _classificar_leads(leads: list[dict], produto: str, grupo: str, origem: str) -> dict:
    """Analisa e classifica leads para importacao."""
    resultado = {
        "total_lido": len(leads),
        "produto": produto,
        "grupo": grupo,
        "origem": origem,
        "com_telefone": 0,
        "sem_telefone": 0,
        "telefone_invalido": 0,
        "telefone_valido": 0,
        "duplicados_internos": 0,
        "unicos": 0,
        "por_subnicho": Counter(),
        "por_cidade": Counter(),
        "validos": [],
        "invalidos": [],
    }

    vistos: dict[str, dict] = {}
    for lead in leads:
        tel_raw = lead.get("telefone") or lead.get("whatsapp") or ""
        tel_norm = lead.get("telefone_normalizado", "")
        # Normalizar se ainda nao foi normalizado
        if not tel_norm and tel_raw and tel_raw != "None":
            lead["telefone_normalizado"] = normalizar_telefone_br(tel_raw)
            tel_norm = lead["telefone_normalizado"]

        # Validar telefone primeiro
        if not tel_raw or tel_raw == "None":
            resultado["sem_telefone"] += 1
            resultado["invalidos"].append({"nome": lead.get("nome", "")[:40], "motivo": "sem_telefone"})
            continue

        resultado["com_telefone"] += 1

        if not tel_norm or not tel_norm.startswith("55") or len(tel_norm) < 10:
            resultado["telefone_invalido"] += 1
            resultado["invalidos"].append({"nome": lead.get("nome", "")[:40], "motivo": "tel_invalido",
                                            "tel_masked": (tel_raw[:4] + "****" + tel_raw[-4:]) if len(tel_raw) >= 8 else "****"})
            continue

        # Resolver subnicho se nao veio preenchido
        if "subnicho" not in lead or not lead["subnicho"]:
            lead["subnicho"] = _resolver_subnicho(lead.get("source_query", ""), lead.get("subnicho", ""))
        if not lead.get("subnicho"):
            resultado["invalidos"].append({"nome": lead.get("nome", "")[:40], "motivo": "sem_subnicho"})
            continue

        resultado["telefone_valido"] += 1

        if tel_norm in vistos:
            resultado["duplicados_internos"] += 1
            continue

        lead["produto"] = produto
        lead["grupo"] = grupo
        lead["origem"] = origem
        lead["status"] = "novo"

        vistos[tel_norm] = lead
        resultado["por_subnicho"][lead.get("subnicho", "?")] += 1
        resultado["por_cidade"][lead.get("cidade", "?")] += 1

    resultado["validos"] = list(vistos.values())
    resultado["unicos"] = len(resultado["validos"])
    return resultado


def _consultar_existentes(sb, telefones: list[str]) -> dict[str, dict]:
    """Consulta Supabase por telefones ja existentes."""
    existentes = {}
    batch_size = 100
    for i in range(0, len(telefones), batch_size):
        batch = telefones[i:i + batch_size]
        try:
            resp = sb.table("leads").select("id,nome,telefone_normalizado,status,produto,grupo,subnicho").in_("telefone_normalizado", batch).execute()
            for row in resp.data:
                existentes[row["telefone_normalizado"]] = row
        except Exception as e:
            logger.warning("Erro ao consultar existentes (batch %d): %s", i, e)
    return existentes


def _inserir_lead(sb, lead: dict) -> bool:
    """Insere um lead no Supabase. Retorna True se sucesso."""
    try:
        payload = {
            "nome": lead.get("nome", ""),
            "nome_curto": lead.get("nome_curto", ""),
            "telefone": lead.get("telefone", ""),
            "whatsapp": lead.get("whatsapp", ""),
            "telefone_normalizado": lead.get("telefone_normalizado", ""),
            "cidade": lead.get("cidade", ""),
            "subnicho": lead.get("subnicho", ""),
            "grupo": lead.get("grupo", ""),
            "produto": lead.get("produto", ""),
            "status": lead.get("status", "novo"),
            "origem": lead.get("origem", ""),
            "instagram": lead.get("instagram", ""),
            "url_site": lead.get("url_site", ""),
            "uf": lead.get("uf", ""),
            "estado": lead.get("estado", ""),
            "regiao": lead.get("regiao", ""),
            "source_query": lead.get("source_query", ""),
            "source_scope": lead.get("source_scope", ""),
            "run_id": lead.get("run_id", ""),
            "captured_at": lead.get("captured_at", ""),
            "place_id": lead.get("place_id", ""),
            "maps_url": lead.get("maps_url", ""),
            "faz_assistencia": lead.get("faz_assistencia", ""),
            "score_avgestao": _safe_int(lead.get("score_avgestao", "0")),
            "motivos_score": lead.get("motivos_score", ""),
            "mensagem_whatsapp": lead.get("mensagem_whatsapp", ""),
            "link_whatsapp": lead.get("link_whatsapp", ""),
            "avaliacao": _safe_float(lead.get("avaliacao", "0")),
            "num_avaliacoes": _safe_int(lead.get("num_avaliacoes", "0")),
        }
        # Remove Nones/vazios para campos opcionais
        payload = {k: v for k, v in payload.items() if v is not None and v != ""}
        sb.table("leads").insert(payload).execute()
        return True
    except Exception as e:
        logger.warning("Erro ao inserir lead %s: %s", lead.get("nome", "")[:30], e)
        return False


def _safe_int(val):
    try:
        return int(float(str(val).replace(",", ".")))
    except (ValueError, TypeError):
        return 0


def _safe_float(val):
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _mostrar_dry_run(resultado: dict, existentes: dict, amostra: int = 5) -> None:
    """Exibe relatorio de dry-run."""
    print("\n" + "=" * 60)
    print("  DRY-RUN — Importacao de Leads")
    print("=" * 60)
    print(f"  Produto: {resultado['produto']}")
    print(f"  Grupo: {resultado['grupo']}")
    print(f"  Origem: {resultado['origem']}")
    print(f"  Total lido do ZIP/XLSX: {resultado['total_lido']}")
    print(f"  Com telefone: {resultado['com_telefone']}")
    print(f"  Sem telefone: {resultado['sem_telefone']}")
    print(f"  Telefone valido: {resultado['telefone_valido']}")
    print(f"  Telefone invalido: {resultado['telefone_invalido']}")
    print(f"  Duplicados internos: {resultado['duplicados_internos']}")
    print(f"  Unicos validos: {resultado['unicos']}")

    ja_existentes = sum(1 for t in resultado['validos'] if t['telefone_normalizado'] in existentes)
    protegidos = sum(1 for t in resultado['validos']
                     if t['telefone_normalizado'] in existentes
                     and existentes[t['telefone_normalizado']].get('status') in ('abordado', 'sent', 'confirmed_from_whatsapp', 'interessado', 'convertido'))
    novos = resultado['unicos'] - len([t for t in resultado['validos'] if t['telefone_normalizado'] in existentes])

    print(f"  Ja existentes no Supabase: {ja_existentes}")
    print(f"    (protegidos — status nao 'novo'): {protegidos}")
    print(f"  Novos que seriam inseridos: {novos}")

    print(f"\n  Por subnicho:")
    for k, v in resultado['por_subnicho'].most_common():
        print(f"    {k}: {v}")

    print(f"\n  Por cidade (top 10):")
    for k, v in resultado['por_cidade'].most_common(10):
        print(f"    {k}: {v}")

    print(f"\n  Amostra sanitizada ({min(amostra, len(resultado['validos']))} leads):")
    for lead in resultado['validos'][:amostra]:
        t = lead.get('telefone_normalizado', '')
        masked = t[:4] + "****" + t[-4:] if len(t) >= 8 else "****"
        nome = lead.get('nome', '?')[:35]
        # Sanitizar caracteres nao-imprimiveis
        nome = nome.encode('ascii', errors='replace').decode('ascii').replace('?', '?')
        cidade = lead.get('cidade', '?').encode('ascii', errors='replace').decode('ascii').replace('?', '?')
        print(f"    {nome:35s} | {masked:14s} | {lead.get('subnicho', '?'):15s} | {cidade}")

    print(f"\n  Comando para importacao real:")
    print(f"  python campanha_whatsapp.py import-leads --from-zip <ZIP> --produto {resultado['produto']} --grupo {resultado['grupo']} --confirm")
    print("=" * 60)
    print("  ZERO ESCRITA — dry-run concluido.")


def _executar_importacao(resultado: dict, existentes: dict) -> dict:
    """Executa importacao real no Supabase."""
    sb = _get_supabase_client()
    inseridos = 0
    erros = 0
    pulados = 0

    for lead in resultado["validos"]:
        tel_norm = lead["telefone_normalizado"]
        if tel_norm in existentes:
            existente = existentes[tel_norm]
            status_existente = existente.get("status", "")
            if status_existente in ("abordado", "sent", "confirmed_from_whatsapp", "interessado", "convertido"):
                logger.info("Pulando %s (status protegido: %s)", tel_norm[:4] + "****" + tel_norm[-4:], status_existente)
                pulados += 1
                continue
            # Se existente com status novo/pronto, pular tambem (ja existe)
            logger.info("Pulando %s (ja existente)", tel_norm[:4] + "****" + tel_norm[-4:])
            pulados += 1
            continue

        if _inserir_lead(sb, lead):
            inseridos += 1
        else:
            erros += 1

    return {"inseridos": inseridos, "erros": erros, "pulados": pulados}


def importar_leads_zip(zip_path: str, produto: str = "avgestao", grupo: str = "assistencias",
                        origem: str = "", dry_run: bool = True, confirm: bool = False) -> int:
    """
    Fluxo completo de importacao de leads ZIP/XLSX.

    Args:
        zip_path: Caminho para ZIP ou XLSX.
        produto: Valor do campo produto (default: avgestao).
        grupo: Valor do campo grupo (default: assistencias).
        origem: Valor do campo origem.
        dry_run: Se True, apenas analisa sem escrever.
        confirm: Se True e dry_run=False, executa escrita.

    Returns:
        0 se sucesso, 1 se erro.
    """
    if openpyxl is None:
        logger.error("openpyxl e necessario. Instale com: pip install openpyxl")
        return 1

    # Determinar origem automatica
    if not origem:
        fname = Path(zip_path).stem
        origem = f"zip_{fname}"

    # Ler XLSX
    try:
        if zip_path.endswith(".zip"):
            xlsx_data = _extrair_xlsx_do_zip(zip_path)
        else:
            xlsx_data = open(zip_path, "rb")
        leads = _ler_xlsx_para_leads(io.BytesIO(xlsx_data.read() if hasattr(xlsx_data, 'read') else xlsx_data))
    except Exception as e:
        logger.error("Erro ao ler arquivo: %s", e)
        return 1

    # Classificar
    resultado = _classificar_leads(leads, produto, grupo, origem)

    # Dry-run: analisar sem consultar Supabase
    if dry_run or not confirm:
        _mostrar_dry_run(resultado, {}, amostra=5)
        return 0

    # Consultar existentes (apenas em modo real)
    todos_tels = [l["telefone_normalizado"] for l in resultado["validos"] if l["telefone_normalizado"]]
    existentes = {}
    if todos_tels:
        try:
            sb = _get_supabase_client()
            existentes = _consultar_existentes(sb, todos_tels)
        except Exception as e:
            if not confirm:
                logger.warning("Supabase indisponivel: %s. Abortando.", e)
                return 1
            raise

    # Executar
    res = _executar_importacao(resultado, existentes)
    print(f"\nImportacao concluida: {res['inseridos']} inseridos, {res['erros']} erros, {res['pulados']} pulados.")
    return 0 if res["erros"] == 0 else 1
