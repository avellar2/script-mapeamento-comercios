"""
Testes de config/dedup.py (dedup global em dois tempos, 5 niveis).

Roda de duas formas:
    py -3.12 tests/test_dedup.py
    pytest tests/test_dedup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.dedup import (
    chave_dedup_global,
    IndexadorDedup,
    deduplicar_leads_global,
    mesclar_chaves_existentes,
)
from config.avgestao import deduplicar_leads


def _lead(**kw):
    base = {
        "nome": "", "cidade": "", "endereco": "", "telefone": "",
        "whatsapp": "", "place_id": "", "link_maps": "",
    }
    base.update(kw)
    return base


# ── chaves ─────────────────────────────────────────────────────────

def test_chave_dedup_global_tem_5_niveis():
    ch = chave_dedup_global(_lead(place_id="ChIJ123", link_maps="https://m/abc",
                                  whatsapp="21999999999",
                                  nome="Tech Cel", endereco="Rua X",
                                  cidade="Nova Iguaçu"))
    assert ch["place_id"]
    assert ch["maps_url"]
    assert ch["telefone"] == "5521999999999"
    assert ch["nome_endereco"] == "tech cel|rua x"
    assert ch["nome_cidade"] == "tech cel|nova iguacu"
    assert ch["has_strong"] is True


def test_chave_dedup_global_sem_fortes_tem_nome_cidade():
    ch = chave_dedup_global(_lead(nome="João Silva", cidade="Niterói"))
    assert ch["has_strong"] is False
    assert ch["nome_endereco"] == ""
    assert ch["nome_cidade"] == "joao silva|niteroi"


# ── dois tempos: fortes ─────────────────────────────────────────────

def test_place_id_deduplica():
    idx = IndexadorDedup()
    a = _lead(place_id="ChIJ1", nome="A", cidade="RJ")
    b = _lead(place_id="ChIJ1", nome="A", cidade="RJ")
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_maps_url_deduplica():
    idx = IndexadorDedup()
    a = _lead(link_maps="https://google.com/maps/place?q=1", nome="A", cidade="RJ")
    b = _lead(link_maps="https://google.com/maps/place", nome="A", cidade="RJ")
    # query string de busca (q) removida -> mesma maps_url canonica -> dup
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_maps_url_preserva_id_nao_colapsa():
    """?id=ChIJ e identificador de place — preservar; nao colapsar URLs distintas."""
    idx = IndexadorDedup()
    a = _lead(link_maps="https://maps.google.com/?id=ChIJ111", nome="A", cidade="RJ")
    b = _lead(link_maps="https://maps.google.com/?id=ChIJ222", nome="B", cidade="RJ")
    assert idx.add(a) is True
    # place_id ausente, mas maps_url (?id=) distinto -> NAO eh duplicata
    assert idx.add(b) is True


def test_maps_url_id_igual_deduplica():
    """Mesmo ?id= -> mesma maps_url canonica -> duplicata."""
    idx = IndexadorDedup()
    a = _lead(link_maps="https://maps.google.com/?id=ChIJ111&hl=pt", nome="A", cidade="RJ")
    b = _lead(link_maps="https://maps.google.com/?id=ChIJ111&hl=en", nome="B", cidade="RJ")
    assert idx.add(a) is True
    # hl (tracking) removido, id igual -> dup
    assert idx.add(b) is False


def test_telefone_mesma_cidade_deduplica():
    idx = IndexadorDedup()
    a = _lead(whatsapp="21988887777", nome="A", cidade="São Paulo")
    b = _lead(whatsapp="21988887777", nome="B", cidade="São Paulo")
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_telefone_cidades_diferentes_nao_elimina_filial():
    idx = IndexadorDedup()
    a = _lead(whatsapp="21988887777", nome="A Matriz", cidade="São Paulo")
    b = _lead(whatsapp="21988887777", nome="A Filial", cidade="Rio de Janeiro")
    assert idx.add(a) is True
    assert idx.add(b) is True  # filial mantida


def test_telefone_cidade_ausente_nao_elimina():
    # cidade ausente protege (nao deduplica sozinho)
    idx = IndexadorDedup()
    a = _lead(whatsapp="21988887777", nome="A", cidade="São Paulo")
    b = _lead(whatsapp="21988887777", nome="B")  # sem cidade
    assert idx.add(a) is True
    assert idx.add(b) is True


def test_mesmo_telefone_terceira_cidade_igual_a_primeira_deduplica():
    idx = IndexadorDedup()
    a = _lead(whatsapp="21988887777", nome="A", cidade="São Paulo")
    b = _lead(whatsapp="21988887777", nome="B", cidade="Rio de Janeiro")
    c = _lead(whatsapp="21988887777", nome="C", cidade="São Paulo")
    assert idx.add(a) is True
    assert idx.add(b) is True  # filial
    assert idx.add(c) is False  # mesma cidade de A -> dup


# ── fallback nome+endereco ─────────────────────────────────────────

def test_nome_endereco_deduplica():
    idx = IndexadorDedup()
    a = _lead(nome="Tech Cel", endereco="Rua das Flores, 10", cidade="RJ")
    b = _lead(nome="Tech Cel", endereco="Rua das Flores, 10", cidade="RJ")
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_nome_endereco_diferente_nao_deduplica():
    idx = IndexadorDedup()
    a = _lead(nome="Tech Cel", endereco="Rua X", cidade="RJ")
    b = _lead(nome="Tech Cel", endereco="Rua Y", cidade="RJ")
    assert idx.add(a) is True
    assert idx.add(b) is True


# ── nome+cidade so sem fortes ───────────────────────────────────────

def test_nome_cidade_deduplica_sem_fortes():
    idx = IndexadorDedup()
    a = _lead(nome="João Silva", cidade="Niterói")  # sem forte, sem endereco
    b = _lead(nome="João Silva", cidade="Niterói")
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_nome_cidade_diferente_nao_deduplica():
    idx = IndexadorDedup()
    a = _lead(nome="João Silva", cidade="Niterói")
    b = _lead(nome="João Silva", cidade="Duque de Caxias")
    assert idx.add(a) is True
    assert idx.add(b) is True  # cidades diferentes -> mantem


def test_nomes_diferentes_mesma_cidade_nao_deduplica():
    idx = IndexadorDedup()
    a = _lead(nome="Assistência A", cidade="Niterói")
    b = _lead(nome="Assistência B", cidade="Niterói")
    assert idx.add(a) is True
    assert idx.add(b) is True  # nomes diferentes -> mantem


def test_nomes_parecidos_cidades_diferentes_nao_unifica():
    idx = IndexadorDedup()
    a = _lead(nome="João Assistência", cidade="Niterói")
    b = _lead(nome="João Assistência", cidade="Duque de Caxias")
    assert idx.add(a) is True
    assert idx.add(b) is True  # nomes parecidos/iguais, cidades diferentes -> mantem


def test_nome_cidade_nao_usado_quando_ha_forte():
    idx = IndexadorDedup()
    a = _lead(place_id="ChIJ1", nome="João", cidade="Niterói")
    b = _lead(nome="João", cidade="Niterói")  # sem forte -> recorre a nome+cidade
    assert idx.add(a) is True
    # A registrou nome_end? A tem nome mas sem endereco -> nome_end vazio.
    # A tem forte (place_id) -> NAO registra nome_cidade.
    # B: sem forte, sem nome_end -> checa nome_cidade "joao|niteroi" -> NAO registrado -> aceita
    assert idx.add(b) is True


# ── conjuntos diferentes de campos (mesma empresa) ─────────────────

def test_mesma_empresa_campos_diferentes_reconhecida_por_nome_end():
    idx = IndexadorDedup()
    # A tem place_id + nome + endereco
    a = _lead(place_id="ChIJ1", nome="Tech Cel", endereco="Rua X, 10", cidade="RJ")
    # B tem telefone (forte diferente/ausente no index) + mesmo nome+endereco
    b = _lead(whatsapp="21977776666", nome="Tech Cel", endereco="Rua X, 10", cidade="RJ")
    assert idx.add(a) is True
    # B: forte telefone nao bate (novo) -> fallback nome+endereco bate -> dup
    assert idx.add(b) is False


def test_mesma_empresa_um_com_place_id_outro_com_telefone_mesma_cidade():
    idx = IndexadorDedup()
    a = _lead(place_id="ChIJ1", nome="Loja A", endereco="Rua X", cidade="São Paulo",
              whatsapp="21977776666")
    # mesmo telefone, mesma cidade -> dup mesmo sem place_id
    b = _lead(whatsapp="21977776666", nome="Loja A", endereco="Rua X", cidade="São Paulo")
    assert idx.add(a) is True
    assert idx.add(b) is False


def test_dois_leads_sem_chaves_ambos_mantidos():
    idx = IndexadorDedup()
    a = _lead(nome="A")  # sem nada que gere chave
    b = _lead(nome="B")
    assert idx.add(a) is True
    assert idx.add(b) is True


# ── pre-carga Supabase ──────────────────────────────────────────────

def test_indexador_carrega_chaves_supabase_telefone_mesma_cidade():
    idx = IndexadorDedup()
    mesclar_chaves_existentes(idx, {
        "telefones": {"5521977776666": {"são paulo"}},
        "place_ids": {"chij999"},
        "maps_urls": set(),
    })
    # lead com telefone ja existente na mesma cidade -> dup
    novo = _lead(whatsapp="21977776666", nome="X", cidade="São Paulo")
    assert idx.add(novo) is False


def test_indexador_carrega_chaves_supabase_telefone_cidade_diferente_mantem():
    idx = IndexadorDedup()
    mesclar_chaves_existentes(idx, {
        "telefones": {"5521977776666": {"são paulo"}},
    })
    novo = _lead(whatsapp="21977776666", nome="Filial", cidade="Rio de Janeiro")
    assert idx.add(novo) is True  # filial mantida


def test_indexador_carrega_place_id_supabase():
    idx = IndexadorDedup()
    mesclar_chaves_existentes(idx, {"place_ids": {"chijabc"}})
    novo = _lead(place_id="ChIJABC", nome="X", cidade="RJ")
    assert idx.add(novo) is False


# ── funcao pura ─────────────────────────────────────────────────────

def test_deduplicar_leads_global_lista():
    leads = [
        _lead(place_id="ChIJ1", nome="A", cidade="RJ"),
        _lead(place_id="ChIJ1", nome="A", cidade="RJ"),
        _lead(nome="B", cidade="Niterói"),
        _lead(nome="B", cidade="Niterói"),
        _lead(whatsapp="21999999999", nome="C", cidade="SP"),
        _lead(whatsapp="21999999999", nome="C filial", cidade="RJ"),
    ]
    unicos = deduplicar_leads_global(leads)
    # esperado: A (1), B (1, nome+cidade dup), C (SP, 1), C filial RJ (1) = 4
    assert len(unicos) == 4


def test_dedup_global_compat_com_deduplicar_leads_mesma_cidade():
    # na mesma cidade e sem nome+cidade-only, o novo deve concordar com o antigo
    leads = [
        _lead(place_id="P1", nome="A", endereco="Rua X", cidade="RJ"),
        _lead(place_id="P1", nome="A", endereco="Rua X", cidade="RJ"),  # dup
        _lead(whatsapp="21988887777", nome="B", endereco="Rua Y", cidade="RJ"),
        _lead(whatsapp="21988887777", nome="B", endereco="Rua Y", cidade="RJ"),  # dup
        _lead(nome="C", endereco="Rua Z", cidade="RJ"),
        _lead(nome="C", endereco="Rua Z", cidade="RJ"),  # dup por nome+end
    ]
    antigo = deduplicar_leads(leads)
    novo = deduplicar_leads_global(leads)
    assert len(antigo) == len(novo) == 3


# ── runner ──────────────────────────────────────────────────────────

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