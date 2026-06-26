"""
Configuracao do modo de prospeccao AVGESTAO.

AVGESTAO e um SaaS de orcamentos, ordens de servico, aprovacao por link,
portal do cliente, financeiro e estoque. Este modulo agrupa os nichos com
forte potencial de contratacao, gera consultas especificas para o Google Maps,
calcula o score_avgestao (0-100), classifica se o negocio faz assistencia e
produz as mensagens de abordagem por nicho.

Funcoes puras e testaveis (sem I/O nem rede).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from config.franquia import detectar_franquia
from utils.phone_utils import normalizar_telefone_br, gerar_link_whatsapp


# ══════════════════════════════════════════════════════════════════
# NORMALIZACAO DE TEXTO (central)
# ══════════════════════════════════════════════════════════════════

_STOP_WORDS = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "e", "a", "o", "as", "os", "que", "ao",
    "aos", "pelo", "pela", "num", "numa", "dum", "duma",
}


def normalizar_texto(valor) -> str:
    """
    Normaliza um texto para comparacao:
    1. trata None -> string vazia
    2. converte para string
    3. aplica lowercase/casefold
    4. remove acentos com unicodedata.normalize (NFKD)
    5. remove pontuacao
    6. normaliza espacos
    """
    if valor is None:
        return ""
    s = str(valor).casefold()
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ASCII", "ignore").decode("ASCII")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenizar_sem_stopwords(valor) -> list[str]:
    """Normaliza e tokeniza removendo stop words."""
    tokens = normalizar_texto(valor).split()
    return [t for t in tokens if t and t not in _STOP_WORDS]


# ══════════════════════════════════════════════════════════════════
# GRUPOS E SUBNICHOS
# ══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Subnicho:
    query: str
    label: str
    msg_cat: str
    subnicho_key: str


@dataclass
class GrupoConfig:
    key: str
    label: str
    subnichos: list[Subnicho]

    @property
    def queries(self) -> list[str]:
        return [s.query for s in self.subnichos]


_ASSISTENCIAS = [
    Subnicho("assistencia tecnica de celular", "Assistência técnica de celular", "assistencia_tecnica", "celular"),
    Subnicho("conserto de celular", "Conserto de celular", "assistencia_tecnica", "celular"),
    Subnicho("assistencia de computadores e notebooks", "Assistência de computadores e notebooks", "assistencia_tecnica", "computadores"),
    Subnicho("assistencia de impressoras", "Assistência de impressoras", "assistencia_tecnica", "impressoras"),
    Subnicho("assistencia de eletrodomesticos", "Assistência de eletrodomésticos", "assistencia_tecnica", "eletrodomesticos"),
    Subnicho("assistencia de eletronicos e videogames", "Assistência de eletrônicos e videogames", "assistencia_tecnica", "eletronicos"),
]

_REFRIGERACAO = [
    Subnicho("refrigeracao", "Refrigeração", "ar_refrigeracao", "refrigeracao"),
    Subnicho("climatizacao", "Climatização", "ar_refrigeracao", "climatizacao"),
    Subnicho("instalacao de ar condicionado", "Instalação de ar-condicionado", "ar_refrigeracao", "ar_condicionado"),
    Subnicho("manutencao de ar condicionado", "Manutenção de ar-condicionado", "ar_refrigeracao", "ar_condicionado"),
    Subnicho("conserto de geladeiras e freezers", "Conserto de geladeiras e freezers", "ar_refrigeracao", "geladeiras"),
]

_AUTOMOTIVO = [
    Subnicho("oficina mecanica", "Oficina mecânica", "oficina_mecanica", "oficina_mecanica"),
    Subnicho("autoeletrica", "Autoelétrica", "oficina_mecanica", "autoeletrica"),
    Subnicho("oficina de motos", "Oficina de motos", "oficina_mecanica", "motos"),
    Subnicho("centro automotivo", "Centro automotivo", "oficina_mecanica", "centro_automotivo"),
    Subnicho("injecao eletronica", "Injeção eletrônica", "oficina_mecanica", "injecao_eletronica"),
]

_SOB_MEDIDA = [
    Subnicho("vidracaria", "Vidraçaria", "oficina_producao", "vidracaria"),
    Subnicho("marcenaria", "Marcenaria", "oficina_producao", "marcenaria"),
    Subnicho("moveis planejados", "Móveis planejados", "oficina_producao", "moveis_planejados"),
    Subnicho("serralheria", "Serralheria", "oficina_producao", "serralheria"),
    Subnicho("portoes automaticos", "Portões automáticos", "oficina_producao", "portoes"),
]

_SERVICOS_EXTERNOS = [
    Subnicho("energia solar", "Energia solar", "prestador_servico", "energia_solar"),
    Subnicho("seguranca eletronica", "Segurança eletrônica", "seguranca", "seguranca"),
    Subnicho("cameras e alarmes", "Câmeras e alarmes", "seguranca", "cameras_alarmes"),
    Subnicho("dedetizacao", "Dedetização", "prestador_servico", "dedetizacao"),
    Subnicho("manutencao de piscinas", "Manutenção de piscinas", "prestador_servico", "piscinas"),
    Subnicho("manutencao predial", "Manutenção predial", "prestador_servico", "predial"),
]


GRUPOS: dict[str, GrupoConfig] = {
    "assistencias": GrupoConfig("assistencias", "Assistências Técnicas", _ASSISTENCIAS),
    "refrigeracao": GrupoConfig("refrigeracao", "Refrigeração e Climatização", _REFRIGERACAO),
    "automotivo": GrupoConfig("automotivo", "Automotivo", _AUTOMOTIVO),
    "sob_medida": GrupoConfig("sob_medida", "Sob Medida", _SOB_MEDIDA),
    "servicos_externos": GrupoConfig("servicos_externos", "Serviços Externos", _SERVICOS_EXTERNOS),
}


def get_grupo(key: str) -> GrupoConfig:
    if key not in GRUPOS:
        raise ValueError(f"Grupo '{key}' nao existe. Opcoes: {list(GRUPOS.keys())}")
    return GRUPOS[key]


def listar_grupos() -> list[str]:
    return list(GRUPOS.keys())


def resolver_grupo(arg: Optional[str]) -> list[GrupoConfig]:
    if arg is None or arg == "" or arg == "todos":
        return list(GRUPOS.values())
    return [get_grupo(arg)]


def consultar_subnichos(grupo_key: str, cidade: str) -> list[tuple[str, str, str]]:
    """
    Retorna lista de (query_google_maps, subnicho_label, msg_cat) para o grupo e cidade.
    As consultas sao especificas por nicho e cidade.
    Mantida por compatibilidade. Prefira gerar_consultas_meta().
    """
    grupo = get_grupo(grupo_key)
    cidade_clean = (cidade or "").strip()
    return [
        (f"{s.query} em {cidade_clean}", s.label, s.msg_cat)
        for s in grupo.subnichos
    ]


def gerar_consultas_meta(grupo_key: str, cidade: str) -> list[dict]:
    """
    Gera consultas com metadados explicitos para o Google Maps.

    Cada item contem:
        query:        termo de busca completo (ex: "assistência técnica de celular em Duque de Caxias, RJ")
        grupo:        chave do grupo (ex: "assistencias")
        subnicho:     chave curta do subnicho (ex: "celular")
        subnicho_label: label legivel (ex: "Assistência técnica de celular")
        msg_cat:      categoria da mensagem (ex: "assistencia_tecnica")

    Durante a captacao, cada lead deve preservar source_query + grupo + subnicho.
    """
    grupo = get_grupo(grupo_key)
    cidade_clean = (cidade or "").strip()
    return [
        {
            "query": f"{s.query} em {cidade_clean}",
            "grupo": grupo.key,
            "subnicho": s.subnicho_key,
            "subnicho_label": s.label,
            "msg_cat": s.msg_cat,
        }
        for s in grupo.subnichos
    ]


def _validar_grupo_existe(grupo_key: str) -> bool:
    """Verifica se uma chave de grupo existe no registro."""
    return grupo_key in GRUPOS


def detectar_grupo_subnicho(lead: dict) -> tuple[str, str]:
    """
    Detecta (grupo_key, subnicho_label) a partir dos dados do lead.

    Precedencia:
    1. grupo/subnicho explicitos do lead (metadados da consulta de origem)
    2. source_query com metadados (quando o lead traz source_query_id)
    3. inferencia por _match_query (fallback para dados antigos/importacoes manuais)

    Retorna ("", "") se nao encaixar em nenhum grupo.
    """
    grupo_explicito = str(lead.get("grupo") or "").strip().lower()
    subnicho_explicito = str(lead.get("subnicho") or "").strip()

    if grupo_explicito and _validar_grupo_existe(grupo_explicito):
        grupo = GRUPOS[grupo_explicito]
        if subnicho_explicito:
            for sub in grupo.subnichos:
                if sub.subnicho_key == subnicho_explicito or sub.label == subnicho_explicito:
                    return grupo_explicito, sub.label
        return grupo_explicito, subnicho_explicito or grupo.subnichos[0].label

    texto = " ".join([
        str(lead.get("nome") or ""),
        str(lead.get("categoria") or ""),
        str(lead.get("nicho") or ""),
        str(lead.get("subnicho") or ""),
    ])

    for grupo_key, grupo in GRUPOS.items():
        for sub in grupo.subnichos:
            if _match_query(sub.query, texto):
                return grupo_key, sub.label
    return "", ""


def _match_query(query: str, texto: str) -> bool:
    """
    Verifica se os tokens significativos da query aparecem no texto.
    Usa normalizar_texto() (remove acentos, pontuacao, lowercase) e
    remove stop words de ambos os lados.

    A comparacao nao depende da frase completa: cada token significativo
    da query deve aparecer como substring de algum token do texto (ou vice-versa
    para tokens curtos como "ar").
    """
    tokens_query = tokenizar_sem_stopwords(query)
    if not tokens_query:
        return False

    tokens_texto = tokenizar_sem_stopwords(texto)
    texto_joined = " ".join(tokens_texto)

    for tq in tokens_query:
        if tq in texto_joined:
            continue
        if any(tq in tt or tt in tq for tt in tokens_texto if len(tt) >= 2):
            continue
        return False
    return True


# ══════════════════════════════════════════════════════════════════
# CLASSIFICACAO FAZ ASSISTENCIA
# ══════════════════════════════════════════════════════════════════

SINAIS_FORTES = [
    "assistencia tecnica", "assistência técnica",
    "conserto", "manutencao", "manutenção",
    "reparo", "troca de tela", "diagnostico", "diagnóstico",
    "formatacao", "formatação", "instalacao", "instalação",
    "tecnico", "técnico",
]

SINAIS_FRACOS = [
    "servico", "serviço", "orcamento", "orçamento",
    "os ", "ordem de servico", "ordem de serviço",
    "assistencia", "assistência", "reparo", "reparos",
    "manutencao predial", "manutenção predial",
]

FAZ_ASSISTENCIA_CONFIRMADO = "CONFIRMADO"
FAZ_ASSISTENCIA_PROVAVEL = "PROVÁVEL"
FAZ_ASSISTENCIA_NAO = "NÃO CONFIRMADO"


def classificar_faz_assistencia(lead: dict) -> str:
    """
    Classifica se o negocio faz assistencia/servico de reparo.

    CONFIRMADO: nome/categoria/subnicho contem sinal forte.
    PROVAVEL: somente sinais fracos ou pertence a grupo tipico de servico.
    NAO CONFIRMADO: nenhum sinal.
    """
    texto = " ".join([
        str(lead.get("nome") or ""),
        str(lead.get("categoria") or ""),
        str(lead.get("nicho") or ""),
        str(lead.get("subnicho") or ""),
    ]).lower()

    for sinal in SINAIS_FORTES:
        if sinal in texto:
            return FAZ_ASSISTENCIA_CONFIRMADO

    grupo_key, _ = detectar_grupo_subnicho(lead)
    if grupo_key in ("assistencias", "refrigeracao", "automotivo"):
        return FAZ_ASSISTENCIA_PROVAVEL

    for sinal in SINAIS_FRACOS:
        if sinal in texto:
            return FAZ_ASSISTENCIA_PROVAVEL

    return FAZ_ASSISTENCIA_NAO


# ══════════════════════════════════════════════════════════════════
# SCORE AVGESTAO (0-100)
# ══════════════════════════════════════════════════════════════════

_PALAVRAS_SERVICO = [
    "assistencia", "assistência", "manutencao", "manutenção",
    "conserto", "reparo", "instalacao", "instalação",
]

_PALAVRAS_VAREJO = [
    "loja", "venda", "vendas", "comercial", "distribuidora",
    "atacado", "atacadao", "supermercado", "mercado", "varejo",
    "deposito", "revenda",
]

_MARCADORES_EMPRESA = [
    "ltda", "me", "eireli", "eireli", "shop", "center", "centro",
    "empresa", "group", "grupo", "service", "servicos", "serviços",
    "tech", "solutions", "comercio", "trading",
]


@dataclass
class ResultadoScore:
    score: int
    motivos: list[str] = field(default_factory=list)


def _to_int(valor) -> int:
    try:
        return int(re.sub(r"\D", "", str(valor)))
    except (ValueError, TypeError):
        return 0


def _to_float(valor) -> float:
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def calcular_score_avgestao(lead: dict) -> ResultadoScore:
    """
    Calcula o score_avgestao de 0 a 100.

    Encaixe operacional:
      +30 nicho principal compativel
      +10 nome/categoria com assistencia/manutencao/conserto/reparo/instalacao
      +10 multiplos sinais de prestacao de servico
    Estrutura:
      +15 >= 20 avaliacoes
      +10 endereco comercial
      +5 site ou instagram
    Contato:
      +15 telefone ou whatsapp
      +5 nome e cidade validos
    Penalidades:
      -30 franquia ou grande rede
      -25 negocio aparentemente somente varejista
      -20 sem telefone
      -15 autonomo generico sem empresa identificada

    Presenca digital (site/instagram) NUNCA e penalizada.
    """
    score = 0
    motivos: list[str] = []

    nome = str(lead.get("nome") or "").strip()
    categoria = str(lead.get("categoria") or lead.get("nicho") or "").strip()
    subnicho = str(lead.get("subnicho") or "").strip()
    endereco = str(lead.get("endereco") or "").strip()
    cidade = str(lead.get("cidade") or "").strip()
    telefone = str(lead.get("telefone") or "").strip()
    whatsapp = str(lead.get("whatsapp") or "").strip()
    instagram = str(lead.get("instagram") or "").strip()
    url_site = str(lead.get("url_site") or "").strip()
    tem_site = str(lead.get("tem_site") or "").strip().lower() in ("true", "sim", "1", "yes")
    num_avaliacoes = _to_int(lead.get("num_avaliacoes", 0))

    texto_baixo = f"{nome} {categoria} {subnicho}".lower()

    grupo_key, _ = detectar_grupo_subnicho(lead)
    if grupo_key:
        score += 30
        motivos.append("nicho principal compativel (+30)")
    elif any(p in texto_baixo for p in _PALAVRAS_SERVICO):
        score += 30
        motivos.append("nicho principal compativel (+30)")

    if any(p in texto_baixo for p in _PALAVRAS_SERVICO):
        score += 10
        motivos.append("nome/categoria com termos de servico (+10)")

    canais = sum([
        bool(telefone), bool(whatsapp), bool(instagram),
        bool(url_site) or tem_site, bool(endereco),
    ])
    if canais >= 2:
        score += 10
        motivos.append(f"multiplos sinais de prestacao de servico ({canais} canais) (+10)")

    if num_avaliacoes >= 20:
        score += 15
        motivos.append(f"{num_avaliacoes} avaliacoes (+15)")

    if endereco:
        score += 10
        motivos.append("endereco comercial (+10)")

    if url_site or instagram or tem_site:
        score += 5
        motivos.append("site ou instagram (+5)")

    tel_ou_wa = bool(telefone) or bool(whatsapp)
    if tel_ou_wa:
        score += 15
        motivos.append("telefone ou whatsapp (+15)")

    if nome and cidade:
        score += 5
        motivos.append("nome e cidade validos (+5)")

    resultado_franquia = detectar_franquia(
        nome,
        endereco=endereco,
        site=url_site,
        instagram=instagram,
    )
    if resultado_franquia.nivel_confianca == "alta":
        score -= 30
        motivos.append("franquia ou grande rede (-30)")

    if any(p in texto_baixo for p in _PALAVRAS_VAREJO) and \
       not any(p in texto_baixo for p in _PALAVRAS_SERVICO):
        score -= 25
        motivos.append("negocio aparentemente somente varejista (-25)")

    if not tel_ou_wa:
        score -= 20
        motivos.append("sem telefone (-20)")

    nome_tem_empresa = any(m in nome.lower() for m in _MARCADORES_EMPRESA)
    palavras_nome = nome.split()
    parece_pessoa = (1 <= len(palavras_nome) <= 4) and not nome_tem_empresa
    if parece_pessoa and not grupo_key and not any(p in texto_baixo for p in _PALAVRAS_SERVICO):
        score -= 15
        motivos.append("autonomo generico sem empresa identificada (-15)")

    score = max(0, min(100, score))
    return ResultadoScore(score=score, motivos=motivos)


# ══════════════════════════════════════════════════════════════════
# DEDUPLICACAO
# ══════════════════════════════════════════════════════════════════

def chave_dedup(lead: dict) -> tuple[str, str, str, str]:
    """
    Retorna a chave de deduplicacao em ordem de preferencia:
    (place_id, url_maps, telefone_normalizado, nome+endereco).

    O primeiro valor nao vazio determina a chave primaria.
    """
    place_id = str(lead.get("place_id") or "").strip()
    url_maps = str(lead.get("link_maps") or lead.get("url_maps") or "").strip()
    tel_norm = normalizar_telefone_br(lead.get("whatsapp") or lead.get("telefone") or "") or ""
    nome = str(lead.get("nome") or "").strip().lower()
    endereco = str(lead.get("endereco") or "").strip().lower()
    nome_endereco = f"{nome}|{endereco}" if nome else ""
    return (place_id, url_maps, tel_norm, nome_endereco)


def deduplicar_leads(leads: list[dict]) -> list[dict]:
    """
    Deduplica leads por place_id, url do Google Maps, telefone normalizado
    e combinacao nome + endereco (nesta ordem de prioridade).
    """
    vistos_place = set()
    vistos_maps = set()
    vistos_tel = set()
    vistos_nome_end = set()
    unicos: list[dict] = []

    for lead in leads:
        place_id, url_maps, tel_norm, nome_end = chave_dedup(lead)

        duplicata = False
        if place_id and place_id in vistos_place:
            duplicata = True
        elif url_maps and url_maps in vistos_maps:
            duplicata = True
        elif tel_norm and tel_norm in vistos_tel:
            duplicata = True
        elif nome_end and nome_end in vistos_nome_end:
            duplicata = True

        if duplicata:
            continue

        if place_id:
            vistos_place.add(place_id)
        if url_maps:
            vistos_maps.add(url_maps)
        if tel_norm:
            vistos_tel.add(tel_norm)
        if nome_end:
            vistos_nome_end.add(nome_end)

        unicos.append(lead)

    return unicos


# ══════════════════════════════════════════════════════════════════
# MENSAGENS POR NICHO (adaptado de campanha_avgestao.py)
# ══════════════════════════════════════════════════════════════════

def _msg_oficina_mecanica(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar oficinas e serviços automotivos.\n\n"
        f"Com ele vocês registram o veículo, abrem a ordem de serviço, controlam peças e serviços e enviam o orçamento para aprovação do cliente.\n\n"
        f"Eu mesmo configuro a conta para vocês testarem com um veículo real durante 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def _msg_assistencia_tecnica(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.\n\n"
        f"Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.\n\n"
        f"Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )


def _msg_oficina_producao(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar serviços sob medida.\n\n"
        f"Com ele vocês registram medidas e observações, montam o orçamento e enviam um link para o cliente conferir, aprovar e acompanhar o serviço.\n\n"
        f"Eu mesmo configuro a conta para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def _msg_prestador_servico(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar clientes, orçamentos e serviços.\n\n"
        f"Com ele vocês montam o orçamento, enviam para aprovação e acompanham os atendimentos pendentes, em andamento e concluídos.\n\n"
        f"Eu mesmo configuro a conta para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def _msg_ar_refrigeracao(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar empresas de manutenção e refrigeração.\n\n"
        f"Com ele vocês registram o cliente e o equipamento, abrem a ordem de serviço, enviam o orçamento para aprovação e mantêm o histórico do atendimento.\n\n"
        f"Eu mesmo configuro a conta para vocês testarem com um chamado real durante 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def _msg_seguranca(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar clientes, orçamentos e serviços.\n\n"
        f"Com ele vocês montam o orçamento, enviam para aprovação e acompanham os atendimentos pendentes, em andamento e concluídos.\n\n"
        f"Eu mesmo configuro a conta para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


_MENSAGENS_POR_CAT = {
    "oficina_mecanica": _msg_oficina_mecanica,
    "assistencia_tecnica": _msg_assistencia_tecnica,
    "oficina_producao": _msg_oficina_producao,
    "prestador_servico": _msg_prestador_servico,
    "ar_refrigeracao": _msg_ar_refrigeracao,
    "seguranca": _msg_seguranca,
}


def _followup1(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Passei aqui para saber se vocês chegaram a ver minha mensagem sobre o AVGESTÃO.\n\n"
        f"O sistema organiza os clientes, orçamentos e ordens de serviço em um só lugar, com link para o cliente aprovar e acompanhar tudo pelo celular.\n\n"
        f"A conta fica pronta rapidinho e vocês testam gratuitamente por 15 dias.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def _followup2(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}!\n\n"
        f"Esta é minha última mensagem para não incomodar.\n\n"
        f"Se mudarem de ideia sobre o AVGESTÃO, é só me procurar. Deixo o convite em aberto para testarem o sistema gratuitamente por 15 dias, sem compromisso.\n\n"
        f"Posso liberar o acesso de vocês?"
    )


def gerar_mensagem_avgestao(lead: dict, tentativa: int = 1) -> str:
    """
    Gera a mensagem de WhatsApp para o lead.
    tentativa=1: abordagem inicial
    tentativa=2: follow-up 1
    tentativa=3: follow-up 2

    A categoria da mensagem (msg_cat) e definida nesta ordem:
    1. msg_cat explicito do lead
    2. grupo/subnicho explicitos do lead -> msg_cat do subnicho
    3. classificacao por sinais do lead (detectar_grupo_subnicho)
    4. _match_query como fallback
    5. template generico (prestador_servico) como ultimo recurso
    """
    nome = str(lead.get("nome") or "").strip() or "empresa"
    nome_curto = gerar_nome_curto(lead)

    if tentativa == 2:
        return _followup1(nome_curto)
    if tentativa == 3:
        return _followup2(nome_curto)

    msg_cat = str(lead.get("msg_cat") or "").strip()

    if not msg_cat:
        grupo_explicito = str(lead.get("grupo") or "").strip().lower()
        subnicho_explicito = str(lead.get("subnicho") or "").strip()
        if grupo_explicito and _validar_grupo_existe(grupo_explicito):
            grupo = GRUPOS[grupo_explicito]
            for sub in grupo.subnichos:
                if sub.label == subnicho_explicito or sub.subnicho_key == subnicho_explicito:
                    msg_cat = sub.msg_cat
                    break
            if not msg_cat:
                msg_cat = grupo.subnichos[0].msg_cat

    if not msg_cat:
        grupo_key, _ = detectar_grupo_subnicho(lead)
        if grupo_key:
            msg_cat = GRUPOS[grupo_key].subnichos[0].msg_cat

    geradora = _MENSAGENS_POR_CAT.get(msg_cat, _msg_prestador_servico)
    return geradora(nome_curto)


def gerar_link_whatsapp_avgestao(lead: dict, tentativa: int = 1) -> str:
    """Gera link wa.me com a mensagem do AVGESTAO. NUNCA envia automaticamente."""
    tel = normalizar_telefone_br(lead.get("whatsapp") or lead.get("telefone") or "")
    if not tel:
        return ""
    return gerar_link_whatsapp(tel, gerar_mensagem_avgestao(lead, tentativa))


# ══════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════

def gerar_nome_curto(lead: dict) -> str:
    """Extrai um nome curto do negocio a partir do nome completo."""
    nome = str(lead.get("nome") or "").strip()
    if not nome:
        return "empresa"
    nome_curto = nome.split(" - ")[0].split(" | ")[0].split(",")[0].strip()
    if len(nome_curto) > 40:
        nome_curto = nome_curto[:40].rsplit(" ", 1)[0].strip()
    return nome_curto or "empresa"


def enriquecer_lead_avgestao(lead: dict) -> dict:
    """
    Adiciona ao lead os campos do modo AVGESTAO:
    grupo, subnicho, msg_cat, faz_assistencia, score_avgestao,
    motivos_score, nome_curto, mensagem_inicial, link_whatsapp.

    Precedencia de grupo/subnicho:
    1. grupo/subnicho explicitos do lead (metadados da consulta de origem)
    2. grupo/subnicho da source_query (quando disponivel)
    3. classificacao por sinais do lead
    4. _match_query como fallback

    NUNCA sobrescreve grupo/subnicho explicitos vindos da captacao.
    """
    lead = dict(lead)

    grupo_explicito = str(lead.get("grupo") or "").strip().lower()
    subnicho_explicito = str(lead.get("subnicho") or "").strip()
    msg_cat_explicito = str(lead.get("msg_cat") or "").strip()

    if grupo_explicito and _validar_grupo_existe(grupo_explicito):
        grupo_key = grupo_explicito
        if not subnicho_explicito:
            subnicho_explicito = GRUPOS[grupo_key].subnichos[0].label
    else:
        grupo_key, subnicho_detectado = detectar_grupo_subnicho(lead)
        if not subnicho_explicito:
            subnicho_explicito = subnicho_detectado

    lead["grupo"] = grupo_key
    lead["subnicho"] = subnicho_explicito

    if not msg_cat_explicito:
        if grupo_key:
            grupo = GRUPOS[grupo_key]
            sub_match = None
            for sub in grupo.subnichos:
                if sub.label == subnicho_explicito or sub.subnicho_key == subnicho_explicito:
                    sub_match = sub
                    break
            lead["msg_cat"] = sub_match.msg_cat if sub_match else grupo.subnichos[0].msg_cat
    else:
        lead["msg_cat"] = msg_cat_explicito

    lead["faz_assistencia"] = classificar_faz_assistencia(lead)

    resultado = calcular_score_avgestao(lead)
    lead["score_avgestao"] = resultado.score
    lead["motivos_score"] = " | ".join(resultado.motivos)

    lead["nome_curto"] = gerar_nome_curto(lead)
    lead["mensagem_inicial"] = gerar_mensagem_avgestao(lead, tentativa=1)
    lead["link_whatsapp"] = gerar_link_whatsapp_avgestao(lead, tentativa=1)

    return lead


def filtrar_por_grupo(leads: list[dict], grupo_key: str) -> list[dict]:
    """
    Filtra leads pertencentes a um grupo.

    Precedencia:
    1. campo 'grupo' explicito do lead (metadados da consulta de origem)
    2. _match_query nos textos (nome/categoria/nicho/subnicho)
    """
    grupo = get_grupo(grupo_key)
    palavras = [s.query for s in grupo.subnichos]
    filtrados = []
    for lead in leads:
        lead_grupo = str(lead.get("grupo") or "").strip().lower()
        if lead_grupo == grupo_key:
            filtrados.append(lead)
            continue
        texto = " ".join([
            str(lead.get("nome") or ""),
            str(lead.get("categoria") or ""),
            str(lead.get("nicho") or ""),
            str(lead.get("subnicho") or ""),
        ])
        if any(_match_query(p, texto) for p in palavras):
            filtrados.append(lead)
    return filtrados


def filtrar_por_cidade(leads: list[dict], cidade: str) -> list[dict]:
    """Filtra leads por cidade (case-insensitive, normalizada)."""
    alvo = (cidade or "").split(",")[0].strip().lower()
    if not alvo:
        return leads
    return [
        l for l in leads
        if alvo in str(l.get("cidade") or "").lower()
    ]


# ══════════════════════════════════════════════════════════════════
# COLUNAS DO XLSX (compartilhado entre prospectar e campanha)
# ══════════════════════════════════════════════════════════════════

COLUNAS_XLSX_AVGESTAO: list[tuple[str, str, int]] = [
    ("Nome", "nome", 38),
    ("Nome curto", "nome_curto", 28),
    ("Cidade", "cidade", 20),
    ("Nicho", "categoria", 22),
    ("Subnicho", "subnicho", 26),
    ("Telefone", "telefone", 18),
    ("WhatsApp", "whatsapp", 18),
    ("Instagram", "instagram", 28),
    ("Site", "url_site", 30),
    ("Avaliação", "avaliacao", 10),
    ("Quantidade de avaliações", "num_avaliacoes", 14),
    ("Faz assistência", "faz_assistencia", 16),
    ("Score AVGESTÃO", "score_avgestao", 14),
    ("Motivos do score", "motivos_score", 50),
    ("Mensagem inicial", "mensagem_inicial", 70),
    ("Link WhatsApp", "link_whatsapp", 55),
    ("Status", "status", 12),
    ("Data da abordagem", "data_abordagem", 16),
    ("Follow-up 1", "followup1", 70),
    ("Follow-up 2", "followup2", 70),
]


def linha_xlsx_avgestao(lead: dict) -> dict:
    """Constroi o dict header -> valor para uma linha do XLSX AVGESTAO (enriquecendo)."""
    enriquecido = enriquecer_lead_avgestao(lead)
    return {
        "Nome": enriquecido.get("nome", ""),
        "Nome curto": enriquecido.get("nome_curto", ""),
        "Cidade": enriquecido.get("cidade", ""),
        "Nicho": enriquecido.get("categoria", ""),
        "Subnicho": enriquecido.get("subnicho", ""),
        "Telefone": enriquecido.get("telefone", ""),
        "WhatsApp": enriquecido.get("whatsapp", ""),
        "Instagram": enriquecido.get("instagram", ""),
        "Site": enriquecido.get("url_site", ""),
        "Avaliação": enriquecido.get("avaliacao", ""),
        "Quantidade de avaliações": enriquecido.get("num_avaliacoes", ""),
        "Faz assistência": enriquecido.get("faz_assistencia", ""),
        "Score AVGESTÃO": enriquecido.get("score_avgestao", 0),
        "Motivos do score": enriquecido.get("motivos_score", ""),
        "Mensagem inicial": enriquecido.get("mensagem_inicial", ""),
        "Link WhatsApp": enriquecido.get("link_whatsapp", ""),
        "Status": enriquecido.get("status", "novo"),
        "Data da abordagem": enriquecido.get("data_abordagem", ""),
        "Follow-up 1": gerar_mensagem_avgestao(lead, tentativa=2),
        "Follow-up 2": gerar_mensagem_avgestao(lead, tentativa=3),
    }


def linha_xlsx_avgestao_pronto(lead: dict) -> dict:
    """
    Constroi o dict header -> valor a partir dos campos ja existentes no lead,
    sem reenriquecer nem recalcular score. Usado pela campanha para preservar
    o score_avgestao calculado pelo prospectar.
    """
    def _get(campo, default=""):
        v = lead.get(campo, default)
        return v if v is not None else default

    return {
        "Nome": _get("nome"),
        "Nome curto": _get("nome_curto") or gerar_nome_curto(lead),
        "Cidade": _get("cidade"),
        "Nicho": _get("categoria") or _get("nicho"),
        "Subnicho": _get("subnicho"),
        "Telefone": _get("telefone"),
        "WhatsApp": _get("whatsapp"),
        "Instagram": _get("instagram"),
        "Site": _get("url_site"),
        "Avaliação": _get("avaliacao"),
        "Quantidade de avaliações": _get("num_avaliacoes"),
        "Faz assistência": _get("faz_assistencia"),
        "Score AVGESTÃO": _get("score_avgestao", 0),
        "Motivos do score": _get("motivos_score"),
        "Mensagem inicial": _get("mensagem_whatsapp") or _get("mensagem_inicial") or gerar_mensagem_avgestao(lead, 1),
        "Link WhatsApp": _get("link_whatsapp") or gerar_link_whatsapp_avgestao(lead, 1),
        "Status": _get("status", "novo"),
        "Data da abordagem": _get("data_abordagem", ""),
        "Follow-up 1": _get("followup1") or gerar_mensagem_avgestao(lead, 2),
        "Follow-up 2": _get("followup2") or gerar_mensagem_avgestao(lead, 3),
    }


def prioridade_avgestao(score: int) -> str:
    if score >= 70:
        return "Alta"
    if score >= 40:
        return "Média"
    return "Baixa"
