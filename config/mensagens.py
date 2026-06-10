"""
Geracao de mensagens WhatsApp por tom de regiao.

Informal (baixada): casual, amigavel, direto
Consultivo (rio_premium): profissional, elegante, tom de conselho

Regras para todas as mensagens:
- Sem preco na primeira mensagem
- Sem link na primeira mensagem
- Pedir permissao antes de mandar exemplo
- Ser curta e humana
- Portugues brasileiro natural
- Tom consultivo: "notei que...", "pode acabar...", "eu trabalho criando..."
- Citar o nome do comercio
- NUNCA: "você está perdendo cliente", "enquanto não tiver", "concorrente"
"""

from __future__ import annotations

from config.regioes import RegiaoConfig, BAIXADA, RIO_PREMIUM


# ═══════════════════════════════════════════════════════════════
# INFORMAL (BAIXADA)
# ═══════════════════════════════════════════════════════════════

_MSGS_INFORMAL_AGENDAMENTO = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e notei que não tem uma página de agendamento. Quando o cliente quer marcar horário e não consegue, acaba indo para o próximo que aparece. Posso te mostrar como ficaria uma página?",
    "Oi! Tudo bem? Estava olhando {artigo} {referencia} no Google e percebi que não tem como agendar online. Percebeu que muitos clientes desistem quando não conseguem marcar fácil? Posso te mandar uma prévia de como ficaria uma página?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Notei que não tem uma página com serviços e agendamento, isso faz o cliente acabar chamando outro lugar. Quer ver como ficaria uma página profissional?",
]

_MSGS_INFORMAL_CARDAPIO = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e reparei que não tem uma página com cardápio. Os clientes querem ver o que tem antes de pedir ou ir, sabe? Sem isso, perde venda. Quer ver como ficaria uma página?",
    "Oi! Tudo bem? Estava vendo {artigo} {referencia} no Google e notei que não tem o cardápio online. As pessoas pesquisam antes de decidir onde pedir, sem cardápio, elas vão para o concorrente. Posso te mandar uma prévia?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Quem busca por aí quer ver o cardápio e fazer pedido fácil, mas como não tem página, acaba escolhendo outro lugar. Quer que eu te mostre como ficaria?",
]

_MSGS_INFORMAL_PRESENCA = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e notei que não tem um site. Quem pesquisa online acaba achando o concorrente primeiro. Posso te mostrar como ficaria uma página profissional?",
    "Oi! Tudo bem? Estava olhando {artigo} {referencia} no Google e percebi que não tem presença online. Quando o cliente pesquisa e não acha nada, ele vai para quem tem. Quer ver como ficaria uma página?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Sem uma página online, quem pesquisa acaba encontrando o concorrente. Posso te mandar uma prévia de como ficaria uma página para o seu negócio?",
]

_FOLLOWUP_INFORMAL_1 = "Oi, tudo bem? Te mandei uma mensagem sobre uma página profissional para {artigo} {referencia}. Se tiver interesse, posso te mandar um exemplo. Sem compromisso."
_FOLLOWUP_INFORMAL_2 = "Oi! Último contato sobre {artigo} {referencia}. Se não for o momento, tudo bem. Se quiser ver como ficaria uma página, é só me avisar."


# ═══════════════════════════════════════════════════════════════
# CONSULTIVO (RIO PREMIUM) — tom elegante, cada nicho com sua dor
# ═══════════════════════════════════════════════════════════════

# Para clínicas, salões, barbearias, estética — foco em agendamento
_MSGS_CONSULTIVO_AGENDAMENTO = [
    "Olá, tudo bem? Vi {artigo} {referencia} {nome} no Google. Notei que as informações de serviços e agendamento poderiam ficar mais fáceis de encontrar em uma página simples. Quando a cliente precisa procurar muito, ela pode acabar agendando em outro lugar. Eu trabalho criando páginas para {referencia}. Posso te mandar uma prévia visual de como ficaria?",
    "Olá, tudo bem? Encontrei {artigo} {referencia} {nome} no Google. Percebi que não há uma página com informações de horários e agendamento. Sem isso, clientes que querem praticidade podem acabar indo para outro lugar. Trabalho criando páginas para {referencia}. Posso te enviar uma proposta visual?",
]

