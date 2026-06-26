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
from dataclasses import dataclass, field
from typing import Optional

from config.franquia import detectar_franquia
from utils.phone_utils import normalizar_telefone_br, gerar_link_whatsapp


# ══════════════════════════════════════════════════════════════════
# GRUPOS E SUBNICHOS
# ══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Subnicho:
    query: str
    label: str
    msg_cat: str


@dataclass
class GrupoConfig:
    key: str
    label: str
    subnichos: list[Subnicho]

    @property
    def queries(self) -> list[str]:
        return [s.query for s in self.subnichos]


_ASSISTENCIAS = [
    Subnicho("assistencia tecnica de celular", "Assistência técnica de celular", "assistencia_tecnica"),
    Subnicho("conserto de celular", "Conserto de celular", "assistencia_tecnica"),
    Subnicho("assistencia de computadores e notebooks", "Assistência de computadores e notebooks", "assistencia_tecnica"),
    Subnicho("assistencia de impressoras", "Assistência de impressoras", "assistencia_tecnica"),
    Subnicho("assistencia de eletrodomesticos", "Assistência de eletrodomésticos", "assistencia_tecnica"),
    Subnicho("assistencia de eletronicos e videogames", "Assistência de eletrônicos e videogames", "assistencia_tecnica"),
]

_REFRIGERACAO = [
    Subnicho("refrigeracao", "Refrigeração", "ar_refrigeracao"),
    Subnicho("climatizacao", "Climatização", "ar_refrigeracao"),
    Subnicho("instalacao de ar condicionado", "Instalação de ar-condicionado", "ar_refrigeracao"),
    Subnicho("manutencao de ar condicionado", "Manutenção de ar-condicionado", "ar_refrigeracao"),
    Subnicho("conserto de geladeiras e freezers", "Conserto de geladeiras e freezers", "ar_refrigeracao"),
]

_AUTOMOTIVO = [
    Subnicho("oficina mecanica", "Oficina mecânica", "oficina_mecanica"),
    Subnicho("autoeletrica", "Autoelétrica", "oficina_mecanica"),
    Subnicho("oficina de motos", "Oficina de motos", "oficina_mecanica"),
    Subnicho("centro automotivo", "Centro automotivo", "oficina_mecanica"),
    Subnicho("injecao eletronica", "Injeção eletrônica", "oficina_mecanica"),
]

_SOB_MEDIDA = [
    Subnicho("vidracaria", "Vidraçaria", "oficina_producao"),
    Subnicho("marcenaria", "Marcenaria", "oficina_producao"),
    Subnicho("moveis planejados", "Móveis planejados", "oficina_producao"),
    Subnicho("serralheria", "Serralheria", "oficina_producao"),
    Subnicho("portoes automaticos", "Portões automáticos", "oficina_producao"),
]

