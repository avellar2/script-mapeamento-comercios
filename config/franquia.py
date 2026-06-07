"""
Deteccao estruturada de franquias e redes grandes.
Retorna confianca e motivos, ao inves de simples booleano.

Usado para:
- Penalizar score (alta: -30, media: -15, baixa: 0)
- Excluir de campanhas premium
- Classificar tipo_cliente
"""

import re
from dataclasses import dataclass, field


@dataclass
class ResultadoFranquia:
    """Resultado da analise de franquia."""
    possivel_franquia: bool
    nivel_confianca: str       # "alta" | "media" | "baixa"
    motivos: list[str]         # Explicacoes da deteccao
    tipo_cliente: str          # "possivel_franquia" | "rede_grande" | derivado


# ═══════════════════════════════════════════════════════════════
# LISTA DE MARCAS CONHECIDAS
# ═══════════════════════════════════════════════════════════════

# (padrao, nome_amigavel, confianca_padrao)
MARCAS_CONHECIDAS = {
    # Fast food
    "mcdonald": ("McDonald's", "alta"),
    "burger king": ("Burger King", "alta"),
    "subway": ("Subway", "alta"),
    "habib": ("Habib's", "alta"),
    "bob's": ("Bob's", "alta"),
    "kfc": ("KFC", "alta"),
    "pizza hut": ("Pizza Hut", "alta"),
    "domino": ("Domino's", "alta"),
    "starbucks": ("Starbucks", "alta"),
    "giraffas": ("Giraffas", "alta"),
    "spoleto": ("Spoleto", "alta"),
    "outback": ("Outback", "alta"),
    "applebee": ("Applebee's", "alta"),
    "wendy": ("Wendy's", "alta"),
    "taco bell": ("Taco Bell", "alta"),
    "baskin robbins": ("Baskin Robbins", "alta"),
    "cold stone": ("Cold Stone", "alta"),
    "madero": ("Madero", "alta"),
    # Varejo
    "pao de acucar": ("Pao de Acucar", "alta"),
    "extra hiper": ("Extra Hiper", "alta"),
    "carrefour": ("Carrefour", "alta"),
    "atacadao": ("Atacadao", "alta"),
    "big ": ("BIG", "alta"),
    "magazine luiza": ("Magazine Luiza", "alta"),
    "americanas": ("Americanas", "alta"),
    "casas bahia": ("Casas Bahia", "alta"),
    "pontofrio": ("Ponto Frio", "alta"),
    "renner": ("Renner", "alta"),
    "riachuelo": ("Riachuelo", "alta"),
    "c&a": ("C&A", "alta"),
    "marisa": ("Marisa", "alta"),
    "arezzo": ("Arezzo", "alta"),
    "track&field": ("Track&Field", "alta"),
    "vivolo": ("Vivolo", "alta"),
    # Fitness
    "smartfit": ("Smart Fit", "alta"),
    "smart fit": ("Smart Fit", "alta"),
    "bluefit": ("Bluefit", "alta"),
    "bodytech": ("Bodytech", "alta"),
    "formula academia": ("Formula Academia", "alta"),
    # Saude / Estetica
    "odontoprev": ("OdontoPrev", "alta"),
    "espaçolaser": ("Espacolaser", "alta"),
    "espacolaser": ("Espacolaser", "alta"),
    "odontocompany": ("OdontoCompany", "alta"),
    "oral sin": ("Oral Sin", "alta"),
    "sorridents": ("Sorridents", "alta"),
    "sobrancelhas design": ("Sobrancelhas Design", "alta"),
    # Pet
    "petz": ("Petz", "alta"),
    "cobasi": ("Cobasi", "alta"),
    # Educacao
    "cna": ("CNA", "alta"),
    "wizard": ("Wizard", "alta"),
    "fisk": ("Fisk", "alta"),
    "microlins": ("Microlins", "alta"),
    "kumon": ("Kumon", "alta"),
    # Beauty / Cosmeticos
    "o boticário": ("O Boticario", "alta"),
    "o boticario": ("O Boticario", "alta"),
    "natura": ("Natura", "alta"),
    "quem disse berenice": ("Quem Disse Berenice", "alta"),
    "cacau show": ("Cacau Show", "alta"),
    # Farmacia
    "drogasil": ("Drogasil", "alta"),
    "drogaria pacheco": ("Drogaria Pacheco", "alta"),
    "raia": ("Raia", "media"),
    "pague menos": ("Pague Menos", "alta"),
    # Hotel
    "ibis": ("Ibis", "alta"),
    "mercure": ("Mercure", "alta"),
    "novotel": ("Novotel", "alta"),
    # Imobiliaria
    "lopes": ("Lopes", "media"),
    "cyrela": ("Cyrela", "media"),
    # Transporte
    "localiza": ("Localiza", "alta"),
    "movida": ("Movida", "alta"),
    "unidas": ("Unidas", "alta"),
    # Delivery
    "ifood": ("iFood", "media"),
    "rappi": ("Rappi", "media"),
    "ubereats": ("UberEats", "media"),
    # Cartao / Viagem
    "cartão de todos": ("Cartao de Todos", "media"),
    "cvc": ("CVC", "alta"),
    # Moveis / Casa
    "ortobom": ("Ortobom", "alta"),
    # Churrascaria redes
    "fogo de chao": ("Fogo de Chao", "alta"),
    "porcao": ("Porcao", "alta"),
}