# Para estética, clínicas premium — tratamentos e resultados
_MSGS_CONSULTIVO_CLINICA = [
    "Olá, tudo bem? Vi {artigo} {referencia} {nome} no Google. Notei que as informações sobre tratamentos e resultados poderiam ficar mais organizadas em uma página simples. Quando a cliente precisa pesquisar muito, ela pode acabar escolhendo outra clínica. Eu trabalho criando páginas para clínicas de estética. Posso te mandar uma prévia visual de como ficaria?",
    "Olá, tudo bem? Encontrei {artigo} {referencia} {nome} no Google. Percebi que os procedimentos e diferenciais do espaço não estão fáceis de encontrar online. Quem busca um tratamento de qualidade acaba valorizando uma apresentação profissional. Trabalho criando páginas para clínicas. Posso te enviar uma proposta visual?",
]

# Para profissionais liberais — portfólio e serviços
_MSGS_CONSULTIVO_PORTFOLIO = [
    "Olá, tudo bem? Vi {artigo} {referencia} {nome} no Google. Notei que os trabalhos e serviços poderiam ficar mais fáceis de encontrar em uma página simples. Quando o cliente precisa ver exemplos do seu trabalho e não encontra fácil, ele pode acabar contratando outro profissional. Eu trabalho criando páginas para {referencia}. Posso te mandar uma prévia visual de como ficaria?",
    "Olá, tudo bem? Encontrei {artigo} {referencia} {nome} no Google. Percebi que não há uma página com portfólio e informações dos serviços. Clientes que buscam um profissional de qualidade valorizam ver os trabalhos antes de contratar. Trabalho criando páginas para {referencia}. Posso te enviar uma proposta visual?",
]

# Para consultórios — informações e contato
_MSGS_CONSULTIVO_CONSULTORIO = [
    "Olá, tudo bem? Vi {artigo} {referencia} {nome} no Google. Notei que as informações de contato e especialidades poderiam ficar mais organizadas em uma página simples. Quando o paciente precisa pesquisar muito para encontrar o que procura, ele pode acabar escolhendo outro profissional. Eu trabalho criando páginas para {referencia}. Posso te mandar uma prévia visual de como ficaria?",
    "Olá, tudo bem? Encontrei {artigo} {referencia} {nome} no Google. Percebi que não há uma página com as especialidades e formas de contato de forma organizada. Pacientes que buscam atendimento de qualidade confiam mais em profissionais com presença digital profissional. Trabalho criando páginas para consultórios. Posso te enviar uma proposta visual?",
]

# Para cardápio e delivery
_MSGS_CONSULTIVO_CARDAPIO = [
    "Olá, boa tarde. Vi {artigo} {referencia} {nome} no Google e notei que não há cardápio online. Quando o cliente quer ver o que tem antes de pedir e não encontra, ele pode acabar escolhendo outro lugar. Eu trabalho criando páginas com cardápio digital para restaurantes. Posso te mostrar como ficaria?",
]

# Padrão (presença geral)
_MSGS_CONSULTIVO_PRESENCA = [
    "Olá, tudo bem? Vi {artigo} {referencia} {nome} no Google. Notei que as informações do seu negócio poderiam ficar mais fáceis de encontrar em uma página simples. Quando o cliente busca por {referencia} na região e não encontra informações claras, ele pode acabar indo para outro lugar. Eu trabalho criando páginas para {referencia}. Posso te mandar uma prévia visual de como ficaria?",
]

