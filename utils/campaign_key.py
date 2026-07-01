#!/usr/bin/env python3
"""
Geração e validação de campaign_key para proteção contra duplicidade.

Formato: <produto>:<grupo>:<tipo_abordagem>:<versao>

Exemplos:
    avgestao:assistencias:primeiro_contato:v1
    avgestao:assistencias:follow_up:v1
    avgestao:refrigeracao:primeiro_contato:v2

Regras:
    - Não incluir cidade, estado, run_id, campaigns.id
    - Não incluir subnicho quando todos os subnichos recebem a mesma abordagem
    - Não armazenar como propriedade fixa do lead
    - Armazenar apenas em lead_outreach
    - Follow-up usa chave diferente (follow_up)
    - Abordagem alterada incrementa versão
"""

import re

# Constantes das campanhas atuais
PRIMEIRO_CONTATO_V1 = "avgestao:assistencias:primeiro_contato:v1"
FOLLOW_UP_V1 = "avgestao:assistencias:follow_up:v1"

# Padrão de validação: produto:grupo:tipo_abordagem:versao
# Cada segmento: letras minúsculas, números e underscore
_CAMPAIGN_KEY_PATTERN = re.compile(r'^[a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+:v[0-9]+$')

# Tipos de abordagem válidos
_TIPOS_ABORDAGEM_VALIDOS = {"primeiro_contato", "follow_up"}


def gerar_campaign_key(
    produto: str,
    grupo: str,
    tipo_abordagem: str,
    versao: str = "v1"
) -> str:
    """
    Gera uma campaign_key no formato canônico.

    Args:
        produto: Nome do produto (ex: 'avgestao')
        grupo: Nome do grupo (ex: 'assistencias')
        tipo_abordagem: Tipo de abordagem (ex: 'primeiro_contato', 'follow_up')
        versao: Versão da abordagem (ex: 'v1', 'v2')

    Returns:
        campaign_key no formato <produto>:<grupo>:<tipo_abordagem>:<versao>

    Raises:
        ValueError: Se algum parâmetro for inválido
    """
    if not produto or not re.match(r'^[a-z0-9_]+$', produto):
        raise ValueError(f"produto inválido: {produto!r}")
    if not grupo or not re.match(r'^[a-z0-9_]+$', grupo):
        raise ValueError(f"grupo inválido: {grupo!r}")
    if tipo_abordagem not in _TIPOS_ABORDAGEM_VALIDOS:
        raise ValueError(
            f"tipo_abordagem inválido: {tipo_abordagem!r}. "
            f"Válidos: {_TIPOS_ABORDAGEM_VALIDOS}"
        )
    if not re.match(r'^v[0-9]+$', versao):
        raise ValueError(f"versao inválida: {versao!r}")

    return f"{produto}:{grupo}:{tipo_abordagem}:{versao}"


def validar_campaign_key(chave: str) -> bool:
    """
    Valida se uma campaign_key está no formato correto.

    Args:
        chave: A chave a ser validada

    Returns:
        True se válida, False caso contrário
    """
    if not chave:
        return False
    return bool(_CAMPAIGN_KEY_PATTERN.match(chave))


def extrair_partes(chave: str) -> dict | None:
    """
    Extrai as partes de uma campaign_key.

    Args:
        chave: A campaign_key

    Returns:
        Dict com 'produto', 'grupo', 'tipo_abordagem', 'versao'
        ou None se inválida
    """
    if not validar_campaign_key(chave):
        return None

    partes = chave.split(":")
    return {
        "produto": partes[0],
        "grupo": partes[1],
        "tipo_abordagem": partes[2],
        "versao": partes[3],
    }


def interaction_type_from_campaign_key(chave: str) -> str | None:
    """
    Mapeia o tipo de abordagem da campaign_key para o enum de lead_interactions.

    Args:
        chave: A campaign_key

    Returns:
        'primeira_abordagem' para primeiro_contato
        'follow_up' para follow_up
        None para tipo desconhecido
    """
    partes = extrair_partes(chave)
    if partes is None:
        return None

    tipo = partes["tipo_abordagem"]
    if tipo == "primeiro_contato":
        return "primeira_abordagem"
    if tipo == "follow_up":
        return "follow_up"
    return None