# ═══════════════════════════════════════════════════════════════
# PATTERNS DE ENDERECO / NOME
# ═══════════════════════════════════════════════════════════════

PADROES_FILIAIS = [
    (r"unidade\s+\w+", "endereco com 'Unidade'"),
    (r"filial\s+\d+", "endereco com 'Filial'"),
    (r"loja\s+\d+", "endereco com 'Loja N'"),
    (r"\bunit\s+\w+", "endereco com 'Unit'"),
]

SHOPPINGS_CONHECIDOS = [
    "barra shopping", "barra shopping shopping",
    "norteshopping", "norte shopping",
    "villagemall", "village mall",
    "parkjacarepaguá", "park jacarepaguá",
    "riosul", "rio sul",
    "shopping tijuca", "shopping da tijuca",
    "shopping leblon", "leblon shopping",
    "shopping iguatemi",
    "bangu shopping",
    "shopping meier", "méier shopping",
    "carioca shopping",
    "shopping grande rio",
    "boulevard shopping",
    "penha shopping",
    "nova america",
    "sao goncala shopping",
    "center shopping",
    "riverside shopping",
    "recreio shopping",
    "shopping downtown",
    "rio design barra", "rio design",
    "gavea shopping",
]

PADROES_NOME_FILIAL = [
    (r"\bunidade\b", "nome com 'Unidade'"),
    (r"\bfilial\b", "nome com 'Filial'"),
    (r"\bshopping\b", "nome com 'Shopping'"),
    (r"\bloja\s+\d", "nome com 'Loja N'"),
]