_FOLLOWUP_CONSULTIVO_1 = "Olá, tudo bem? Mandei uma mensagem outro dia sobre uma página para {artigo} {referencia} {nome}. Se tiver interesse, posso te mandar um exemplo visual. Sem compromisso."
_FOLLOWUP_CONSULTIVO_2 = "Olá, tudo bem? Último contato sobre a página para {artigo} {referencia} {nome}. Se não for o momento, tudo bem. Se quiser ver como ficaria, é só me avisar."


# ═══════════════════════════════════════════════════════════════
# MAPEAMENTO NICHO -> REFERENCIA
# ═══════════════════════════════════════════════════════════════

_NICHO_REFERENCIA = {
    "estética": ("a", "clínica de estética"),
    "estetica": ("a", "clínica de estética"),
    "clínica de estética": ("a", "clínica de estética"),
    "clinica de estetica": ("a", "clínica de estética"),
    "harmonização facial": ("a", "clínica de harmonização"),
    "harmonizacao facial": ("a", "clínica de harmonização"),
    "salão de beleza": ("o", "salão"),
    "salao de beleza": ("o", "salão"),
    "salão premium": ("o", "salão"),
    "barbearia": ("a", "barbearia"),
    "barbearia premium": ("a", "barbearia"),
    "dentista": ("a", "clínica odontológica"),
    "psicólogo": ("o", "consultório"),
    "psicologo": ("o", "consultório"),
    "nutricionista": ("o", "consultório"),
    "fisioterapeuta": ("a", "clínica de fisioterapia"),
    "pilates": ("o", "estúdio de pilates"),
    "academia": ("a", "academia"),
    "academia boutique": ("a", "academia"),
    "clínica médica": ("a", "clínica"),
    "clinica medica": ("a", "clínica"),
    "clínica veterinária": ("a", "clínica veterinária"),
    "clinica veterinaria": ("a", "clínica veterinária"),
    "auto escola": ("a", "auto escola"),
    "restaurante": ("o", "restaurante"),
    "pizzaria": ("a", "pizzaria"),
    "confeitaria": ("a", "confeitaria"),
    "padaria": ("a", "padaria"),
    "lanchonete": ("a", "lanchonete"),
    "bar": ("o", "bar"),
    "advogado": ("o", "escritório de advocacia"),
    "oficina mecânica": ("a", "oficina"),
    "oficina mecanica": ("a", "oficina"),
    "pet shop": ("o", "pet shop"),
    "spa": ("o", "spa"),
    "depilação a laser": ("a", "clínica de depilação"),
    "depilacao a laser": ("a", "clínica de depilação"),
    "micropigmentação": ("a", "clínica de micropigmentação"),
    "micropigmentacao": ("a", "clínica de micropigmentação"),
    "studio de sobrancelha": ("o", "studio de sobrancelha"),
    "studio de cílios": ("o", "studio de cílios"),
    "lash designer": ("a", "lash designer"),
    "personal trainer": ("o", "personal trainer"),
    "arquiteto": ("o", "escritório de arquitetura"),
    "designer de interiores": ("o", "escritório de design"),
    "fotógrafo": ("o", "estúdio de fotografia"),
    "fotografo": ("o", "estúdio de fotografia"),
    "consultório": ("o", "consultório"),
    "consultorio": ("o", "consultório"),
    "hotel boutique": ("o", "hotel"),
    "pousada": ("a", "pousada"),
    "escola": ("a", "escola"),
    "curso livre": ("o", "curso"),
    "encanador": ("o", "serviço"),
    "enfermeiro": ("o", "consultório"),
    "fisioterapia": ("a", "clínica de fisioterapia"),
}


import random


def _get_referencia(nicho: str) -> tuple[str, str]:
    """Retorna (artigo, referencia) para o nicho."""
    nicho_lower = (nicho or "").lower().strip()
    return _NICHO_REFERENCIA.get(nicho_lower, ("o", "estabelecimento"))


