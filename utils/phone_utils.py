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

from __future__ import annotations

import hashlib
import re
from urllib.parse import quote


def _validar_ddd(digitos: str) -> bool:
    """Valida DDD brasileiro (11-99, exceto 00-09)."""
    if len(digitos) < 2:
        return False
    ddd = digitos[:2]
    return bool(re.match(r"^(1[1-9]|[2-9][0-9])$", ddd))


def normalizar_telefone_br(valor: str) -> str | None:
    """
    Normaliza um telefone brasileiro para o formato internacional canônico.

    Regras:
    - Remove espaços, parênteses, traços, pontos e símbolos
    - Mantém apenas números
    - Remove prefixo 00 (internacional)
    - Se já começa com 55 e tem 12 ou 13 dígitos, valida DDD e retorna
    - Remove zero inicial (ex: 021...)
    - Se tem 11 dígitos (celular com DDD), prependa 55
    - Se tem 10 dígitos (fixo com DDD), prependa 55
    - Valida DDD (11-99)
    - Qualquer outro caso, retorna None
    """
    if not valor:
        return None

    numeros = re.sub(r"\D", "", str(valor))
    if not numeros:
        return None

    if numeros.startswith("00"):
        numeros = numeros[2:]

    if numeros.startswith("55") and len(numeros) in (12, 13):
        if _validar_ddd(numeros[2:4]):
            return numeros
        return None

    if numeros.startswith("0"):
        numeros = numeros[1:]

    if len(numeros) == 11:
        if _validar_ddd(numeros):
            return "55" + numeros
        return None

    if len(numeros) == 10:
        if _validar_ddd(numeros):
            return "55" + numeros
        return None

    return None


def canonical_phone_hash(phone: str | None) -> str:
    """
    Hash canônico de telefone.

    Fluxo obrigatório:
    telefone bruto -> normalização brasileira canônica -> somente dígitos
    -> formato único definido -> SHA-256 UTF-8.
    """
    phone_norm = normalizar_telefone_br(phone or "")
    if not phone_norm:
        return ""
    return hashlib.sha256(phone_norm.encode("utf-8")).hexdigest()


def hash_telefone_canonico(telefone_canonico: str | None) -> str:
    """Compatibilidade retroativa: assume telefone já normalizado."""
    if not telefone_canonico:
        return ""
    return hashlib.sha256(str(telefone_canonico).encode("utf-8")).hexdigest()


def variantes_busca_telefone(tel: str) -> list[str]:
    """
    Gera UMA única variante nacional brasileira para busca no WhatsApp Web.

    Regras:
    - Remove código do país 55
    - Remove +, espaços, parênteses e hífens
    - Celular: DDD + 9 dígitos = 11 dígitos
    - Fixo: DDD + 8 dígitos = 10 dígitos
    - Telefone inválido é rejeitado (lista vazia)
    - Não gera variante internacional
    - Não gera variante sem nono dígito
    - Não gera formatos alternativos
    """
    if not tel or not tel.startswith("55") or len(tel) < 12:
        return []

    ddd_numero = tel[2:]
    if len(ddd_numero) not in (10, 11):
        return []
    if not _validar_ddd(ddd_numero):
        return []
    return [ddd_numero]


def gerar_link_whatsapp(telefone_normalizado: str, mensagem: str = "") -> str:
    """
    Gera um link wa.me para abrir o WhatsApp com mensagem preenchida.

    NÃO envia mensagens automaticamente. Apenas gera o link para envio manual.
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
    """
    tel = lead.get("whatsapp", "") or lead.get("telefone", "") or ""
    return normalizar_telefone_br(tel)
