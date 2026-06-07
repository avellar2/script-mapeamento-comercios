#!/usr/bin/env python3
"""
Normalização de telefone brasileiro e geração de link WhatsApp.

Consolida as implementações duplicadas em:
- prospectar_leads.py (limpar_telefone)
- gerar_lista_diaria.py (extrair_numero)
- gerar_painel_prospeccao.py (gerar_link_whatsapp)
- campanha_diaria.py (gerar_link_whatsapp)

Uso:
    from utils.phone_utils import normalizar_telefone_br, gerar_link_whatsapp

    tel = normalizar_telefone_br("21999999999")
    # => "5521999999999"

    link = gerar_link_whatsapp(tel, "Olá, tudo bem?")
    # => "https://wa.me/5521999999999?text=Ol%C3%A1%2C%20tudo%20bem%3F"
"""

import re
from urllib.parse import quote


def normalizar_telefone_br(valor: str) -> str | None:
    """
    Normaliza um telefone brasileiro para o formato internacional.

    Regras:
    - Remove espaços, parênteses, traços, pontos e símbolos
    - Mantém apenas números
    - Se já começa com 55 e tem >= 12 dígitos, mantém
    - Remove zero inicial
    - Se tem 11 dígitos (celular com DDD), prependa 55
    - Se tem 10 dígitos (fixo com DDD), prependa 55
    - Qualquer outro caso, retorna None

    Exemplos:
    >>> normalizar_telefone_br("21999999999")
    '5521999999999'
    >>> normalizar_telefone_br("(21) 99999-9999")
    '5521999999999'
    >>> normalizar_telefone_br("5521999999999")
    '5521999999999'
    >>> normalizar_telefone_br("021999999999")
    '5521999999999'
    >>> normalizar_telefone_br("999999999")
    None  # sem DDD
    """
    if not valor:
        return None

    # Remover tudo que não é dígito
    numeros = re.sub(r"\D", "", str(valor))

    if not numeros:
        return None

    # Já tem código do país (55) e comprimento válido
    if numeros.startswith("55") and len(numeros) >= 12:
        return numeros

    # Remover zero inicial (ex: 021999999999)
    if numeros.startswith("0"):
        numeros = numeros[1:]

    # Celular com DDD (11 dígitos): 21999999999
    if len(numeros) == 11:
        return "55" + numeros

    # Fixo com DDD (10 dígitos): 2133333333
    if len(numeros) == 10:
        return "55" + numeros

    # Número sem DDD ou formato inválido
    return None


def gerar_link_whatsapp(telefone_normalizado: str, mensagem: str = "") -> str:
    """
    Gera um link wa.me para abrir o WhatsApp com mensagem preenchida.

    NÃO envia mensagens automaticamente. Apenas gera o link para envio manual.

    Args:
        telefone_normalizado: Telefone no formato internacional (ex: 5521999999999)
        mensagem: Texto da mensagem (opcional)

    Returns:
        Link wa.me com ou sem mensagem preenchida.
        String vazia se telefone_normalizado estiver vazio.
    """
    if not telefone_normalizado:
        return ""

    if mensagem:
        msg_encoded = quote(mensagem)
        return f"https://wa.me/{telefone_normalizado}?text={msg_encoded}"

    return f"https://wa.me/{telefone_normalizado}"


def extrair_telefone_lead(lead: dict) -> str | None:
    """
    Extrai e normaliza o telefone de um lead (dict).

    Prioriza o campo 'whatsapp' sobre 'telefone'.

    Args:
        lead: Dicionário com dados do lead

    Returns:
        Telefone normalizado ou None se inválido
    """
    # Priorizar whatsapp sobre telefone
    tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""
    return normalizar_telefone_br(tel)