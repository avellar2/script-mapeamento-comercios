"""
Testes de config/fila.py.

Roda de duas formas:
    py -3.12 tests/test_fila.py
    pytest tests/test_fila.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.avgestao import GRUPOS, get_grupo
from config.territorios import Municipio, normalizar_nome_cidade
from config.fila import (
    ItemFila,
    gerar_fila,
    distribuicao_estimada,
    salvar_fila,
    carregar_fila,
    atualizar_status_item,
    buscar_item,
    filtrar_por_status,
    contagem_por_status,
    STATUS_PENDENTE,
    STATUS_IGNORADA_LIMITE,
    STATUS_CONCLUIDA,
    STATUS_EXECUTAVEIS,
)


def _mun(nome, uf, regiao="sudeste"):
    return Municipio(
        nome=nome,
        nome_normalizado=normalizar_nome_cidade(nome),
        uf=uf,
        uf_nome=uf,
        regiao=regiao,
        capital=False,
        populacao=0,
        codigo_ibge="0000000",
    )


CIDADES = [
    _mun("Duque de Caxias", "RJ"),
    _mun("Nova Iguaçu", "RJ"),
    _mun("São Paulo", "SP"),
]

GRUPO_ASSIS = [get_grupo("assistencias")]  # 6 subnichos


# ── geracao ─────────────────────────────────────────────────────────

def test_gerar_fila_cartesiano():
    # 1 grupo (6 subnichos) x 3 cidades = 18 itens
    fila = gerar_fila(GRUPO_ASSIS, CIDADES, max_por_consulta=20)
    assert len(fila) == 18
    assert all(isinstance(i, ItemFila) for i in fila)
    assert all(i.status == STATUS_PENDENTE for i in fila)
    assert all(i.tentativas == 0 for i in fila)
    assert all(i.captados == 0 for i in fila)


def test_gerar_fila_dois_grupos():
    grupos = [get_grupo("assistencias"), get_grupo("refrigeracao")]
    fila = gerar_fila(grupos, CIDADES, max_por_consulta=10)
    # 6 + N(refrigeracao) subnichos x 3 cidades
    esperado = (len(grupos[0].subnichos) + len(grupos[1].subnichos)) * 3
    assert len(fila) == esperado


def test_query_formato():
    fila = gerar_fila(GRUPO_ASSIS, [_mun("Duque de Caxias", "RJ")])
    item = fila[0]
    assert "em Duque de Caxias, RJ" in item.query
    # subnicho de celular: query começa com o termo do subnicho
    assert item.query.startswith("assistencia tecnica de celular em ")


def test_campos_geograficos_preenchidos():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    for item in fila:
        assert item.cidade
        assert item.uf
        assert item.regiao
        assert item.grupo
        assert item.subnicho
        assert item.subnicho_label
        assert item.msg_cat


def test_id_tarefa_deterministico():
    f1 = gerar_fila(GRUPO_ASSIS, CIDADES)
    f2 = gerar_fila(GRUPO_ASSIS, CIDADES)
    ids1 = [i.id_tarefa for i in f1]
    ids2 = [i.id_tarefa for i in f2]
    assert ids1 == ids2
    # ids unicos dentro da fila
    assert len(set(ids1)) == len(ids1)


def test_fila_nao_truncada_por_max_total():
    # a fila representa todas as consultas planejadas; max_total nao corta
    fila = gerar_fila(GRUPO_ASSIS, CIDADES, max_por_consulta=20)
    # mesmo que conceitualmente max_total=5, a geracao nao trunca
    assert len(fila) == 18


def test_ordem_cidades_respeitada():
    # a ordem dos municipios recebidos eh preservada (cidade-outer)
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    cidades_na_ordem = []
    seen = set()
    for item in fila:
        chave = (item.cidade, item.uf)
        if chave not in seen:
            seen.add(chave)
            cidades_na_ordem.append(item.cidade)
    assert cidades_na_ordem == ["Duque de Caxias", "Nova Iguaçu", "São Paulo"]


# ── distribuicao estimada ───────────────────────────────────────────

def test_distribuicao_estimada():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES, max_por_consulta=20)
    d = distribuicao_estimada(fila, max_por_consulta=20)
    assert d["total_tarefas"] == 18
    assert d["estimativa_maxima_leads"] == 18 * 20
    assert d["por_uf"]["RJ"] == 12  # 6 subnichos x 2 cidades RJ
    assert d["por_uf"]["SP"] == 6
    assert d["cidades"] == 3
    assert d["ufs"] == 2
    # soma por uf == total
    assert sum(d["por_uf"].values()) == 18


# ── persistencia ───────────────────────────────────────────────────

def test_salvar_carregar_fila_roundtrip():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "fila.json"
        salvar_fila(fila, caminho)
        assert caminho.exists()
        # conteudo eh JSON valido e UTF-8 (acentos preservados)
        texto = caminho.read_text(encoding="utf-8")
        assert "Iguaçu" in texto
        carregada = carregar_fila(caminho)
    assert len(carregada) == len(fila)
    assert [i.id_tarefa for i in carregada] == [i.id_tarefa for i in fila]
    assert carregada[0].query == fila[0].query
    assert carregada[0].cidade == "Duque de Caxias"


def test_salvar_fila_cria_diretorio_pai():
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "runs" / "run1" / "fila.json"
        fila = gerar_fila(GRUPO_ASSIS, [_mun("Niterói", "RJ")])
        salvar_fila(fila, caminho)
        assert caminho.exists()


# ── atualizacao de status ──────────────────────────────────────────

def test_atualizar_status_item():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    alvo = fila[0].id_tarefa
    item = atualizar_status_item(fila, alvo, status=STATUS_IGNORADA_LIMITE,
                                 captados=0, erro="limite")
    assert item is not None
    assert item.status == STATUS_IGNORADA_LIMITE
    # persiste no objeto da fila
    assert buscar_item(fila, alvo).status == STATUS_IGNORADA_LIMITE


def test_atualizar_status_item_inexistente():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    assert atualizar_status_item(fila, "inexistente", status="x") is None


def test_filtrar_e_contar_status():
    fila = gerar_fila(GRUPO_ASSIS, CIDADES)
    atualizar_status_item(fila, fila[0].id_tarefa, status=STATUS_CONCLUIDA)
    atualizar_status_item(fila, fila[1].id_tarefa, status=STATUS_IGNORADA_LIMITE)
    cont = contagem_por_status(fila)
    assert cont[STATUS_PENDENTE] == 16
    assert cont[STATUS_CONCLUIDA] == 1
    assert cont[STATUS_IGNORADA_LIMITE] == 1
    executaveis = filtrar_por_status(fila, STATUS_EXECUTAVEIS)
    assert len(executaveis) == 16


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