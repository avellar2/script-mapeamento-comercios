#!/usr/bin/env python3
"""
Fingerprint de mensagens para reconciliação de campanhas no WhatsApp.

Gera um hash estável do texto normalizado da mensagem e compara com
as frases-chave estáveis do template da campanha.

Não armazena o texto completo da conversa — apenas o hash e o booleano
de correspondência.
"""

import hashlib
import re
import unicodedata

from utils.campaign_key import extrair_partes


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para comparação: lowercase, sem acentos, sem pontuação,
    whitespace colapsado.

    Args:
        texto: Texto bruto

    Returns:
        Texto normalizado
    """
    if not texto:
        return ""

    # Unicode normalize (decompõe acentos)
    texto = unicodedata.normalize("NFKD", str(texto))
    # Remove acentos (mantém apenas ASCII)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    texto = texto.lower()
    # Remove pontuação (mantém letras, números, espaços)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    # Colapsa whitespace
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto


def fingerprint_mensagem(texto: str) -> str:
    """
    Gera um hash SHA-256 do texto normalizado da mensagem.

    Args:
        texto: Texto da mensagem

    Returns:
        Hash hexadecimal do texto normalizado
    """
    normalizado = normalizar_texto(texto)
    if not normalizado:
        return ""
    return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def chaves_estaveis_da_campanha(campaign_key: str) -> list[str]:
    """
    Retorna as frases-chave estáveis do template da campanha.

    Essas frases são extraídas do template de mensagem usado na campanha
    e servem para identificar se uma mensagem de saída corresponde à
    abordagem atual.

    Args:
        campaign_key: A chave da campanha

    Returns:
        Lista de frases normalizadas que identificam a campanha
    """
    partes = extrair_partes(campaign_key)
    if partes is None:
        return []

    produto = partes["produto"]
    grupo = partes["grupo"]
    tipo = partes["tipo_abordagem"]

    # Frases-chave estáveis do template AVGESTÃO assistências
    # (extraídas de config/mensagens.py e config/avgestao.py)
    if produto == "avgestao" and grupo == "assistencias":
        if tipo == "primeiro_contato":
            return [
                "ola tudo bem",
                "tudo bem",
                "bom dia",
                "boa tarde",
                "avgestao",
                "faz assistencia",
                "assistencia tecnica",
                "precisa de",
                "servico de",
                "conheco seu trabalho",
            ]
        if tipo == "follow_up":
            return [
                "ola tudo bem",
                "tudo bem",
                "bom dia",
                "boa tarde",
                "avgestao",
                "falei com voce",
                "semana passada",
                "entrar em contato",
                "ainda tem interesse",
            ]

    # Fallback: frases genéricas
    return [
        "ola",
        "tudo bem",
        "bom dia",
        "boa tarde",
        produto,
        grupo,
    ]


def corresponde_campanha(
    texto_mensagem: str,
    campaign_key: str,
    limiar: float = 0.3
) -> bool:
    """
    Verifica se uma mensagem de saída corresponde à campanha.

    Compara o texto normalizado da mensagem com as frases-chave estáveis
    da campanha. Retorna True se uma proporção suficiente das frases
    for encontrada.

    Args:
        texto_mensagem: Texto da mensagem encontrada no WhatsApp
        campaign_key: Chave da campanha para comparar
        limiar: Proporção mínima de frases que devem ser encontradas (0.0 a 1.0)

    Returns:
        True se a mensagem corresponde à campanha, False caso contrário
    """
    if not texto_mensagem or not campaign_key:
        return False

    texto_norm = normalizar_texto(texto_mensagem)
    if not texto_norm:
        return False

    frases = chaves_estaveis_da_campanha(campaign_key)
    if not frases:
        return False

    # Conta quantas frases-chave aparecem no texto
    encontradas = sum(1 for frase in frases if frase in texto_norm)
    proporcao = encontradas / len(frases)

    return proporcao >= limiar
