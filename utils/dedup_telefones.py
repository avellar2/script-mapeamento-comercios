#!/usr/bin/env python3
"""
Relatório de telefones legados divergentes.

Detecta leads cujo telefone_normalizado difere do canônico calculado,
ou que convergem para o mesmo canônico a partir de normalizações
divergentes.

NÃO faz backfill destrutivo. Apenas relata conflitos para revisão manual.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any

from utils.phone_utils import normalizar_telefone_br

logger = logging.getLogger(__name__)


def detectar_conflitos(
    leads: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Detecta conflitos de normalização em uma lista de leads.

    Para cada lead, calcula o canônico a partir de telefone/whatsapp
    e compara com o telefone_normalizado armazenado.

    Args:
        leads: Lista de dicts com 'id', 'telefone', 'whatsapp',
               'telefone_normalizado'

    Returns:
        Lista de conflitos encontrados, cada um com:
        - canonical: canônico calculado
        - leads: lista de leads que convergem para este canônico
        - divergentes: True se algum telefone_normalizado difere
    """
    # Agrupa por canônico calculado
    grupos: dict[str, list[dict[str, Any]]] = {}

    for lead in leads:
        tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""
        canonico = normalizar_telefone_br(tel)

        if canonico is None:
            continue

        if canonico not in grupos:
            grupos[canonico] = []

        grupos[canonico].append({
            "id": str(lead.get("id", "")),
            "telefone": lead.get("telefone", ""),
            "whatsapp": lead.get("whatsapp", ""),
            "telefone_normalizado": lead.get("telefone_normalizado", ""),
            "nome": lead.get("nome", ""),
            "status": lead.get("status", ""),
        })

    # Filtra grupos com conflitos
    conflitos = []
    for canonico, leads_grupo in sorted(grupos.items()):
        normalizados = set(
            l["telefone_normalizado"] for l in leads_grupo
            if l["telefone_normalizado"]
        )
        divergentes = len(normalizados) > 1 or (
            len(normalizados) == 1 and canonico not in normalizados
        )
        tem_nulo = any(
            not l["telefone_normalizado"] for l in leads_grupo
        )

        if divergentes or tem_nulo or len(leads_grupo) > 1:
            conflitos.append({
                "canonical": canonico,
                "total_leads": len(leads_grupo),
                "divergentes": divergentes,
                "algum_nulo": tem_nulo,
                "leads": leads_grupo,
            })

    return conflitos


def gerar_relatorio(
    conflitos: list[dict[str, Any]],
    caminho: str | Path,
    mascarar: bool = True
) -> None:
    """
    Gera relatório CSV de conflitos com telefones mascarados.

    Args:
        conflitos: Lista de conflitos de detectar_conflitos()
        caminho: Caminho do arquivo CSV de saída
        mascarar: Se True, máscara os telefones (ex: 55219****9999)
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "canonical",
            "lead_id",
            "nome",
            "telefone",
            "whatsapp",
            "telefone_normalizado_armazenado",
            "divergente",
        ])

        for conflito in conflitos:
            canon = _mascarar(conflito["canonical"]) if mascarar else conflito["canonical"]
            for lead in conflito["leads"]:
                tel = _mascarar(lead["telefone"]) if mascarar else lead["telefone"]
                wa = _mascarar(lead["whatsapp"]) if mascarar else lead["whatsapp"]
                tn = _mascarar(lead["telefone_normalizado"]) if mascarar else lead["telefone_normalizado"]
                divergente = (
                    lead["telefone_normalizado"]
                    and lead["telefone_normalizado"] != conflito["canonical"]
                )

                writer.writerow([
                    canon,
                    lead["id"],
                    lead["nome"],
                    tel,
                    wa,
                    tn,
                    "SIM" if divergente else "nao",
                ])

    logger.info("Relatório de conflitos salvo em: %s", caminho)


def _mascarar(telefone: str) -> str:
    """Mascara telefone mantendo DDD e últimos 4 dígitos."""
    if not telefone:
        return ""
    digitos = "".join(c for c in str(telefone) if c.isdigit())
    if len(digitos) <= 6:
        return digitos[:2] + "****" + digitos[-2:]
    return digitos[:4] + "****" + digitos[-4:]


def gerar_json_resumo(
    conflitos: list[dict[str, Any]],
    caminho: str | Path
) -> None:
    """
    Gera JSON de resumo dos conflitos (sem dados sensíveis).

    Args:
        conflitos: Lista de conflitos
        caminho: Caminho do arquivo JSON
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    resumo = {
        "total_conflitos": len(conflitos),
        "total_leads_afetados": sum(c["total_leads"] for c in conflitos),
        "conflitos": [
            {
                "canonical_mascarado": _mascarar(c["canonical"]),
                "total_leads": c["total_leads"],
                "divergentes": c["divergentes"],
                "algum_nulo": c["algum_nulo"],
            }
            for c in conflitos
        ],
    }

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)

    logger.info("Resumo JSON salvo em: %s", caminho)