def detectar_franquia(
    nome: str,
    endereco: str = "",
    site: str = "",
    instagram: str = "",
) -> ResultadoFranquia:
    """
    Detecta possivel franquia/rede grande com confianca e motivos.

    Retorna ResultadoFranquia com:
    - possivel_franquia: bool
    - nivel_confianca: "alta" | "media" | "baixa"
    - motivos: lista de razoes
    - tipo_cliente: classificacao do cliente
    """
    motivos = []
    nivel = "baixa"
    nome_lower = nome.lower() if nome else ""
    end_lower = endereco.lower() if endereco else ""
    site_lower = site.lower() if site else ""
    ig_lower = instagram.lower() if instagram else ""

    # 1) Verificar marcas conhecidas
    for pattern, (marca, conf) in MARCAS_CONHECIDAS.items():
        if pattern in nome_lower:
            motivos.append(f"nome contem marca '{marca}'")
            if conf == "alta":
                nivel = "alta"
            elif conf == "media" and nivel == "baixa":
                nivel = "media"

    # 2) Verificar shoppings no endereco ou nome
    for shopping in SHOPPINGS_CONHECIDOS:
        if shopping in end_lower:
            motivos.append(f"endereco no shopping '{shopping.title()}'")
            if nivel == "baixa":
                nivel = "media"
        if shopping in nome_lower:
            motivos.append(f"nome referencia shopping '{shopping.title()}'")
            if nivel == "baixa":
                nivel = "media"

    # 3) Padroes de endereco (Unidade, Filial, etc)
    for pattern, descricao in PADROES_FILIAIS:
        if re.search(pattern, end_lower):
            motivos.append(descricao)
            if nivel == "baixa":
                nivel = "media"

    # 4) Padroes no nome (Unidade, Filial, Shopping)
    for pattern, descricao in PADROES_NOME_FILIAL:
        if re.search(pattern, nome_lower):
            motivos.append(descricao)
            if nivel == "baixa":
                nivel = "media"

    # 5) Site corporativo (heuristica)
    if site_lower:
        padroes_corp = ["/unidades", "/franquias", "/lojas", "/nossa-historia"]
        for p in padroes_corp:
            if p in site_lower:
                motivos.append(f"site com pagina '{p}'")
                if nivel == "baixa":
                    nivel = "media"

    # 6) Instagram corporativo
    if ig_lower:
        termos_rede = ["franquia", "franqueado", "unidades em todo", "todo o brasil", "seja um franqueado"]
        for t in termos_rede:
            if t in ig_lower:
                motivos.append(f"instagram com '{t}'")
                if nivel == "baixa":
                    nivel = "media"

    # Classificar tipo_cliente
    if nivel == "alta" and len(motivos) >= 2:
        tipo = "rede_grande"
    elif motivos:
        tipo = "possivel_franquia"
    else:
        tipo = ""

    return ResultadoFranquia(
        possivel_franquia=len(motivos) > 0,
        nivel_confianca=nivel,
        motivos=motivos,
        tipo_cliente=tipo,
    )


def classificar_tipo_cliente(lead: dict) -> str:
    """
    Classifica o tipo de cliente baseado nos dados do lead.

    Retorna: pequeno_negocio | profissional_liberal | clinica_local |
             loja_local | possivel_franquia | rede_grande | indefinido
    """
    nome = (lead.get("nome") or "").lower()
    categoria = (lead.get("categoria") or lead.get("nicho") or "").lower()

    # Verificar franquia primeiro
    resultado = detectar_franquia(
        lead.get("nome", ""),
        lead.get("endereco", ""),
        lead.get("url_site", ""),
        lead.get("instagram", ""),
    )
    if resultado.tipo_cliente in ("rede_grande", "possivel_franquia"):
        return resultado.tipo_cliente

    # Profissional liberal
    profissionais = [
        "advogado", "psicologo", "psicólogo", "nutricionista",
        "arquiteto", "fotógrafo", "fotografo", "personal trainer",
        "designer de interiores", "contador",
    ]
    if any(p in categoria for p in profissionais):
        return "profissional_liberal"

    # Clinica
    clinicas = [
        "clínica", "clinica", "estética", "estetica", "dentista",
        "harmonização", "harmonizacao", "fisioterapeuta", "pilates",
        "spa", "consultório", "consultorio",
    ]
    if any(c in categoria for c in clinicas):
        return "clinica_local"

    # Loja
    lojas = [
        "loja", "pet shop", "floricultura", "ótica", "otica",
        "joalheria", "papelaria", "supermercado", "farmácia", "farmacia",
    ]
    if any(l in categoria for l in lojas):
        return "loja_local"

    # Academia / escola
    if any(t in categoria for t in ["academia", "escola", "curso", "auto escola"]):
        return "pequeno_negocio"

    # Restaurante / bar
    if any(t in categoria for t in ["restaurante", "bar", "pizzaria", "lanchonete", "padaria", "confeitaria"]):
        return "pequeno_negocio"

    return "indefinido"


def score_penalidade_franquia(nivel_confianca: str) -> int:
    """Retorna penalidade de score baseada na confianca de franquia."""
    if nivel_confianca == "alta":
        return 30
    elif nivel_confianca == "media":
        return 15
    return 0