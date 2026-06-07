"""
Geracao de mensagens WhatsApp por tom de regiao.

Informal (baixada): casual, amigavel, direto
Consultivo (rio_premium): profissional, elegante, pede permissao

Regras para todas as mensagens:
- Sem preco na primeira mensagem
- Sem link na primeira mensagem
- Pedir permissao antes de mandar exemplo
- Ser curta e humana
- Portugues brasileiro natural
"""

from __future__ import annotations

from config.regioes import RegiaoConfig, BAIXADA, RIO_PREMIUM

# ═══════════════════════════════════════════════════════════════
# INFORMAL (BAIXADA) — mantem estilo atual
# ═══════════════════════════════════════════════════════════════

_MSGS_INFORMAL_AGENDAMENTO = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e notei que nao tem uma pagina de agendamento. Quando o cliente quer marcar horario e nao consegue, acaba indo pro proximo que aparece. Posso te mostrar como ficaria uma pagina?",
    "Oi! Tudo bem? Estava olhando {artigo} {referencia} no Google e percebi que nao tem como agendar online. Percebeu que muitos clientes desistem quando nao conseguem marcar facil? Posso te mandar uma previa de como ficaria uma pagina?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Notei que nao tem uma pagina com servicos e agendamento, isso faz o cliente acabar chamando outro lugar. Quer ver como ficaria uma pagina profissional?",
]

_MSGS_INFORMAL_CARDAPIO = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e reparei que nao tem uma pagina com cardapio. Os clientes querem ver o que tem antes de pedir ou ir, sabe? Sem isso, perde venda. Quer ver como ficaria uma pagina?",
    "Oi! Tudo bem? Estava vendo {artigo} {referencia} no Google e notei que nao tem o cardapio online. As pessoas pesquisam antes de decidir onde pedir, sem cardapio, elas vao pro concorrente. Posso te mandar uma previa?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Quem busca por ai quer ver o cardapio e fazer pedido facil, mas como nao tem pagina, acaba escolhendo outro lugar. Quer que eu te mostre como ficaria?",
]

_MSGS_INFORMAL_PRESENCA = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e notei que nao tem um site. Quem pesquisa online acaba achando o concorrente primeiro. Posso te mostrar como ficaria uma pagina profissional?",
    "Oi! Tudo bem? Estava olhando {artigo} {referencia} no Google e percebi que nao tem presenca online. Quando o cliente pesquisa e nao acha nada, ele vai pra quem tem. Quer ver como ficaria uma pagina?",
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Sem uma pagina online, quem pesquisa acaba encontrando o concorrente. Posso te mandar uma previa de como ficaria uma pagina pro seu negocio?",
]

_FOLLOWUP_INFORMAL_1 = "Oi, tudo bem? Te mandei uma mensagem sobre uma pagina profissional para {artigo} {referencia}. Se tiver interesse, posso te mandar um exemplo. Sem compromisso."
_FOLLOWUP_INFORMAL_2 = "Oi! Ultimo contato sobre {artigo} {referencia}. Se nao for o momento, tudo bem. Se quiser ver como ficaria uma pagina, e so me avisar."


# ═══════════════════════════════════════════════════════════════
# CONSULTIVO (RIO PREMIUM) — tom profissional e elegante
# ═══════════════════════════════════════════════════════════════

_MSGS_CONSULTIVO_AGENDAMENTO = [
    "Boa tarde. Encontrei {artigo} {referencia} no Google e percebi que nao ha uma pagina com informacoes de agendamento. Considerando o padrao do seu negocio, uma pagina profissional poderia facilitar bastante o acesso dos clientes. Posso enviar uma proposta visual de como ficaria?",
    "Boa tarde. Vi {artigo} {referencia} no Google e observei que nao ha como agendar horario online. Clientes que buscam praticidade acabam optando por negocios que oferecem esse recurso. Posso te mostrar como ficaria uma pagina profissional?",
    "Boa tarde. Encontrei {artigo} {referencia} no Google. Notei que nao ha uma pagina com servicos e agendamento, o que pode fazer com que o cliente busque outra opcao. Posso te mandar um exemplo de como ficaria?",
]

