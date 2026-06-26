"""
Testes do modo AVGESTAO.

Roda de duas formas:
    python tests/test_avgestao.py      (asserts puros, sem dependencias)
    pytest tests/test_avgestao.py      (se pytest estiver instalado)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.avgestao import (
    GRUPOS,
    get_grupo,
    resolver_grupo,
    listar_grupos,
    consultar_subnichos,
    gerar_consultas_meta,
    detectar_grupo_subnicho,
    classificar_faz_assistencia,
    FAZ_ASSISTENCIA_CONFIRMADO,
    FAZ_ASSISTENCIA_PROVAVEL,
    FAZ_ASSISTENCIA_NAO,
    calcular_score_avgestao,
    chave_dedup,
    deduplicar_leads,
    gerar_mensagem_avgestao,
    gerar_link_whatsapp_avgestao,
    gerar_nome_curto,
    enriquecer_lead_avgestao,
    filtrar_por_grupo,
    filtrar_por_cidade,
    linha_xlsx_avgestao,
    prioridade_avgestao,
    COLUNAS_XLSX_AVGESTAO,
    normalizar_texto,
    tokenizar_sem_stopwords,
    _match_query,
    _MENSAGENS_POR_CAT,
    _followup1,
    _followup2,
    _msg_oficina_mecanica,
    _msg_assistencia_tecnica,
    _msg_oficina_producao,
    _msg_prestador_servico,
    _msg_ar_refrigeracao,
    _msg_seguranca,
)
from utils.phone_utils import normalizar_telefone_br


# ── Helpers ────────────────────────────────────────────────────────

def _lead(**kwargs):
    base = {
        "nome": "",
        "categoria": "",
        "nicho": "",
        "subnicho": "",
        "endereco": "",
        "cidade": "",
        "telefone": "",
        "whatsapp": "",
        "instagram": "",
        "url_site": "",
        "tem_site": "False",
        "num_avaliacoes": "0",
        "avaliacao": "0",
    }
    base.update(kwargs)
    return base


# ── Normalizacao de telefone ───────────────────────────────────────

def test_normalizar_telefone_celular_ddd():
    assert normalizar_telefone_br("21999999999") == "5521999999999"


def test_normalizar_telefone_com_mascara():
    assert normalizar_telefone_br("(21) 99999-9999") == "5521999999999"


def test_normalizar_telefone_com_55():
    assert normalizar_telefone_br("5521999999999") == "5521999999999"


def test_normalizar_telefone_zero_inicial():
    assert normalizar_telefone_br("021999999999") == "5521999999999"


def test_normalizar_telefone_fixo():
    assert normalizar_telefone_br("2133333333") == "552133333333"


def test_normalizar_telefone_sem_ddd():
    assert normalizar_telefone_br("999999999") is None


def test_normalizar_telefone_vazio():
    assert normalizar_telefone_br("") is None
    assert normalizar_telefone_br(None) is None


# ── Grupos e subnichos ─────────────────────────────────────────────

def test_cinco_grupos_definidos():
    assert set(listar_grupos()) == {
        "assistencias", "refrigeracao", "automotivo",
        "sob_medida", "servicos_externos",
    }


def test_get_grupo_existente():
    g = get_grupo("assistencias")
    assert g.key == "assistencias"
    assert len(g.subnichos) == 6


def test_get_grupo_inexistente():
    try:
        get_grupo("inexistente")
        assert False, "deveria ter lancado ValueError"
    except ValueError:
        assert True


def test_resolver_grupo_todos():
    assert len(resolver_grupo("todos")) == 5
    assert len(resolver_grupo(None)) == 5


def test_resolver_grupo_unico():
    assert len(resolver_grupo("refrigeracao")) == 1


def test_consultar_subnichos_tem_cidade():
    consultas = consultar_subnichos("automotivo", "Nova Iguacu, RJ")
    assert len(consultas) == 5
    query, sub, cat = consultas[0]
    assert "Nova Iguacu, RJ" in query
    assert sub == "Oficina mecânica"
    assert cat == "oficina_mecanica"


def test_detectar_grupo_subnicho():
    lead = _lead(nome="Tech Cel Assistencia Tecnica", categoria="assistencia tecnica de celular")
    grupo, sub = detectar_grupo_subnicho(lead)
    assert grupo == "assistencias"
    assert "celular" in sub.lower()


def test_detectar_grupo_subnicho_nao_encontrado():
    lead = _lead(nome="Padaria Sao Joao", categoria="padaria")
    grupo, sub = detectar_grupo_subnicho(lead)
    assert grupo == ""
    assert sub == ""


# ── Classificacao faz_assistencia ──────────────────────────────────

def test_faz_assistencia_confirmado():
    lead = _lead(nome="Conserto de Celular Tech", categoria="conserto de celular")
    assert classificar_faz_assistencia(lead) == FAZ_ASSISTENCIA_CONFIRMADO


def test_faz_assistencia_confirmado_manutencao():
    lead = _lead(nome="Ar Clima Manutencao", categoria="manutencao de ar condicionado")
    assert classificar_faz_assistencia(lead) == FAZ_ASSISTENCIA_CONFIRMADO


def test_faz_assistencia_provavel_grupo():
    lead = _lead(nome="Oficina do Joao", categoria="oficina mecanica")
    assert classificar_faz_assistencia(lead) == FAZ_ASSISTENCIA_PROVAVEL


def test_faz_assistencia_nao_confirmado():
    lead = _lead(nome="Loja de Moveis ABC", categoria="moveis")
    assert classificar_faz_assistencia(lead) == FAZ_ASSISTENCIA_NAO


# ── Score AVGESTAO ─────────────────────────────────────────────────

def test_score_lead_bom_assistencia():
    lead = _lead(
        nome="Tech Cel Assistencia Tecnica",
        categoria="assistencia tecnica de celular",
        cidade="Nova Iguacu",
        telefone="(21) 99999-9999",
        whatsapp="21999999999",
        endereco="Rua A, 123 - Centro",
        num_avaliacoes="45",
        instagram="@techcel",
    )
    r = calcular_score_avgestao(lead)
    assert r.score >= 70, f"esperado >=70, got {r.score} | {r.motivos}"
    assert 0 <= r.score <= 100
    assert any("+30" in m for m in r.motivos)


def test_score_nicho_compativel_30_pontos():
    lead = _lead(nome="Oficina Mecanica do Zé", categoria="oficina mecanica")
    r = calcular_score_avgestao(lead)
    assert any("nicho principal compativel (+30)" in m for m in r.motivos)


def test_score_20_avaliacoes_15_pontos():
    lead = _lead(nome="X", categoria="oficina mecanica", num_avaliacoes="25")
    r = calcular_score_avgestao(lead)
    assert any("avaliacoes (+15)" in m for m in r.motivos)


def test_score_menos_20_avaliacoes_sem_bonus():
    lead = _lead(nome="X", categoria="oficina mecanica", num_avaliacoes="10")
    r = calcular_score_avgestao(lead)
    assert not any("avaliacoes (+15)" in m for m in r.motivos)


def test_score_penalidade_franquia():
    lead = _lead(nome="McDonald's Loja 123", categoria="restaurante")
    r = calcular_score_avgestao(lead)
    assert any("(-30)" in m for m in r.motivos)


def test_score_penalidade_varejista():
    lead = _lead(nome="Loja de Vendas de Moveis", categoria="loja de moveis")
    r = calcular_score_avgestao(lead)
    assert any("varejista (-25)" in m for m in r.motivos)


def test_score_penalidade_sem_telefone():
    lead = _lead(nome="X Assistencia", categoria="assistencia tecnica de celular", telefone="")
    r = calcular_score_avgestao(lead)
    assert any("sem telefone (-20)" in m for m in r.motivos)


def test_score_site_nao_penaliza():
    lead_com_site = _lead(
        nome="Tech Cel Assistencia",
        categoria="assistencia tecnica de celular",
        cidade="Nova Iguacu",
        telefone="21999999999",
        url_site="https://techcel.com.br",
        tem_site="True",
        num_avaliacoes="30",
        endereco="Rua A",
    )
    r = calcular_score_avgestao(lead_com_site)
    assert not any(m.strip().startswith("site") and "-" in m for m in r.motivos), \
        "site nao deve gerar penalidade"
    assert any("site ou instagram (+5)" in m for m in r.motivos)


def test_score_clamp_0_100():
    lead = _lead(nome="McDonald's", categoria="loja de vendas", telefone="")
    r = calcular_score_avgestao(lead)
    assert 0 <= r.score <= 100


def test_score_autonomo_generico_penaliza():
    lead = _lead(nome="Joao Silva", categoria="vendedor", cidade="Nova Iguacu", telefone="21999999999")
    r = calcular_score_avgestao(lead)
    assert any("autonomo" in m.lower() for m in r.motivos)


# ── Deduplicacao ───────────────────────────────────────────────────

def test_dedup_por_place_id():
    l1 = _lead(nome="A", place_id="abc123")
    l2 = _lead(nome="B", place_id="abc123")
    assert len(deduplicar_leads([l1, l2])) == 1


def test_dedup_por_url_maps():
    l1 = _lead(nome="A", link_maps="https://maps.google.com/x")
    l2 = _lead(nome="B", link_maps="https://maps.google.com/x")
    assert len(deduplicar_leads([l1, l2])) == 1


def test_dedup_por_telefone_normalizado():
    l1 = _lead(nome="A", whatsapp="(21) 99999-9999")
    l2 = _lead(nome="B", whatsapp="5521999999999")
    assert len(deduplicar_leads([l1, l2])) == 1


def test_dedup_por_nome_endereco():
    l1 = _lead(nome="Tech Cel", endereco="Rua A, 123")
    l2 = _lead(nome="Tech Cel", endereco="Rua A, 123")
    assert len(deduplicar_leads([l1, l2])) == 1


def test_dedup_mantem_distintos():
    l1 = _lead(nome="A", telefone="21999999999")
    l2 = _lead(nome="B", telefone="21888888888")
    assert len(deduplicar_leads([l1, l2])) == 2


def test_dedup_prioridade_place_id():
    l1 = _lead(nome="A", place_id="p1", whatsapp="21999999999")
    l2 = _lead(nome="B", place_id="p1", whatsapp="21888888888")
    assert len(deduplicar_leads([l1, l2])) == 1


def test_chave_dedup_estrutura():
    lead = _lead(place_id="pid", link_maps="maps", whatsapp="21999999999", nome="X", endereco="Rua A")
    pid, maps, tel, ne = chave_dedup(lead)
    assert pid == "pid"
    assert maps == "maps"
    assert tel == "5521999999999"
    assert "x|" in ne


# ── Mensagens ──────────────────────────────────────────────────────

def test_gerar_mensagem_avgestao_inicial():
    lead = _lead(nome="Tech Cel Assistencia", categoria="assistencia tecnica de celular")
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "AVGESTÃO" in msg
    assert "Tech Cel" in msg or "Tech Cel Assistencia" in msg


def test_gerar_mensagem_followup1():
    lead = _lead(nome="Oficina do Joao", categoria="oficina mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=2)
    assert "AVGESTÃO" in msg
    assert "Passei aqui" in msg


def test_gerar_mensagem_followup2():
    lead = _lead(nome="Oficina do Joao", categoria="oficina mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=3)
    assert "última mensagem" in msg or "último contato" in msg


def test_gerar_link_whatsapp_avgestao():
    lead = _lead(nome="Tech Cel", whatsapp="21999999999", categoria="assistencia tecnica de celular")
    link = gerar_link_whatsapp_avgestao(lead, tentativa=1)
    assert link.startswith("https://wa.me/5521999999999?text=")


def test_gerar_link_whatsapp_sem_telefone():
    lead = _lead(nome="Tech Cel", telefone="", whatsapp="")
    assert gerar_link_whatsapp_avgestao(lead) == ""


def test_mensagem_por_grupo_automotivo():
    lead = _lead(nome="Oficina Mec", grupo="automotivo", subnicho="oficina_mecanica", msg_cat="oficina_mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "oficinas" in msg.lower() or "veículo" in msg.lower()


def test_mensagem_por_grupo_refrigeracao():
    lead = _lead(nome="Ar Clima", grupo="refrigeracao", subnicho="ar_condicionado", msg_cat="ar_refrigeracao")
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "refrigeração" in msg.lower() or "manutenção" in msg.lower()


# ── Nome curto ─────────────────────────────────────────────────────

def test_nome_curto_simples():
    assert gerar_nome_curto(_lead(nome="Tech Cel")) == "Tech Cel"


def test_nome_curto_com_traco():
    assert gerar_nome_curto(_lead(nome="Tech Cel - Centro - Nova Iguacu")) == "Tech Cel"


def test_nome_curto_vazio():
    assert gerar_nome_curto(_lead(nome="")) == "empresa"


def test_nome_curto_longo():
    nome = "Assistencia Tecnica Especializada em Celulares e Tablets do Centro"
    curto = gerar_nome_curto(_lead(nome=nome))
    assert len(curto) <= 40


# ── Enriquecimento ─────────────────────────────────────────────────

def test_enriquecer_lead_avgestao():
    lead = _lead(
        nome="Tech Cel Assistencia Tecnica",
        categoria="assistencia tecnica de celular",
        cidade="Nova Iguacu",
        whatsapp="21999999999",
        num_avaliacoes="30",
        endereco="Rua A",
    )
    e = enriquecer_lead_avgestao(lead)
    assert e["grupo"] == "assistencias"
    assert "celular" in e["subnicho"].lower()
    assert e["faz_assistencia"] == FAZ_ASSISTENCIA_CONFIRMADO
    assert "score_avgestao" in e
    assert 0 <= e["score_avgestao"] <= 100
    assert e["mensagem_inicial"]
    assert e["link_whatsapp"].startswith("https://wa.me/")
    assert e["nome_curto"]


# ── Filtros por grupo e cidade ─────────────────────────────────────

def test_filtrar_por_grupo():
    leads = [
        _lead(nome="A", categoria="oficina mecanica"),
        _lead(nome="B", categoria="assistencia tecnica de celular"),
        _lead(nome="C", categoria="padaria"),
    ]
    assert len(filtrar_por_grupo(leads, "automotivo")) == 1
    assert len(filtrar_por_grupo(leads, "assistencias")) == 1


def test_filtrar_por_cidade():
    leads = [
        _lead(nome="A", cidade="Nova Iguacu, RJ"),
        _lead(nome="B", cidade="Duque de Caxias, RJ"),
        _lead(nome="C", cidade="nova iguacu"),
    ]
    assert len(filtrar_por_cidade(leads, "Nova Iguacu, RJ")) == 2


def test_filtrar_por_cidade_vazia_mantem_tudo():
    leads = [_lead(nome="A", cidade="X"), _lead(nome="B", cidade="Y")]
    assert len(filtrar_por_cidade(leads, "")) == 2


# ── XLSX helpers ───────────────────────────────────────────────────

def test_colunas_xlsx_avgestao_especificadas():
    headers = [c[0] for c in COLUNAS_XLSX_AVGESTAO]
    esperado = [
        "Nome", "Nome curto", "Cidade", "Nicho", "Subnicho",
        "Telefone", "WhatsApp", "Instagram", "Site", "Avaliação",
        "Quantidade de avaliações", "Faz assistência", "Score AVGESTÃO",
        "Motivos do score", "Mensagem inicial", "Link WhatsApp",
        "Status", "Data da abordagem", "Follow-up 1", "Follow-up 2",
    ]
    assert headers == esperado


def test_linha_xlsx_avgestao_campos():
    lead = _lead(
        nome="Tech Cel Assistencia",
        categoria="assistencia tecnica de celular",
        cidade="Nova Iguacu",
        whatsapp="21999999999",
        num_avaliacoes="30",
    )
    linha = linha_xlsx_avgestao(lead)
    assert linha["Status"] == "novo"
    assert linha["Data da abordagem"] == ""
    assert "AVGESTÃO" in linha["Mensagem inicial"]
    assert "AVGESTÃO" in linha["Follow-up 1"]
    assert "última" in linha["Follow-up 2"]
    assert isinstance(linha["Score AVGESTÃO"], int)


def test_prioridade_avgestao():
    assert prioridade_avgestao(80) == "Alta"
    assert prioridade_avgestao(70) == "Alta"
    assert prioridade_avgestao(55) == "Média"
    assert prioridade_avgestao(40) == "Média"
    assert prioridade_avgestao(20) == "Baixa"


# ── Regressoes ─────────────────────────────────────────────────────

def test_enriquecer_preserva_subnicho_da_fonte():
    lead = _lead(
        nome="Ar Clima Refrigeracao",
        categoria="ar condicionado",
        subnicho="manutencao de ar condicionado",
        cidade="Duque de Caxias",
        whatsapp="21888888888",
        num_avaliacoes="30",
        endereco="Rua B 222",
    )
    e = enriquecer_lead_avgestao(lead)
    assert "manutencao" in e["subnicho"].lower(), \
        f"subnicho da fonte deve ser preservado, got '{e['subnicho']}'"


def test_autonomo_nao_penaliza_empresa_de_grupo():
    lead = _lead(
        nome="Ar Clima Refrigeracao",
        categoria="ar condicionado",
        subnicho="manutencao de ar condicionado",
        cidade="Duque de Caxias",
        whatsapp="21888888888",
        num_avaliacoes="30",
        endereco="Rua B 222",
    )
    r = calcular_score_avgestao(lead)
    assert not any("autonomo" in m.lower() for m in r.motivos), \
        f"empresa de grupo valido nao deve ter penalidade autonomo: {r.motivos}"
    assert r.score >= 85, f"esperado >=85, got {r.score} | {r.motivos}"


def test_autonomo_penaliza_generico_sem_grupo():
    lead = _lead(nome="Joao Silva", categoria="vendedor", cidade="Nova Iguacu", telefone="21999999999")
    r = calcular_score_avgestao(lead)
    assert any("autonomo" in m.lower() for m in r.motivos)


# ── Normalizacao de texto (novos casos) ────────────────────────────

def test_normalizar_texto_none():
    assert normalizar_texto(None) == ""


def test_normalizar_texto_com_acentos():
    assert normalizar_texto("Assistência Técnica") == "assistencia tecnica"


def test_normalizar_texto_sem_acentos():
    assert normalizar_texto("Assistencia Tecnica") == "assistencia tecnica"


def test_normalizar_texto_acentos_igual_sem_acentos():
    assert normalizar_texto("Manutenção de Ar-Condicionado") == normalizar_texto("Manutencao de Ar Condicionado")


def test_normalizar_texto_remove_pontuacao():
    assert normalizar_texto("Clima Forte - Manutenção & Instalação") == "clima forte manutencao instalacao"


def test_normalizar_texto_normaliza_espacos():
    assert normalizar_texto("  vários   espaços  ") == "varios espacos"


def test_tokenizar_sem_stopwords():
    tokens = tokenizar_sem_stopwords("manutenção de ar condicionado em Nova Iguaçu")
    assert "de" not in tokens
    assert "em" not in tokens
    assert "manutencao" in tokens
    assert "condicionado" in tokens


# ─_ Correspondencia de queries (novos casos) ───────────────────────

def test_match_query_assistencia_com_acentos():
    assert _match_query("assistência técnica de celular", "Assistência Técnica Celular Center")


def test_match_query_assistencia_sem_acentos():
    assert _match_query("assistencia tecnica de celular", "Assistência Técnica Celular Center")


def test_match_query_refrigeracao_composto():
    assert _match_query(
        "manutenção de ar-condicionado",
        "Clima Forte Manutenção e Instalação de Ar Condicionado",
    )


def test_match_query_oficina_motos():
    assert _match_query("oficina de motos", "Motosul Oficina e Peças")


def test_match_query_false_padaria():
    assert not _match_query("oficina mecanica", "Padaria Sao Joao")


# ── Metadados explicitos (novos casos) ─────────────────────────────

def test_gerar_consultas_meta_tem_metadados():
    consultas = gerar_consultas_meta("assistencias", "Duque de Caxias, RJ")
    assert len(consultas) == 6
    c0 = consultas[0]
    assert c0["query"] == "assistencia tecnica de celular em Duque de Caxias, RJ"
    assert c0["grupo"] == "assistencias"
    assert c0["subnicho"] == "celular"
    assert c0["msg_cat"] == "assistencia_tecnica"
    assert "subnicho_label" in c0


def test_enriquecer_preserva_grupo_subnicho_da_consulta():
    lead = _lead(
        nome="Assistência Técnica Celular Center",
        categoria="",
        grupo="assistencias",
        subnicho="celular",
        msg_cat="assistencia_tecnica",
        cidade="Duque de Caxias",
        whatsapp="21999999999",
        num_avaliacoes="30",
        endereco="Rua A",
    )
    e = enriquecer_lead_avgestao(lead)
    assert e["grupo"] == "assistencias"
    assert e["subnicho"] == "celular"
    assert e["msg_cat"] == "assistencia_tecnica"


def test_precedencia_metadados_sobre_inferencia():
    """Lead com grupo explicito mas nome que nao bate com _match_query."""
    lead = _lead(
        nome="Motosul Centro Automotivo",
        categoria="centro automotivo",
        grupo="automotivo",
        subnicho="motos",
        msg_cat="oficina_mecanica",
        cidade="Nova Iguacu",
        whatsapp="21888888888",
        num_avaliacoes="20",
        endereco="Rua B",
    )
    e = enriquecer_lead_avgestao(lead)
    assert e["grupo"] == "automotivo"
    assert e["msg_cat"] == "oficina_mecanica"


def test_detectar_grupo_usa_grupo_explicito():
    lead = _lead(nome="Empresa X", categoria="", grupo="refrigeracao", subnicho="ar_condicionado")
    g, s = detectar_grupo_subnicho(lead)
    assert g == "refrigeracao"


def test_enriquecer_grupo_explicito_nao_eh_sobrescrito_por_inferencia():
    """Mesmo se _match_query encontrar grupo diferente, o explicito prevalece."""
    lead = _lead(
        nome="Oficina Mecânica do Zé",
        categoria="oficina mecanica",
        grupo="automotivo",
        subnicho="oficina_mecanica",
        msg_cat="oficina_mecanica",
    )
    e = enriquecer_lead_avgestao(lead)
    assert e["grupo"] == "automotivo"
    assert e["msg_cat"] == "oficina_mecanica"


# ── Templates de mensagem corretos (novos casos) ───────────────────

def test_template_assistencia_tecnica_gerado():
    lead = _lead(
        nome="Tech Cel",
        grupo="assistencias",
        subnicho="celular",
        msg_cat="assistencia_tecnica",
        whatsapp="21999999999",
        cidade="X",
    )
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "aparelho" in msg.lower()
    assert "assistências técnicas" in msg.lower() or "assistências" in msg.lower()
    assert "AVGESTÃO" in msg


def test_template_refrigeracao_gerado():
    lead = _lead(
        nome="Ar Clima",
        grupo="refrigeracao",
        subnicho="ar_condicionado",
        msg_cat="ar_refrigeracao",
        whatsapp="21888888888",
        cidade="X",
    )
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "refrigeração" in msg.lower() or "manutenção" in msg.lower()
    assert "AVGESTÃO" in msg


def test_todas_mensagens_tem_acentos_corretos():
    """Nenhuma mensagem comercial deve conter versoes sem acento."""
    proibidos = [
        "servicos",
        "orcamento",
        "aprovacao",
        "AVGESTAO",
        "voces ",
        "estao ",
        "sera ",
    ]
    leads_exemplo = [
        _lead(nome="X", grupo="automotivo", subnicho="oficina_mecanica", msg_cat="oficina_mecanica"),
        _lead(nome="X", grupo="assistencias", subnicho="celular", msg_cat="assistencia_tecnica"),
        _lead(nome="X", grupo="sob_medida", subnicho="vidracaria", msg_cat="oficina_producao"),
        _lead(nome="X", grupo="servicos_externos", subnicho="energia_solar", msg_cat="prestador_servico"),
        _lead(nome="X", grupo="refrigeracao", subnicho="ar_condicionado", msg_cat="ar_refrigeracao"),
        _lead(nome="X", grupo="servicos_externos", subnicho="seguranca", msg_cat="seguranca"),
    ]
    for lead in leads_exemplo:
        for tentativa in (1, 2, 3):
            msg = gerar_mensagem_avgestao(lead, tentativa=tentativa)
            for proibido in proibidos:
                assert proibido not in msg, \
                    f"mensagem (tentativa={tentativa}, cat={lead['msg_cat']}) contem '{proibido}'"


def test_url_whatsapp_codifica_acentos():
    lead = _lead(
        nome="Tech Cel",
        grupo="assistencias",
        subnicho="celular",
        msg_cat="assistencia_tecnica",
        whatsapp="21999999999",
        cidade="X",
    )
    link = gerar_link_whatsapp_avgestao(lead, tentativa=1)
    assert link.startswith("https://wa.me/5521999999999?text=")
    from urllib.parse import unquote
    msg_decodificada = unquote(link.split("?text=")[1])
    assert "AVGESTÃO" in msg_decodificada
    assert "serviços" in msg_decodificada or "orçamento" in msg_decodificada


def test_todos_templates_por_cat_existem():
    cats_esperadas = {
        "oficina_mecanica", "assistencia_tecnica", "oficina_producao",
        "prestador_servico", "ar_refrigeracao", "seguranca",
    }
    assert set(_MENSAGENS_POR_CAT.keys()) == cats_esperadas


# ── Testes comerciais das novas mensagens curtas ───────────────────

def _msg_stats(msg):
    """Retorna (palavras, caracteres) ignorando quebras de linha duplas."""
    palavras = len(msg.split())
    caracteres = len(msg)
    return palavras, caracteres


_CATS_MSG = [
    ("automotivo", "oficina_mecanica", "oficina_mecanica", _msg_oficina_mecanica),
    ("assistencias", "assistencia_tecnica", "celular", _msg_assistencia_tecnica),
    ("sob_medida", "oficina_producao", "vidracaria", _msg_oficina_producao),
    ("servicos_externos", "prestador_servico", "energia_solar", _msg_prestador_servico),
    ("refrigeracao", "ar_refrigeracao", "ar_condicionado", _msg_ar_refrigeracao),
    ("servicos_externos", "seguranca", "seguranca", _msg_seguranca),
]


def test_cada_grupo_usa_template_correto():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        assert msg_cat in _MENSAGENS_POR_CAT, f"{msg_cat} deve existir em _MENSAGENS_POR_CAT"
        assert callable(_MENSAGENS_POR_CAT[msg_cat])


def test_mensagem_curta_ate_600_caracteres():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        palavras, caracteres = _msg_stats(msg)
        assert caracteres <= 600, \
            f"{msg_cat}: {caracteres} caracteres (max 600)"


def test_mensagem_menciona_criador_avgestao():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        assert "criador do AVGESTÃO" in msg, f"{msg_cat} deve mencionar 'criador do AVGESTÃO'"


def test_mensagem_menciona_15_dias():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        assert "15 dias" in msg, f"{msg_cat} deve mencionar '15 dias'"


def test_mensagem_termina_oferecendo_acesso():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        linhas = msg.strip().split("\n\n")
        ultima = linhas[-1].strip()
        assert "acesso" in ultima.lower() or "liberar" in ultima.lower(), \
            f"{msg_cat}: ultima linha deve oferecer acesso: '{ultima}'"


def test_mensagem_usa_nome_curto():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        assert "Loja Teste" in msg, f"{msg_cat} deve conter o nome curto do comercio"


def test_mensagem_nao_oferece_foto_video_demo():
    for grupo_key, msg_cat, subnicho_key, fn in _CATS_MSG:
        msg = fn("Loja Teste")
        msg_lower = msg.lower()
        assert "foto" not in msg_lower, f"{msg_cat} nao deve oferecer foto"
        assert "vídeo" not in msg_lower and "video" not in msg_lower, \
            f"{msg_cat} nao deve oferecer video"
        assert "demonstração" not in msg_lower and "demonstracao" not in msg_lower, \
            f"{msg_cat} nao deve oferecer demonstracao"


def test_followup1_max_70_palavras():
    msg = _followup1("Loja Teste")
    palavras, caracteres = _msg_stats(msg)
    assert caracteres <= 450, f"followup1: {caracteres} chars (max ~450)"
    assert palavras <= 70, f"followup1: {palavras} palavras (max 70)"


def test_followup2_max_75_palavras():
    msg = _followup2("Loja Teste")
    palavras, caracteres = _msg_stats(msg)
    assert caracteres <= 450, f"followup2: {caracteres} chars (max ~450)"
    assert palavras <= 75, f"followup2: {palavras} palavras (max 75)"


# ── Regressao completa do modo landing pages ───────────────────────

def test_landing_pages_nao_usa_score_avgestao():
    """O modo landing pages deve continuar usando calcular_score (LP), nao score_avgestao."""
    import prospectar_leads
    lead_lp = {
        "nome": "Salao de Beleza A",
        "categoria": "salão de beleza",
        "cidade": "Nova Iguacu",
        "telefone": "21999999999",
        "tem_site": "False",
        "num_avaliacoes": "30",
        "avaliacao": "4.5",
    }
    score_lp = prospectar_leads.calcular_score(lead_lp)
    assert "score_avgestao" not in lead_lp
    assert 0 <= score_lp <= 100


def test_landing_pages_prospectar_default_funciona():
    """O prospectar_leads sem --produto avgestao nao deve enriquecer com campos avgestao."""
    import prospectar_leads
    lead = {
        "nome": "Barbearia Corte",
        "categoria": "barbearia",
        "cidade": "Duque de Caxias",
        "telefone": "21999999999",
        "tem_site": "False",
        "num_avaliacoes": "20",
        "avaliacao": "4.5",
        "instagram": "@corte",
    }
    score = prospectar_leads.calcular_score(lead)
    assert score > 0
    assert "score_avgestao" not in lead
    assert "faz_assistencia" not in lead


# ── Runner manual ──────────────────────────────────────────────────

def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passou = 0
    falhou = 0
    for fn in fns:
        try:
            fn()
            passou += 1
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            falhou += 1
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            falhou += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