def _is_nicho_clinica(nicho: str) -> bool:
    """Verifica se o nicho e de clinica/estetica premium."""
    nicho_lower = (nicho or "").lower()
    clinicas = [
        "estética", "estetica", "clínica de estética", "clinica de estetica",
        "harmonização", "harmonizacao", "spa", "depilação", "depilacao",
        "micropigmentação", "micropigmentacao",
        "studio de sobrancelha", "studio de cílios", "lash designer",
    ]
    return any(c in nicho_lower for c in clinicas)


def _is_nicho_profissional(nicho: str) -> bool:
    """Verifica se o nicho e de profissional liberal (portfólio)."""
    nicho_lower = (nicho or "").lower()
    profissionais = [
        "personal trainer", "arquiteto", "designer de interiores",
        "fotógrafo", "fotografo", "encanador",
    ]
    return any(p in nicho_lower for p in profissionais)


def _is_nicho_consultorio(nicho: str) -> bool:
    """Verifica se o nicho e de consultorio (informacoes)."""
    nicho_lower = (nicho or "").lower()
    consultorios = [
        "psicólogo", "psicologo", "nutricionista", "consultório", "consultorio",
        "enfermeiro",
    ]
    return any(c in nicho_lower for c in consultorios)


def gerar_mensagem_whatsapp(lead: dict, regiao: RegiaoConfig) -> str:
    """Gera mensagem de WhatsApp baseada no tom da regiao e nicho do lead."""
    nome = lead.get("nome", "")
    nicho = lead.get("nicho") or lead.get("categoria") or ""
    tipo = lead.get("_tipo") or lead.get("tipo_pagina") or ""

    artigo, referencia = _get_referencia(nicho)

    if not tipo:
        tipo = regiao.nicho_tipo.get(nicho.lower(), "presença")

    if regiao.msg_tone == "consultivo":
        if _is_nicho_clinica(nicho):
            msg = random.choice(_MSGS_CONSULTIVO_CLINICA)
        elif _is_nicho_profissional(nicho):
            msg = random.choice(_MSGS_CONSULTIVO_PORTFOLIO)
        elif _is_nicho_consultorio(nicho):
            msg = random.choice(_MSGS_CONSULTIVO_CONSULTORIO)
        elif tipo == "cardápio":
            msg = random.choice(_MSGS_CONSULTIVO_CARDAPIO)
        elif tipo == "agendamento":
            msg = random.choice(_MSGS_CONSULTIVO_AGENDAMENTO)
        else:
            msg = random.choice(_MSGS_CONSULTIVO_PRESENCA)
    else:
        if tipo == "cardápio":
            msg = random.choice(_MSGS_INFORMAL_CARDAPIO)
        elif tipo == "agendamento":
            msg = random.choice(_MSGS_INFORMAL_AGENDAMENTO)
        else:
            msg = random.choice(_MSGS_INFORMAL_PRESENCA)

    return msg.format(artigo=artigo, referencia=referencia, nome=nome)


def gerar_followup_1(lead: dict, regiao: RegiaoConfig) -> str:
    """Gera 2a mensagem de follow-up."""
    nicho = lead.get("nicho") or lead.get("categoria") or ""
    artigo, referencia = _get_referencia(nicho)
    nome = lead.get("nome", "")
    if regiao.msg_tone == "consultivo":
        return _FOLLOWUP_CONSULTIVO_1.format(artigo=artigo, referencia=referencia, nome=nome)
    return _FOLLOWUP_INFORMAL_1.format(artigo=artigo, referencia=referencia)


def gerar_followup_2(lead: dict, regiao: RegiaoConfig) -> str:
    """Gera 3a mensagem de follow-up (ultima)."""
    nicho = lead.get("nicho") or lead.get("categoria") or ""
    artigo, referencia = _get_referencia(nicho)
    nome = lead.get("nome", "")
    if regiao.msg_tone == "consultivo":
        return _FOLLOWUP_CONSULTIVO_2.format(artigo=artigo, referencia=referencia, nome=nome)
    return _FOLLOWUP_INFORMAL_2.format(artigo=artigo, referencia=referencia)