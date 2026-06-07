#!/usr/bin/env python3
"""
Relatorio Comparativo Regional
===============================
Compara metricas entre regioes Baixada e Rio Premium.

Uso:
    python gerar_relatorio_regional.py
    python gerar_relatorio_regional.py --regiao rio_premium
"""

import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Fix encoding no Windows
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Carrega .env
_dotenv = Path(__file__).resolve().parent / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv, override=True)

from config.regioes import resolve_regiao, RIO_PREMIUM, BAIXADA
from config.franquia import detectar_franquia, classificar_tipo_cliente


def _get_supabase():
    """Conecta ao Supabase."""
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None


def gerar_relatorio(regioes_keys=None):
    """Gera relatorio comparativo entre regioes."""
    sb = _get_supabase()
    if not sb:
        print("[X] Supabase nao configurado. Verifique .env")
        return

    if regioes_keys is None:
        regioes_keys = ["baixada", "rio_premium"]

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print("=" * 65)
    print(f"  RELATORIO REGIONAL DE PROSPECCAO - {agora}")
    print("=" * 65)

    # Buscar todos os leads
    result = sb.table("leads").select("*").limit(10000).execute()
    all_leads = result.data

    total_geral = len(all_leads)
    print(f"\n  Total de leads no banco: {total_geral}")
    print()

    for regiao_key in regioes_keys:
        regiao_config = BAIXADA if regiao_key == "baixada" else RIO_PREMIUM
        leads = [l for l in all_leads if (l.get("origem") or "") == regiao_key]

        # Contadores
        sem_site = [l for l in leads if not l.get("tem_site")]
        com_tel = [l for l in leads if l.get("telefone_normalizado")]
        com_whatsapp = [l for l in leads if l.get("link_whatsapp")]

        # Detectar franquias
        franquias = []
        franquia_alta = 0
        for l in leads:
            resultado = detectar_franquia(
                l.get("nome", ""),
                l.get("endereco", ""),
                l.get("url_site", ""),
                l.get("instagram", ""),
            )
            if resultado.possivel_franquia:
                franquias.append(l)
                if resultado.nivel_confianca == "alta":
                    franquia_alta += 1

        # Classificar tipos de cliente
        tipos = Counter()
        for l in leads:
            tipo = classificar_tipo_cliente(l)
            tipos[tipo] += 1

        # Top nichos
        nichos = Counter()
        for l in leads:
            nicho = l.get("nicho") or l.get("categoria") or "indefinido"
            nichos[nicho] += 1

        # Top cidades/bairros
        localidades = Counter()
        campo_local = "bairro" if regiao_key == "rio_premium" else "cidade"
        for l in leads:
            loc = l.get(campo_local) or "indefinido"
            localidades[loc] += 1

        # Score medio
        scores = [l.get("score", 0) for l in leads if l.get("score")]
        score_medio = sum(scores) / len(scores) if scores else 0

        # Status
        statuses = Counter()
        for l in leads:
            statuses[l.get("status", "indefinido")] += 1

        # Top 20 leads recomendados
        leads_ordenados = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)
        top_20 = leads_ordenados[:20]

        # Imprimir
        print("-" * 65)
        print(f"  REGIAO: {regiao_config.label} ({regiao_key})")
        print("-" * 65)
        print(f"  Total de leads:           {len(leads)}")
        print(f"  Sem site:                 {len(sem_site)} ({len(sem_site)*100//max(len(leads),1)}%)")
        print(f"  Com telefone normalizado: {len(com_tel)} ({len(com_tel)*100//max(len(leads),1)}%)")
        print(f"  Com link WhatsApp:        {len(com_whatsapp)} ({len(com_whatsapp)*100//max(len(leads),1)}%)")
        print(f"  Score medio:              {score_medio:.1f}")
        print()
        print(f"  Possiveis franquias:      {len(franquias)}")
        print(f"  Franquias conf. alta:     {franquia_alta}")
        print(f"  Leads sem franquia:        {len(leads) - len(franquias)}")
        print()
        print(f"  Status dos leads:")
        for status, count in statuses.most_common():
            print(f"    {status:25s} {count:4d} ({count*100//max(len(leads),1)}%)")
        print()
        print(f"  Tipo de cliente:")
        for tipo, count in tipos.most_common():
            print(f"    {tipo:25s} {count:4d}")
        print()
        print(f"  Top 10 nichos:")
        for nicho, count in nichos.most_common(10):
            print(f"    {nicho:30s} {count:4d}")
        print()
        print(f"  Top 10 {campo_local}:")
        for loc, count in localidades.most_common(10):
            print(f"    {loc:30s} {count:4d}")
        print()

        if top_20:
            print(f"  Top 20 Leads Recomendados:")
            print(f"  {'#':>3} {'Score':>5} {'Nome':30s} {'Nicho':20s} {'Local':20s}")
            print(f"  {'---':>3} {'-----':>5} {'----':30s} {'-----':20s} {'-----':20s}")
            for i, l in enumerate(top_20, 1):
                nome = (l.get("nome") or "")[:28]
                nicho = (l.get("nicho") or l.get("categoria") or "")[:18]
                loc = (l.get(campo_local) or "")[:18]
                score = l.get("score", 0)
                # Marcar franquia
                resultado = detectar_franquia(l.get("nome", ""), l.get("endereco", ""))
                flag = " [F]" if resultado.possivel_franquia else ""
                print(f"  {i:3d} {score:5d} {nome:30s} {nicho:20s} {loc:20s}{flag}")
        print()

    print("=" * 65)
    print("  Fim do relatorio")
    print("=" * 65)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Relatorio comparativo regional")
    parser.add_argument(
        "--regiao",
        choices=["baixada", "rio_premium", "todas"],
        default="todas",
        help="Regiao para o relatorio (padrao: todas)",
    )
    args = parser.parse_args()

    if args.regiao == "todas":
        gerar_relatorio(["baixada", "rio_premium"])
    else:
        gerar_relatorio([args.regiao])


if __name__ == "__main__":
    main()