_MSGS_CONSULTIVO_CLINICA = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google e percebi que voceis tem uma boa presenca local. Trabalho criando paginas profissionais para clinicas e servicos premium, com apresentacao dos tratamentos, fotos, localizacao e botao direto para WhatsApp. Posso te mandar um exemplo de como ficaria?",
    "Oi, tudo bem? Encontrei {artigo} {referencia} no Google. Considerando o nivel do seu servico, uma pagina com informacoes completas sobre tratamentos e agendamento poderia agregar bastante valor. Posso enviar uma proposta visual?",
]

_MSGS_CONSULTIVO_PROFISSIONAL = [
    "Oi, tudo bem? Vi {artigo} {referencia} no Google. Trabalho criando paginas profissionais para servicos locais, com apresentacao objetiva, areas de atuacao, localizacao e contato direto pelo WhatsApp. Posso te mandar um exemplo?",
    "Oi, tudo bem? Encontrei {artigo} {referencia} no Google. Uma pagina profissional com informacoes de servicos e contato facilita bastante a decisao do cliente. Posso te enviar uma proposta visual?",
]

_MSGS_CONSULTIVO_CARDAPIO = [
    "Boa tarde. Encontrei {artigo} {referencia} no Google e notei que nao ha uma pagina com cardapio ou reservas. Clientes que buscam praticidade preferem estabelecimentos com essas informacoes disponiveis. Posso te mostrar como ficaria uma pagina?",
    "Boa tarde. Vi {artigo} {referencia} no Google. Uma pagina com cardapio, fotos e reserva online pode facilitar bastante a experiencia do cliente. Posso enviar uma proposta visual?",
]

_MSGS_CONSULTIVO_PRESENCA = [
    "Boa tarde. Encontrei {artigo} {referencia} no Google e notei que nao ha uma pagina profissional com informacoes do negocio. Considerando o padrao do seu estabelecimento, uma presenca online completa poderia reforcar a credibilidade. Posso enviar uma proposta visual?",
    "Boa tarde. Vi {artigo} {referencia} no Google. Sem uma pagina profissional, clientes que pesquisam podem acabar encontrando concorrentes primeiro. Posso te mostrar como ficaria uma pagina para o seu negocio?",
]

_FOLLOWUP_CONSULTIVO_1 = "Boa tarde. Entrei em contato anteriormente sobre uma solucao digital para {artigo} {referencia}. Se tiver disponibilidade, posso apresentar uma proposta personalizada. Sem compromisso."
_FOLLOWUP_CONSULTIVO_2 = "Boa tarde. Ultimo contato sobre {artigo} {referencia}. Tenho uma proposta de pagina digital que pode agregar valor ao seu negocio. Caso nao seja o momento, compreendo perfeitamente."


# ═══════════════════════════════════════════════════════════════
# MAPEAMENTO NICHO -> REFERENCIA
# ═══════════════════════════════════════════════════════════════

_NICHO_REFERENCIA = {
    "estética": ("sua", "clínica de estética"),
    "estetica": ("sua", "clínica de estética"),
    "clínica de estética": ("sua", "clínica de estética"),
    "clinica de estetica": ("sua", "clínica de estética"),
    "harmonização facial": ("sua", "clínica de harmonização"),
    "harmonizacao facial": ("sua", "clínica de harmonização"),
    "salão de beleza": ("seu", "salão"),
    "salao de beleza": ("seu", "salão"),
    "salão premium": ("seu", "salão"),
    "barbearia": ("sua", "barbearia"),
    "barbearia premium": ("sua", "barbearia"),
    "dentista": ("sua", "clínica odontológica"),
    "psicólogo": ("seu", "consultório"),
    "psicologo": ("seu", "consultório"),
    "nutricionista": ("seu", "consultório"),
    "fisioterapeuta": ("sua", "clínica de fisioterapia"),
    "pilates": ("seu", "estúdio de pilates"),
    "academia": ("sua", "academia"),
    "academia boutique": ("sua", "academia"),
    "clínica médica": ("sua", "clínica"),
    "clinica medica": ("sua", "clínica"),
    "clínica veterinária": ("sua", "clínica veterinária"),
    "clinica veterinaria": ("sua", "clínica veterinária"),
    "auto escola": ("sua", "auto escola"),
    "restaurante": ("seu", "restaurante"),
    "pizzaria": ("sua", "pizzaria"),
    "confeitaria": ("sua", "confeitaria"),
    "padaria": ("sua", "padaria"),
    "lanchonete": ("sua", "lanchonete"),
    "bar": ("seu", "bar"),
    "advogado": ("seu", "escritório de advocacia"),
    "oficina mecânica": ("sua", "oficina"),
    "oficina mecanica": ("sua", "oficina"),
    "pet shop": ("seu", "pet shop"),
    "spa": ("seu", "spa"),
    "depilação a laser": ("sua", "clínica de depilação"),
    "depilacao a laser": ("sua", "clínica de depilação"),
    "micropigmentação": ("sua", "clínica de micropigmentação"),
    "micropigmentacao": ("sua", "clínica de micropigmentação"),
    "studio de sobrancelha": ("seu", "studio de sobrancelha"),
    "studio de cílios": ("seu", "studio de cílios"),
    "lash designer": ("sua", "lash designer"),
    "personal trainer": ("seu", "personal trainer"),
    "arquiteto": ("seu", "escritório de arquitetura"),
    "designer de interiores": ("seu", "escritório de design"),
    "fotógrafo": ("seu", "estúdio de fotografia"),
    "fotografo": ("seu", "estúdio de fotografia"),
    "consultório": ("seu", "consultório"),
    "consultorio": ("seu", "consultório"),
    "hotel boutique": ("seu", "hotel"),
    "pousada": ("sua", "pousada"),
    "escola": ("sua", "escola"),
    "curso livre": ("seu", "curso"),
}


