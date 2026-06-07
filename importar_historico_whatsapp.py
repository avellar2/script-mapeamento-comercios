#!/usr/bin/env python3
"""
Importar histórico de abordagens do WhatsApp para o Supabase.

Lê um CSV com colunas: telefone,status,observacao
Atualiza leads existentes ou cria leads mínimos para números não encontrados.

Uso:
    python importar_historico_whatsapp.py
    python importar_historico_whatsapp.py --arquivo caminho/do/arquivo.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path=None):
        env_path = Path(path) if path else Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

sys.path.insert(0, str(Path(__file__).parent))
from utils.phone_utils import normalizar_telefone_br

# Status que NUNCA devem ser regredidos
STATUS_TERMINAIS = {"convertido", "perdido"}


def processar_historico(caminho_csv):
    """Processa arquivo CSV de histórico do WhatsApp."""
    if not HAS_SUPABASE:
        print("❌ Pacote 'supabase' não instalado. Instale com: pip install supabase")
        return 0

    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL e SUPABASE_ANON_KEY não encontrados no .env")
        return 0

    try:
        sb = create_client(supabase_url, supabase_key)
        print(f"✅ Conectado ao Supabase: {supabase_url}")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Supabase: {e}")
        return 0

    # Ler CSV
    caminho = Path(caminho_csv)
    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho_csv}")
        return 0

    linhas = []
    with open(caminho, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            linhas.append(row)

    print(f"📊 Linhas lidas do CSV: {len(linhas)}")

    # Processar cada linha
    atualizados = 0
    criados = 0
    pulados_terminal = 0
    pulados_sem_tel = 0
    erros = 0

    agora = datetime.utcnow().isoformat()
    followup = (datetime.utcnow() + timedelta(days=7)).isoformat()

    for i, row in enumerate(linhas, 1):
        tel_raw = row.get("telefone", "").strip()
        obs = row.get("observacao", "").strip()

        tel_norm = normalizar_telefone_br(tel_raw)
        if not tel_norm:
            pulados_sem_tel += 1
            continue

        # Buscar lead no Supabase
        try:
            result = sb.table("leads").select("id,status,ultimo_contato_em,proximo_followup_em").eq("telefone_normalizado", tel_norm).execute()

            if result.data:
                # Lead encontrado - atualizar
                lead = result.data[0]
                lead_id = lead["id"]
                status_atual = lead.get("status", "novo")

                if status_atual in STATUS_TERMINAIS:
                    pulados_terminal += 1
                    continue

                # Atualizar status para abordado
                update_data = {"status": "abordado"}

                # Preencher ultimo_contato_em apenas se vazio
                if not lead.get("ultimo_contato_em"):
                    update_data["ultimo_contato_em"] = agora

                # Preencher proximo_followup_em apenas se vazio
                if not lead.get("proximo_followup_em"):
                    update_data["proximo_followup_em"] = followup

                sb.table("leads").update(update_data).eq("id", lead_id).execute()

                # Criar interação
                sb.table("lead_interactions").insert({
                    "lead_id": lead_id,
                    "tipo": "primeira_abordagem_manual_antiga",
                    "canal": "whatsapp",
                    "observacao": obs or "Importado do histórico WhatsApp",
                }).execute()

                atualizados += 1
            else:
                # Lead não encontrado - criar mínimo
                novo_lead = {
                    "telefone": tel_raw,
                    "telefone_normalizado": tel_norm,
                    "nome": row.get("nome", "").strip() or f"Lead {tel_raw}",
                    "status": "abordado",
                    "origem": "historico_whatsapp",
                    "ultimo_contato_em": agora,
                    "proximo_followup_em": followup,
                }
                if obs:
                    novo_lead["observacoes"] = obs

                result = sb.table("leads").insert(novo_lead).execute()
                novo_id = result.data[0]["id"]

                # Criar interação
                sb.table("lead_interactions").insert({
                    "lead_id": novo_id,
                    "tipo": "primeira_abordagem_manual_antiga",
                    "canal": "whatsapp",
                    "observacao": obs or "Criado do histórico WhatsApp",
                }).execute()

                criados += 1

        except Exception as e:
            print(f"  ❌ Erro na linha {i} ({tel_raw}): {e}")
            erros += 1

        # Log de progresso a cada 50 linhas
        if i % 50 == 0:
            print(f"  ... processados {i}/{len(linhas)}")

    # Resumo
    print()
    print("=" * 60)
    print("📊 RESUMO DA IMPORTAÇÃO DE HISTÓRICO")
    print("=" * 60)
    print(f"  📄 Linhas lidas do CSV:       {len(linhas)}")
    print(f"  🔄 Leads atualizados:         {atualizados}")
    print(f"  🆕 Leads criados:             {criados}")
    print(f"  🔒 Pulados (status terminal): {pulados_terminal}")
    print(f"  ⚠️  Pulados (sem tel válido):  {pulados_sem_tel}")
    print(f"  ❌ Erros:                      {erros}")
    print("=" * 60)

    return atualizados + criados


def main():
    parser = argparse.ArgumentParser(description="Importar histórico WhatsApp para o Supabase")
    parser.add_argument("--arquivo", default="historico_whatsapp.csv",
                        help="Caminho do arquivo CSV (padrão: historico_whatsapp.csv)")
    args = parser.parse_args()

    print("=" * 60)
    print("📱 Importando histórico do WhatsApp")
    print("=" * 60)

    processar_historico(args.arquivo)


if __name__ == "__main__":
    main()