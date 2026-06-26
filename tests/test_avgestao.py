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
    assert "AVGESTAO" in msg
    assert "Tech Cel" in msg


def test_gerar_mensagem_followup1():
    lead = _lead(nome="Oficina do Joao", categoria="oficina mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=2)
    assert "se conseguiram ver" in msg


def test_gerar_mensagem_followup2():
    lead = _lead(nome="Oficina do Joao", categoria="oficina mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=3)
    assert "ultimo contato" in msg


def test_gerar_link_whatsapp_avgestao():
    lead = _lead(nome="Tech Cel", whatsapp="21999999999", categoria="assistencia tecnica de celular")
    link = gerar_link_whatsapp_avgestao(lead, tentativa=1)
    assert link.startswith("https://wa.me/5521999999999?text=")


def test_gerar_link_whatsapp_sem_telefone():
    lead = _lead(nome="Tech Cel", telefone="", whatsapp="")
    assert gerar_link_whatsapp_avgestao(lead) == ""


def test_mensagem_por_grupo_automotivo():
    lead = _lead(nome="Oficina Mec", categoria="oficina mecanica")
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "oficina" in msg.lower() or "veiculo" in msg.lower()


def test_mensagem_por_grupo_refrigeracao():
    lead = _lead(nome="Ar Clima", categoria="refrigeracao")
    msg = gerar_mensagem_avgestao(lead, tentativa=1)
    assert "refrigeracao" in msg.lower() or "climatizacao" in msg.lower() or "manutencao" in msg.lower()


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
    assert "AVGESTAO" in linha["Mensagem inicial"]
    assert "se conseguiram ver" in linha["Follow-up 1"]
    assert "ultimo contato" in linha["Follow-up 2"]
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