def _get_referencia(nicho: str) -> tuple[str, str]:
    """Retorna (artigo, referencia) para o nicho."""
    nicho_lower = (nicho or "").lower().strip()
    return _NICHO_REFERENCIA.get(nicho_lower, ("seu", "estabelecimento"))


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
    """Verifica se o nicho e de profissional liberal."""
    nicho_lower = (nicho or "").lower()
    profissionais = [
        "advogado", "psicólogo", "psicologo", "nutricionista",
        "arquiteto", "fotógrafo", "fotografo", "designer de interiores",
        "personal trainer", "consultório", "consultorio",
    ]
    return any(p in nicho_lower for p in profissionais)


import random


def gerar_mensagem_whatsapp(lead: dict, regiao: RegiaoConfig) -> str:
    """
    Gera mensagem de WhatsApp baseada no tom da regiao e nicho do lead.

    - Informal (baixada): casual e amigavel
    - Consultivo (rio_premium): profissional e elegante
    """
    nome = lead.get("nome", "")
    nicho = lead.get("nicho") or lead.get("categoria") or ""
    tipo = lead.get("_tipo") or lead.get("tipo_pagina") or ""

    artigo, referencia = _get_referencia(nicho)

    # Se nao tem tipo definido, inferir pelo nicho
    if not tipo:
        tipo = regiao.nicho_tipo.get(nicho.lower(), "presença")

    if regiao.msg_tone == "consultivo":
        # Rio Premium: tom consultivo
        if _is_nicho_clinica(nicho):
            msg = random.choice(_MSGS_CONSULTIVO_CLINICA)
        elif _is_nicho_profissional(nicho):
            msg = random.choice(_MSGS_CONSULTIVO_PROFISSIONAL)
        elif tipo == "cardápio":
            msg = random.choice(_MSGS_CONSULTIVO_CARDAPIO)
        elif tipo == "agendamento":
            msg = random.choice(_MSGS_CONSULTIVO_AGENDAMENTO)
        else:
            msg = random.choice(_MSGS_CONSULTIVO_PRESENCA)
    else:
        # Baixada: tom informal
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

    if regiao.msg_tone == "consultivo":
        return _FOLLOWUP_CONSULTIVO_1.format(artigo=artigo, referencia=referencia)
    return _FOLLOWUP_INFORMAL_1.format(artigo=artigo, referencia=referencia)


def gerar_followup_2(lead: dict, regiao: RegiaoConfig) -> str:
    """Gera 3a mensagem de follow-up (ultima)."""
    nicho = lead.get("nicho") or lead.get("categoria") or ""
    artigo, referencia = _get_referencia(nicho)

    if regiao.msg_tone == "consultivo":
        return _FOLLOWUP_CONSULTIVO_2.format(artigo=artigo, referencia=referencia)
    return _FOLLOWUP_INFORMAL_2.format(artigo=artigo, referencia=referencia)