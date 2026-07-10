"""
Testes de config/territorios.py.

Roda de duas formas:
    py -3.12 tests/test_territorios.py
    pytest tests/test_territorios.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config.territorios as T
from config.territorios import (
    Municipio,
    normalizar_nome_cidade,
    normalizar_uf,
    nome_exibicao,
    buscar_municipio,
    resolver_cidades,
    ordenar,
    base_completa,
    status_base,
    BaseIncompletaError,
)


FIXTURE_CIDADES = Path(__file__).resolve().parent / "fixtures" / "cidades.txt"


# ── helpers ─────────────────────────────────────────────────────────

def _m(nome, uf, pop=0, capital=False, codigo="0000000"):
    return Municipio(
        nome=nome,
        nome_normalizado=normalizar_nome_cidade(nome),
        uf=uf,
        uf_nome=uf,
        regiao="sudeste",
        capital=capital,
        populacao=pop,
        codigo_ibge=codigo,
    )


class _SemBase:
    """Contexto que simula base completa ausente (CSV/meta inexistentes)."""

    def __enter__(self):
        self._csv = T.CSV_PATH
        self._meta = T.META_PATH
        T.CSV_PATH = Path("__inexistente__municipios.csv")
        T.META_PATH = Path("__inexistente__municipios.meta.json")
        T._reset_status_cache()
        return self

    def __exit__(self, *exc):
        T.CSV_PATH = self._csv
        T.META_PATH = self._meta
        T._reset_status_cache()
        return False


# ── normalizacao ───────────────────────────────────────────────────

def test_normalizar_nome_cidade():
    assert normalizar_nome_cidade("São João de Meriti") == "sao joao de meriti"
    assert normalizar_nome_cidade("SÃO JOÃO DE MERITI") == "sao joao de meriti"
    assert normalizar_nome_cidade("Nova Iguaçu") == "nova iguacu"
    assert normalizar_nome_cidade(None) == ""
    assert normalizar_nome_cidade("  Belford  Roxo  ") == "belford roxo"


def test_normalizar_uf():
    assert normalizar_uf("rj") == "RJ"
    assert normalizar_uf("RJ") == "RJ"
    assert normalizar_uf("sp") == "SP"
    assert normalizar_uf("Rio de Janeiro") == "RJ"
    assert normalizar_uf("são paulo") == "SP"
    assert normalizar_uf("") == ""
    assert normalizar_uf(None) == ""


def test_parse_cidade_uf_com_virgula():
    # buscar_municipio usa _parse_cidade_uf internamente
    m = buscar_municipio("Nova Iguacu, RJ")
    assert m is not None
    assert m.uf == "RJ"
    assert m.nome == "Nova Iguaçu"


def test_nome_exibicao_preserva_acentos():
    # pela base completa
    assert nome_exibicao("nova iguacu") == "Nova Iguaçu"
    assert nome_exibicao("SAO JOAO DE MERITI") == "São João de Meriti"
    # com UF explicita
    assert nome_exibicao("duque de caxias", "rj") == "Duque de Caxias"


# ── codigo ibge ─────────────────────────────────────────────────────

def test_municipio_tem_codigo_ibge():
    m = buscar_municipio("Nova Iguaçu, RJ")
    assert m is not None
    assert m.codigo_ibge
    assert len(m.codigo_ibge) == 7
    assert m.codigo_ibge.isdigit()


def test_capital_uf_retorna_capital_com_codigo():
    m = T.capital_uf("RJ")
    assert m.nome == "Rio de Janeiro"
    assert m.uf == "RJ"
    assert m.capital is True
    assert m.codigo_ibge.isdigit()


# ── resolucao por escopo (base completa) ────────────────────────────

def test_status_base_completa_apos_geracao():
    st = status_base()
    assert st["completa"] is True, st
    assert st["quantidade"] == 5571, st
    assert st["checksum_ok"] is True
    assert st["checksum_esperado"] == st["checksum_encontrado"]
    assert st["checksum_esperado"]  # SHA-256 obrigatorio e presente


def test_resolver_cidades_uf_rj():
    municipios = resolver_cidades(escopo="uf", uf=["RJ"])
    assert len(municipios) == 92
    nomes = {m.nome for m in municipios}
    assert "Nova Iguaçu" in nomes
    assert "Duque de Caxias" in nomes
    assert all(m.uf == "RJ" for m in municipios)


def test_resolver_cidades_ufs_multiplos():
    municipios = resolver_cidades(escopo="ufs", ufs=["RJ", "ES"])
    ufs = {m.uf for m in municipios}
    assert ufs == {"RJ", "ES"}


def test_resolver_cidades_regiao_sudeste():
    municipios = resolver_cidades(escopo="regiao", regiao="sudeste")
    ufs = {m.uf for m in municipios}
    assert ufs == {"RJ", "SP", "MG", "ES"}


def test_resolver_cidades_brasil():
    municipios = resolver_cidades(escopo="brasil")
    assert len(municipios) == 5571
    # nao duplica
    chaves = {m.chave() for m in municipios}
    assert len(chaves) == 5571


def test_resolver_cidades_cidade_unica():
    municipios = resolver_cidades(escopo="cidade", cidade="Nova Iguaçu, RJ")
    assert len(municipios) == 1
    assert municipios[0].nome == "Nova Iguaçu"
    assert municipios[0].uf == "RJ"


def test_resolver_cidades_cidades_lista():
    municipios = resolver_cidades(
        escopo="cidades", cidades=["Nova Iguaçu, RJ", "São Paulo, SP"]
    )
    assert len(municipios) == 2
    nomes = {m.nome for m in municipios}
    assert nomes == {"Nova Iguaçu", "São Paulo"}


def test_resolver_cidades_arquivo():
    municipios = resolver_cidades(escopo="arquivo", cidades_arquivo=str(FIXTURE_CIDADES))
    assert len(municipios) == 3
    nomes = sorted(m.nome for m in municipios)
    assert nomes == ["Duque de Caxias", "Nova Iguaçu", "São Paulo"]


def test_resolver_cidades_dedup():
    # mesmas cidades repetidas nao duplicam
    municipios = resolver_cidades(
        escopo="cidades", cidades=["Nova Iguaçu, RJ", "Nova Iguaçu, RJ"]
    )
    assert len(municipios) == 1


def test_resolver_cidade_inexistente_aborta():
    try:
        resolver_cidades(escopo="cidade", cidade="Cidade Que Nao Existe, RJ")
        assert False, "esperava BaseIncompletaError"
    except BaseIncompletaError:
        pass


# ── limites ────────────────────────────────────────────────────────

def test_limite_cidades_corta():
    municipios = resolver_cidades(escopo="uf", uf=["RJ"], limite_cidades=5)
    assert len(municipios) == 5


# ── ordenacao ──────────────────────────────────────────────────────

def test_ordem_alfabetica():
    base = [_m("Zebra", "RJ"), _m("Abelha", "SP"), _m("Macaco", "RJ")]
    ord = ordenar(base, "alfabetica")
    assert [m.nome for m in ord] == ["Abelha", "Macaco", "Zebra"]


def test_ordem_capitais_primeiro():
    base = [_m("Campinas", "SP", capital=False), _m("São Paulo", "SP", capital=True),
            _m("Ribeirão Preto", "SP", capital=False)]
    ord = ordenar(base, "capitais")
    assert ord[0].nome == "São Paulo"
    assert {m.nome for m in ord[1:]} == {"Campinas", "Ribeirão Preto"}


def test_ordem_maiores_por_populacao():
    base = [
        _m("Pequena", "RJ", pop=1000),
        _m("Grande", "SP", pop=500000),
        _m("Media", "MG", pop=50000),
    ]
    ord = ordenar(base, "maiores")
    assert [m.nome for m in ord] == ["Grande", "Media", "Pequena"]


def test_ordem_maiores_sem_populacao_cai_alfabetica():
    # todas populacao 0 -> ordem alfabetica por uf+nome
    base = [_m("Zebra", "RJ", pop=0), _m("Abelha", "SP", pop=0)]
    ord = ordenar(base, "maiores")
    assert [m.nome for m in ord] == ["Abelha", "Zebra"]


def test_ordem_aleatoria_reprodutivel():
    base = [_m(f"Cidade{i}", "RJ") for i in range(10)]
    a = ordenar(base, "aleatoria", seed="run123")
    b = ordenar(base, "aleatoria", seed="run123")
    assert [m.nome for m in a] == [m.nome for m in b]
    # seed diferente provavelmente muda (nao deterministico, mas aqui 10 elems)
    c = ordenar(base, "aleatoria", seed="run999")
    assert [m.nome for m in a] != [m.nome for m in c]


def test_ordem_fornecida_preserva():
    base = [_m("Zebra", "RJ"), _m("Abelha", "SP")]
    ord = ordenar(base, "fornecida")
    assert [m.nome for m in ord] == ["Zebra", "Abelha"]


def test_ordem_invalida_erro():
    try:
        ordenar([_m("A", "RJ")], "inesistente")
        assert False
    except ValueError:
        pass


# ── fallback offline ───────────────────────────────────────────────

def test_fallback_sem_csv_tem_27_capitais():
    with _SemBase():
        assert base_completa() is False
        bundled = T._bundled_minimo()
        capitais = [m for m in bundled if m.capital]
        assert len(capitais) == 27


def test_csv_ausente_escopo_brasil_aborta():
    with _SemBase():
        try:
            resolver_cidades(escopo="brasil")
            assert False, "esperava BaseIncompletaError"
        except BaseIncompletaError as e:
            assert "brasil" in str(e).lower() or "incompleta" in str(e).lower()


def test_csv_ausente_escopo_uf_aborta_sem_flag():
    with _SemBase():
        try:
            resolver_cidades(escopo="uf", uf=["RJ"])
            assert False, "esperava BaseIncompletaError"
        except BaseIncompletaError:
            pass


def test_csv_ausente_escopo_uf_permitido_com_flag():
    with _SemBase():
        municipios = resolver_cidades(
            escopo="uf", uf=["RJ"], permitir_base_incompleta=True
        )
        # bundled inclui capital (Rio de Janeiro) + cidades da Baixada (RJ)
        nomes = {m.nome for m in municipios}
        assert "Rio de Janeiro" in nomes
        assert all(m.uf == "RJ" for m in municipios)


def test_fallback_permitido_em_cidade():
    with _SemBase():
        # Rio de Janeiro e capital -> esta no bundled
        municipios = resolver_cidades(escopo="cidade", cidade="Rio de Janeiro, RJ")
        assert len(municipios) == 1
        assert municipios[0].nome == "Rio de Janeiro"
        assert municipios[0].uf == "RJ"


def test_fallback_negado_em_cidade_inexistente():
    with _SemBase():
        # cidade que nao esta no bundled -> aborta
        try:
            resolver_cidades(escopo="cidade", cidade="Cidade Remota Inexistente, AC")
            assert False, "esperava BaseIncompletaError"
        except BaseIncompletaError:
            pass


def test_escopo_invalido_erro():
    try:
        resolver_cidades(escopo="mundo")
        assert False
    except ValueError:
        pass


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