_SERVICOS_EXTERNOS = [
    Subnicho("energia solar", "Energia solar", "prestador_servico"),
    Subnicho("seguranca eletronica", "Segurança eletrônica", "seguranca"),
    Subnicho("cameras e alarmes", "Câmeras e alarmes", "seguranca"),
    Subnicho("dedetizacao", "Dedetização", "prestador_servico"),
    Subnicho("manutencao de piscinas", "Manutenção de piscinas", "prestador_servico"),
    Subnicho("manutencao predial", "Manutenção predial", "prestador_servico"),
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
    """
    grupo = get_grupo(grupo_key)
    cidade_clean = (cidade or "").strip()
    return [
        (f"{s.query} em {cidade_clean}", s.label, s.msg_cat)
        for s in grupo.subnichos
    ]


def detectar_grupo_subnicho(lead: dict) -> tuple[str, str]:
    """
    Detecta (grupo_key, subnicho_label) a partir dos dados do lead.
    Retorna ("", "") se nao encaixar em nenhum grupo.
    """
    texto = " ".join([
        str(lead.get("nome") or ""),
        str(lead.get("categoria") or ""),
        str(lead.get("nicho") or ""),
        str(lead.get("subnicho") or ""),
    ]).lower()

    for grupo_key, grupo in GRUPOS.items():
        for sub in grupo.subnichos:
            if _match_query(sub.query, texto):
                return grupo_key, sub.label
    return "", ""


def _match_query(query: str, texto: str) -> bool:
    padrao = re.sub(r"\s+", " ", query.lower()).strip()
    tokens = [t for t in padrao.split() if len(t) > 2 or t in ("de", "ar")]
    return all(t in texto for t in tokens) if tokens else False


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
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas que trabalham com servicos, veiculos e orcamentos.\n\n"
        f"Um dos maiores problemas de uma oficina e perder o controle de qual servico foi autorizado, o que ja foi feito e quanto o cliente ainda precisa pagar. Isso pode causar atraso, retrabalho e ate discussao na hora da entrega.\n\n"
        f"No AVGESTAO voces conseguem abrir a ordem de servico, registrar tudo que sera feito, enviar o orcamento para aprovacao do cliente e acompanhar cada etapa do veiculo.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um acesso para voces entrarem no sistema e testarem na propria oficina?"
    )


def _msg_assistencia_tecnica(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para ajudar assistencias tecnicas a controlar os aparelhos recebidos e o andamento dos servicos.\n\n"
        f"Uma das situacoes mais complicadas desse ramo e o cliente deixar um aparelho e depois ninguem encontrar rapidamente o diagnostico, o orcamento, as pecas utilizadas ou em qual etapa o servico esta. Alem da perda de tempo, isso pode prejudicar a confianca do cliente.\n\n"
        f"No AVGESTAO voces conseguem abrir a ordem de servico, registrar o aparelho, montar o orcamento e enviar um link para o cliente acompanhar e aprovar.\n\n"
        f"Estou oferecendo 15 dias gratuitos para teste.\n\n"
        f"Posso liberar um login para voces entrarem e testarem com um atendimento real?"
    )


def _msg_oficina_producao(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas que trabalham com servicos personalizados e orcamentos.\n\n"
        f"Um dos maiores riscos desse segmento e uma medida, alteracao ou observacao importante ficar perdida entre varias conversas no WhatsApp. Um detalhe esquecido pode gerar orcamento errado, retrabalho e prejuizo no material.\n\n"
        f"No AVGESTAO voces conseguem registrar o cliente, organizar as informacoes do servico, montar o orcamento e enviar um link para o cliente aprovar antes da producao.\n\n"
        f"O sistema esta disponivel para teste gratuito durante 15 dias.\n\n"
        f"Posso criar um acesso para voces entrarem e testarem no proprio negocio?"
    )


def _msg_prestador_servico(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas e profissionais que trabalham com atendimentos e servicos externos.\n\n"
        f"Um dos maiores problemas nessa rotina e perder o controle de quem pediu orcamento, quem aprovou, qual servico ainda esta pendente e qual cliente ainda nao pagou.\n\n"
        f"No AVGESTAO voces conseguem organizar os clientes, criar orcamentos, abrir ordens de servico e acompanhar os valores recebidos e pendentes em um so lugar.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um login para voces entrarem no sistema e testarem com os proprios servicos?"
    )


def _msg_ar_refrigeracao(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas de manutencao, refrigeracao e climatizacao.\n\n"
        f"Uma das maiores dificuldades desse ramo e controlar varios chamados ao mesmo tempo e depois nao encontrar rapidamente o historico do equipamento, o orcamento aprovado, o que foi trocado ou se o servico ainda esta na garantia.\n\n"
        f"No AVGESTAO voces conseguem registrar o cliente e o equipamento, abrir a ordem de servico, enviar o orcamento para aprovacao e manter todo o historico do atendimento organizado.\n\n"
        f"Estou oferecendo 15 dias gratuitos para teste.\n\n"
        f"Posso liberar um acesso para voces entrarem e usarem o sistema em um atendimento real?"
    )


def _msg_seguranca(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome e Vanderson e desenvolvi o AVGESTAO para empresas que trabalham com servicos e orcamentos.\n\n"
        f"Quando entram varios orcamentos e servicos ao mesmo tempo, controlar tudo pelo WhatsApp ou caderno pode gerar confusao e retrabalho.\n\n"
        f"No AVGESTAO voces conseguem registrar o cliente, abrir a ordem de servico, enviar orcamento para aprovacao e acompanhar cada etapa.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um acesso para voces entrarem no sistema e testarem?"
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
        f"Passando para saber se conseguiram ver minha mensagem sobre o AVGESTAO.\n\n"
        f"O sistema reune clientes, orcamentos, ordens de servico, andamento dos atendimentos, valores e historico em um so lugar.\n\n"
        f"Alem disso, o cliente pode receber um link para visualizar e aprovar o orcamento e acompanhar o servico sem precisar perguntar toda hora pelo WhatsApp.\n\n"
        f"O acesso fica liberado gratuitamente por 15 dias, para voces testarem com atendimentos reais e decidirem somente depois.\n\n"
        f"Posso criar o login de teste para voces?"
    )


def _followup2(nome: str) -> str:
    return (
        f"Boa tarde, pessoal da {nome}!\n\n"
        f"Esse sera meu ultimo contato para nao incomodar.\n\n"
        f"Acredito que o AVGESTAO pode ajudar voces a economizar tempo e evitar informacoes perdidas entre conversas, papel e planilhas.\n\n"
        f"No sistema ficam organizados o cadastro do cliente, orcamento, aprovacao, ordem de servico, andamento, valores e historico de cada atendimento.\n\n"
        f"O teste e gratuito por 15 dias, sem compromisso, e voces podem conhecer o sistema por dentro usando na propria rotina.\n\n"
        f"Quer que eu deixe um acesso preparado para voces?"
    )


def gerar_mensagem_avgestao(lead: dict, tentativa: int = 1) -> str:
    """
    Gera a mensagem de WhatsApp para o lead.
    tentativa=1: abordagem inicial
    tentativa=2: follow-up 1
    tentativa=3: follow-up 2
    """
    nome = str(lead.get("nome") or "").strip() or "empresa"
    nome_curto = gerar_nome_curto(lead)

    if tentativa == 2:
        return _followup1(nome_curto)
    if tentativa == 3:
        return _followup2(nome_curto)

    msg_cat = str(lead.get("msg_cat") or "").strip()
    if not msg_cat:
        grupo_key, _ = detectar_grupo_subnicho(lead)
        if grupo_key:
            grupo = GRUPOS[grupo_key]
            msg_cat = grupo.subnichos[0].msg_cat

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
    """
    lead = dict(lead)
    grupo_key, subnicho = detectar_grupo_subnicho(lead)
    lead["grupo"] = grupo_key
    lead["subnicho"] = lead.get("subnicho") or subnicho

    if not lead.get("msg_cat"):
        if grupo_key:
            lead["msg_cat"] = GRUPOS[grupo_key].subnichos[0].msg_cat

    lead["faz_assistencia"] = classificar_faz_assistencia(lead)

    resultado = calcular_score_avgestao(lead)
    lead["score_avgestao"] = resultado.score
    lead["motivos_score"] = " | ".join(resultado.motivos)

    lead["nome_curto"] = gerar_nome_curto(lead)
    lead["mensagem_inicial"] = gerar_mensagem_avgestao(lead, tentativa=1)
    lead["link_whatsapp"] = gerar_link_whatsapp_avgestao(lead, tentativa=1)

    return lead


def filtrar_por_grupo(leads: list[dict], grupo_key: str) -> list[dict]:
    """Filtra leads pertencentes a um grupo."""
    grupo = get_grupo(grupo_key)
    palavras = [s.query for s in grupo.subnichos]
    filtrados = []
    for lead in leads:
        texto = " ".join([
            str(lead.get("nome") or ""),
            str(lead.get("categoria") or ""),
            str(lead.get("nicho") or ""),
            str(lead.get("subnicho") or ""),
        ]).lower()
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
