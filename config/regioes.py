"""
Configuracao centralizada de regioes de prospeccao.
Fonte unica de verdade para cidades, bairros, categorias, nichos, pesos e mensagens.

Substitui todas as listas hardcoded espalhadas nos scripts.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_BASE = BASE_DIR / "output"


@dataclass
class RegiaoConfig:
    """Configuracao completa de uma regiao de prospeccao."""
    key: str                         # "baixada" | "rio_premium"
    label: str                       # "Baixada Fluminense" | "Rio Premium"
    cidades: list[str]               # Para busca no Maps (ex: "Duque de Caxias, RJ")
    bairros: list[str]               # [] para baixada, 25 bairros para rio_premium
    categorias: list[str]            # Termos de busca Google Maps
    nichos_tier1: list[str]          # Prioridade para Apify
    nichos_bons_landing: list[str]   # Nichos bons para landing page
    oferta_por_nicho: dict[str, str]  # Niche -> tipo de oferta
    nichos_high_ticket: list[str]    # Para +10 no score
    franquias_grandes: list[str]     # Nomes de franquias/redes
    nicho_prio: dict[str, int]       # Peso do nicho (para campanha)
    cidade_prio: dict[str, int]      # Peso da cidade (para campanha)
    nicho_tipo: dict[str, str]       # Niche -> tipo de pagina (agendamento/cardapio/presenca)
    score_peso_regiao: int          # Bonus: +10 rio_premium, 0 baixada
    msg_tone: str                    # "informal" | "consultivo"
    max_results_per_category: int    # Limite por busca no Maps
    max_places_apify: int            # Limite por busca Apify


# ═══════════════════════════════════════════════════════════════
# BAIXADA FLUMINENSE
# ═══════════════════════════════════════════════════════════════

BAIXADA = RegiaoConfig(
    key="baixada",
    label="Baixada Fluminense",
    cidades=[
        "Duque de Caxias, RJ",
        "Nova Iguaçu, RJ",
        "São João de Meriti, RJ",
        "Belford Roxo, RJ",
        "Nilópolis, RJ",
        "Mesquita, RJ",
        "Queimados, RJ",
        "Itaguaí, RJ",
        "Seropédica, RJ",
        "Paracambi, RJ",
        "Japeri, RJ",
    ],
    bairros=[],
    categorias=[
        "restaurante",
        "salão de beleza",
        "barbearia",
        "clínica médica",
        "oficina mecânica",
        "pet shop",
        "loja de roupas",
        "padaria",
        "pizzaria",
        "bar",
        "farmácia",
        "dentista",
        "advogado",
        "contador",
        "imobiliária",
        "academia",
        "lanchonete",
        "supermercado",
        "material de construção",
        "auto escola",
        "lavanderia",
        "floricultura",
        "ótica",
        "joalheria",
        "clínica veterinária",
        "estética",
        "loja de celulares",
        "loja de móveis",
        "papelaria",
        "loja de bicicleta",
        "confeitaria",
        "serralheria",
        "vidraçaria",
        "pintor",
        "eletricista",
        "encanador",
        "marcenaria",
        "escola de idiomas",
        "curso pré-vestibular",
        "estúdio de pilates",
    ],
    nichos_tier1=[
        "dentista",
        "advogado",
        "clínica estética",
        "academia",
        "salão de beleza",
        "barbearia",
    ],
    nichos_bons_landing=[
        "barbearia", "salao de beleza", "salão de beleza", "estetica", "estética",
        "manicure", "sobrancelha", "restaurante", "marmitaria", "pizzaria",
        "açai", "açaí", "lanchonete", "confeitaria", "padaria", "churrascaria",
        "bar", "igreja", "evento", "advogado", "autônomo", "autonomo",
        "assistencia tecnica", "assistência técnica", "oficina mecanica",
        "oficina mecânica", "pet shop", "clinica veterinaria", "clínica veterinária",
        "auto escola", "academia", "estúdio de pilates", "estudio de pilates",
        "dentista", "clinica medica", "clínica médica",
    ],
    oferta_por_nicho={
        # Pagina de Agendamento
        "barbearia": "Página de Agendamento",
        "salão de beleza": "Página de Agendamento",
        "salao de beleza": "Página de Agendamento",
        "estética": "Página de Agendamento",
        "estetica": "Página de Agendamento",
        "manicure": "Página de Agendamento",
        "sobrancelha": "Página de Agendamento",
        "clínica médica": "Página de Agendamento",
        "clinica medica": "Página de Agendamento",
        "estúdio de pilates": "Página de Agendamento",
        "estudio de pilates": "Página de Agendamento",
        "academia": "Página de Agendamento",
        # Cardapio Digital
        "restaurante": "Cardápio Digital",
        "marmitaria": "Cardápio Digital",
        "pizzaria": "Cardápio Digital",
        "açai": "Cardápio Digital",
        "açaí": "Cardápio Digital",
        "lanchonete": "Cardápio Digital",
        "confeitaria": "Cardápio Digital",
        "padaria": "Cardápio Digital",
        "churrascaria": "Cardápio Digital",
        "bar": "Cardápio Digital",
        # Pagina de Evento
        "igreja": "Página de Evento",
        "evento": "Página de Evento",
        # Mini Site Profissional
        "advogado": "Mini Site Profissional",
        "autônomo": "Mini Site Profissional",
        "autonomo": "Mini Site Profissional",
        "assistência técnica": "Mini Site Profissional",
        "assistencia tecnica": "Mini Site Profissional",
        "contador": "Mini Site Profissional",
        "eletricista": "Mini Site Profissional",
        "encanador": "Mini Site Profissional",
        "pintor": "Mini Site Profissional",
        "marcenaria": "Mini Site Profissional",
        "serralheria": "Mini Site Profissional",
        "vidraçaria": "Mini Site Profissional",
        "material de construção": "Mini Site Profissional",
        "oficina mecânica": "Mini Site Profissional",
        "oficina mecanica": "Mini Site Profissional",
        "dentista": "Mini Site Profissional",
        "pet shop": "Mini Site Profissional",
        "clínica veterinária": "Mini Site Profissional",
        "clinica veterinaria": "Mini Site Profissional",
        "auto escola": "Mini Site Profissional",
        "escola de idiomas": "Mini Site Profissional",
        "curso pré-vestibular": "Mini Site Profissional",
        # Mini Site Vendedor
        "floricultura": "Mini Site Vendedor",
        "ótica": "Mini Site Vendedor",
        "otica": "Mini Site Vendedor",
        "joalheria": "Mini Site Vendedor",
        "loja de roupas": "Mini Site Vendedor",
        "loja de celulares": "Mini Site Vendedor",
        "loja de móveis": "Mini Site Vendedor",
        "loja de moveis": "Mini Site Vendedor",
        "loja de bicicleta": "Mini Site Vendedor",
        "papelaria": "Mini Site Vendedor",
        "farmácia": "Mini Site Vendedor",
        "farmacia": "Mini Site Vendedor",
        "supermercado": "Mini Site Vendedor",
        "lavanderia": "Mini Site Vendedor",
        "imobiliária": "Mini Site Vendedor",
        "imobiliaria": "Mini Site Vendedor",
    },
    nichos_high_ticket=[],
    franquias_grandes=[
        "mcdonald", "burger king", "subway", "habib", "bob's", "kfc",
        "pizza hut", "domino", "starbucks", "giraffas", "spoleto",
        "outback", "applebee", "wendy", "taco bell", "baskin robbins",
        "cold stone", "nutrella", "camarao", "madero", "supermercado zaffari",
        "pao de acucar", "extra hiper", "carrefour", "assaí atacadista",
        "atacadao", "big", "mercado livre", "magazine luiza", "americanas",
        "casas bahia", "pontofrio", "extra", "renner", "riachuelo",
        "c&a", "marisa", "arezzo", "track&field", "vivolo",
        "smartfit", "bluefit", "bodytech", "formula academia",
        "odontoprev", "oral uni", "sorriso", "dentsply",
        "cabana", "farroupilha", "churrascaria rodizio",
        "porcao", "fogo de chao", "chama gaucho",
        "ifood", "rappi", "99food", "ubereats",
    ],
    nicho_prio={
        "estética": 5, "salão de beleza": 5, "barbearia": 5,
        "dentista": 4, "confeitaria": 4, "pizzaria": 4,
        "clínica médica": 4, "estúdio de pilates": 4,
        "restaurante": 3, "padaria": 3, "clínica veterinária": 3,
        "academia": 3, "advogado": 3, "auto escola": 3, "pet shop": 3, "lanchonete": 3,
        "bar": 2, "oficina mecânica": 2,
    },
    cidade_prio={
        "Mesquita": 3,
        "Nilópolis": 2,
        "São João de Meriti": 2,
        "Belford Roxo": 1,
        "Nova Iguaçu": 1,
        "Duque de Caxias": 1,
    },
    nicho_tipo={
        "estética": "agendamento", "salão de beleza": "agendamento", "barbearia": "agendamento",
        "dentista": "agendamento", "clínica médica": "agendamento", "clínica veterinária": "agendamento",
        "estúdio de pilates": "agendamento", "academia": "agendamento", "auto escola": "agendamento",
        "confeitaria": "cardápio", "pizzaria": "cardápio", "restaurante": "cardápio",
        "padaria": "cardápio", "lanchonete": "cardápio",
        "advogado": "presença", "bar": "presença", "oficina mecânica": "presença", "pet shop": "presença",
    },
    score_peso_regiao=0,
    msg_tone="informal",
    max_results_per_category=20,
    max_places_apify=10,
)


# ═══════════════════════════════════════════════════════════════
# RIO PREMIUM
# ═══════════════════════════════════════════════════════════════

RIO_PREMIUM = RegiaoConfig(
    key="rio_premium",
    label="Rio Premium",
    cidades=["Rio de Janeiro, RJ"],
    bairros=[
        "Barra da Tijuca",
        "Recreio dos Bandeirantes",
        "Copacabana",
        "Ipanema",
        "Leblon",
        "Botafogo",
        "Flamengo",
        "Tijuca",
        "Jardim Botânico",
        "Lagoa",
        "Gávea",
        "Laranjeiras",
        "Humaitá",
        "São Conrado",
        "Urca",
        "Méier",
        "Vila Isabel",
        "Grajaú",
        "Jardim Guanabara",
        "Freguesia",
        "Pechincha",
        "Vila Valqueire",
        "Recreio",
        "Taquara",
        "Centro",
    ],
    categorias=[
        "clínica de estética",
        "salão premium",
        "barbearia premium",
        "dentista",
        "psicólogo",
        "nutricionista",
        "fisioterapeuta",
        "pilates",
        "academia boutique",
        "studio de sobrancelha",
        "studio de cílios",
        "lash designer",
        "spa",
        "restaurante",
        "pousada",
        "hotel boutique",
        "advogado",
        "arquiteto",
        "fotógrafo",
        "escola",
        "curso livre",
        "clínica médica",
        "harmonização facial",
        "depilação a laser",
        "micropigmentação",
        "designer de interiores",
        "personal trainer",
        "consultório",
    ],
    nichos_tier1=[
        "clínica de estética",
        "dentista",
        "psicólogo",
        "advogado",
        "harmonização facial",
        "pilates",
    ],
    nichos_bons_landing=[
        "estética", "estetica", "clínica de estética", "clinica de estetica",
        "harmonização facial", "harmonizacao facial",
        "salão premium", "salao premium", "barbearia premium",
        "dentista", "clínica odontológica", "clinica odontologica",
        "psicólogo", "psicologo", "nutricionista",
        "fisioterapeuta", "pilates", "academia boutique",
        "studio de sobrancelha", "studio de cílios", "lash designer",
        "spa", "depilação a laser", "depilacao a laser",
        "micropigmentação", "micropigmentacao",
        "personal trainer", "designer de interiores",
        "arquiteto", "fotógrafo", "fotografo",
        "advogado", "consultório", "consultorio",
        "restaurante", "hotel boutique", "pousada",
        "escola", "curso livre",
        "clínica médica", "clinica medica",
    ],
    oferta_por_nicho={
        # Pagina de Agendamento Premium
        "clínica de estética": "Página de Agendamento Premium",
        "clinica de estetica": "Página de Agendamento Premium",
        "estética": "Página de Agendamento Premium",
        "harmonização facial": "Página de Agendamento Premium",
        "harmonizacao facial": "Página de Agendamento Premium",
        "salão premium": "Página de Agendamento Premium",
        "barbearia premium": "Página de Agendamento Premium",
        "dentista": "Página de Agendamento Premium",
        "psicólogo": "Página de Agendamento Premium",
        "nutricionista": "Página de Agendamento Premium",
        "fisioterapeuta": "Página de Agendamento Premium",
        "pilates": "Página de Agendamento Premium",
        "academia boutique": "Página de Agendamento Premium",
        "spa": "Página de Agendamento Premium",
        "depilação a laser": "Página de Agendamento Premium",
        "micropigmentação": "Página de Agendamento Premium",
        "studio de sobrancelha": "Página de Agendamento Premium",
        "studio de cílios": "Página de Agendamento Premium",
        "lash designer": "Página de Agendamento Premium",
        "personal trainer": "Página de Agendamento Premium",
        "clínica médica": "Página de Agendamento Premium",
        "consultório": "Página de Agendamento Premium",
        # Mini Site Profissional Premium
        "advogado": "Mini Site Profissional Premium",
        "arquiteto": "Mini Site Profissional Premium",
        "designer de interiores": "Mini Site Profissional Premium",
        "fotógrafo": "Mini Site Profissional Premium",
        # Pagina de Reserva
        "restaurante": "Página de Reserva",
        "hotel boutique": "Página de Reserva",
        "pousada": "Página de Reserva",
        # Pagina de Inscricao
        "escola": "Página de Inscrição",
        "curso livre": "Página de Inscrição",
    },
    nichos_high_ticket=[
        "estética", "estetica", "clínica de estética", "clinica de estetica",
        "harmonização facial", "harmonizacao facial",
        "dentista", "psicólogo", "psicologo", "nutricionista",
        "fisioterapeuta", "pilates", "academia boutique",
        "advogado", "arquiteto", "spa",
        "salão premium", "salao premium", "barbearia premium",
        "fotógrafo", "fotografo", "curso livre",
    ],
    franquias_grandes=[
        # Comum (mesmo da baixada)
        "mcdonald", "burger king", "subway", "habib", "bob's", "kfc",
        "pizza hut", "domino", "starbucks", "giraffas", "spoleto",
        "outback", "applebee", "wendy", "taco bell", "baskin robbins",
        "cold stone", "madero",
        # Varejo
        "pao de acucar", "extra hiper", "carrefour", "assaí atacadista",
        "atacadao", "big", "magazine luiza", "americanas",
        "casas bahia", "pontofrio", "extra", "renner", "riachuelo",
        "c&a", "marisa", "arezzo", "track&field", "vivolo",
        # Fitness
        "smartfit", "smart fit", "bluefit", "bodytech", "formula academia",
        # Saude
        "odontoprev", "oral uni", "sorriso", "dentsply",
        "espaçolaser", "espacolaser", "odontocompany", "oral sin", "sorridents",
        # Estetica redes
        "sobrancelhas design",
        # Pet
        "petz", "cobasi",
        # Educacao
        "cna", "wizard", "fisk", "microlins", "kumon",
        # Beauty
        "o boticário", "natura", "quem disse berenice",
        # Chocolates
        "cacau show",
        # Imobiliaria
        "lopes", "cyrela",
        # Delivery
        "ifood", "rappi", "ubereats",
        # Hotel
        "ibis", "ibis budget", "ibis styles", "mercure", "novotel",
        # Farmacia
        "drogasil", "drogaria pacheco", "raia", "pague menos",
        # Transporte
        "localiza", "movida", "unidas",
        # Cartao
        "cartão de todos",
        # Viagem
        "cvc",
    ],
    nicho_prio={
        "clínica de estética": 5, "harmonização facial": 5, "dentista": 5,
        "psicólogo": 5, "pilates": 5,
        "salão premium": 4, "barbearia premium": 4, "nutricionista": 4,
        "fisioterapeuta": 4, "spa": 4, "depilação a laser": 4,
        "advogado": 3, "arquiteto": 3, "personal trainer": 3,
        "micropigmentação": 3, "designer de interiores": 3,
        "clínica médica": 3, "academia boutique": 3,
        "restaurante": 2, "fotógrafo": 2,
        "hotel boutique": 2, "pousada": 2,
    },
    cidade_prio={
        # Bairros premium com maior peso
        "Leblon": 5, "Ipanema": 5, "Gávea": 5, "Jardim Botânico": 5,
        "Lagoa": 4, "Copacabana": 4, "São Conrado": 4, "Urca": 4,
        "Barra da Tijuca": 3, "Recreio dos Bandeirantes": 3,
        "Botafogo": 3, "Flamengo": 3, "Vila Isabel": 2,
        "Tijuca": 2, "Méier": 2, "Laranjeiras": 2,
        "Grajaú": 1, "Humaitá": 1, "Centro": 1,
    },
    nicho_tipo={
        "clínica de estética": "agendamento", "harmonização facial": "agendamento",
        "salão premium": "agendamento", "barbearia premium": "agendamento",
        "dentista": "agendamento", "psicólogo": "agendamento",
        "nutricionista": "agendamento", "fisioterapeuta": "agendamento",
        "pilates": "agendamento", "academia boutique": "agendamento",
        "spa": "agendamento", "depilação a laser": "agendamento",
        "micropigmentação": "agendamento", "personal trainer": "agendamento",
        "clínica médica": "agendamento", "consultório": "agendamento",
        "restaurante": "cardápio", "hotel boutique": "cardápio", "pousada": "cardápio",
        "advogado": "presença", "arquiteto": "presença", "designer de interiores": "presença",
        "fotógrafo": "presença",
    },
    score_peso_regiao=10,
    msg_tone="consultivo",
    max_results_per_category=20,
    max_places_apify=5,
)


# ═══════════════════════════════════════════════════════════════
# REGISTRO DE REGIOES
# ═══════════════════════════════════════════════════════════════

_REGIOES: dict[str, RegiaoConfig] = {
    "baixada": BAIXADA,
    "rio_premium": RIO_PREMIUM,
}


def get_regiao(key: str) -> RegiaoConfig:
    """Retorna config de uma regiao pelo key."""
    if key not in _REGIOES:
        raise ValueError(f"Regiao '{key}' nao existe. Opcoes: {list(_REGIOES.keys())}")
    return _REGIOES[key]


def get_regioes() -> dict[str, RegiaoConfig]:
    """Retorna todas as regioes."""
    return dict(_REGIOES)


def resolve_regiao(arg: str | None) -> list[RegiaoConfig]:
    """
    Resolve o argumento --regiao em lista de RegiaoConfig.

    - None / "" -> [BAIXADA] (compatibilidade com scripts atuais)
    - "baixada" -> [BAIXADA]
    - "rio_premium" -> [RIO_PREMIUM]
    - "todas" -> [BAIXADA, RIO_PREMIUM]
    """
    if arg is None or arg == "":
        return [BAIXADA]
    if arg == "todas":
        return [BAIXADA, RIO_PREMIUM]
    return [get_regiao(arg)]


def get_output_dir(regiao_key: str, subdir: str) -> Path:
    """
    Retorna diretorio de saida especifico por regiao.

    baixada -> output/baixada/{subdir}/
    rio_premium -> output/rio_premium/{subdir}/
    """
    region_dir = OUTPUT_BASE / regiao_key / subdir
    region_dir.mkdir(parents=True, exist_ok=True)
    return region_dir


def get_locais_busca(regiao: RegiaoConfig) -> list[str]:
    """
    Retorna lista de locais para busca no Google Maps.

    baixada: cidades (ex: "Duque de Caxias, RJ")
    rio_premium: bairros formatados (ex: "Barra da Tijuca - Rio de Janeiro, RJ")
    """
    if regiao.bairros:
        return [f"{bairro} - Rio de Janeiro, RJ" for bairro in regiao.bairros]
    return regiao.cidades


def detectar_regiao_do_lead(lead: dict) -> str:
    """
    Detecta a regiao de um lead a partir dos dados.

    Retorna "rio_premium" ou "baixada".
    """
    cidade = (lead.get("cidade") or "").lower()
    bairro = (lead.get("bairro") or "").lower()
    origem = lead.get("origem") or ""

    # Se ja tem origem definida, usar
    if origem in ("baixada", "rio_premium"):
        return origem

    # Verificar por cidade
    if "rio de janeiro" in cidade:
        return "rio_premium"

    # Verificar por bairro premium
    bairros_lower = [b.lower() for b in RIO_PREMIUM.bairros]
    if bairro and any(b in bairro for b in bairros_lower):
        return "rio_premium"

    return "baixada"