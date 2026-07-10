"""
Testes de import_leads_to_supabase.py (campos geograficos + listar_chaves_existentes).

Mocka o client Supabase; nao acessa rede.

Roda de duas formas:
    py -3.12 tests/test_import_supabase_geo.py
    pytest tests/test_import_supabase_geo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import import_leads_to_supabase as Imp
from import_leads_to_supabase import (
    MAPEAMENTO_COLUNAS,
    CAMPOS_GEO_OPCIONAIS,
    normalizar_lead,
    _aplicar_campos_geo,
    listar_chaves_existentes,
    _e_erro_coluna,
)


# ── mocks do client supabase ─────────────────────────────────────────

class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, fake, cols):
        self.fake = fake
        self.cols = cols
        self._range = None

    def range(self, a, b):
        self._range = (a, b)
        return self

    def execute(self):
        return self.fake._execute(self.cols, self._range)


class _Table:
    def __init__(self, fake):
        self.fake = fake

    def select(self, cols):
        return _Query(self.fake, cols)


class FakeSB:
    """Mock minimo de supabase-py para select().range().execute()."""

    def __init__(self, rows, full_error=None, min_error=None):
        self.rows = rows
        self.full_error = full_error   # erro ao pedir colunas geo (place_id...)
        self.min_error = min_error     # erro no fallback minimo (real)
        self.calls = []

    def table(self, name):
        return _Table(self)

    def _execute(self, cols, rng):
        self.calls.append((cols, rng))
        # se pede colunas geo e houve erro de coluna -> lanca
        if "place_id" in cols and self.full_error is not None:
            raise self.full_error
        # fallback minimo com erro real -> lanca
        if "place_id" not in cols and "telefone_normalizado" in cols \
                and "place_id" not in cols and self.min_error is not None:
            raise self.min_error
        a, b = rng or (0, max(0, len(self.rows) - 1))
        return _Resp(self.rows[a:b + 1])


def _row(tel="", cidade="", pid="", url="", uf=""):
    return {"telefone_normalizado": tel, "cidade": cidade,
            "place_id": pid, "maps_url": url, "uf": uf}


# ── mapeamento de colunas ───────────────────────────────────────────

def test_mapeamento_colunas_geograficas():
    assert MAPEAMENTO_COLUNAS["UF"] == "uf"
    assert MAPEAMENTO_COLUNAS["Estado"] == "estado"
    assert MAPEAMENTO_COLUNAS["Região"] == "regiao"
    assert MAPEAMENTO_COLUNAS["Query de origem"] == "source_query"
    assert MAPEAMENTO_COLUNAS["Escopo de origem"] == "source_scope"
    assert MAPEAMENTO_COLUNAS["Run ID"] == "run_id"
    assert MAPEAMENTO_COLUNAS["Capturado em"] == "captured_at"
    assert MAPEAMENTO_COLUNAS["Place ID"] == "place_id"
    assert MAPEAMENTO_COLUNAS["URL Google Maps"] == "maps_url"
    # case-insensitive tambem
    assert MAPEAMENTO_COLUNAS["uf"] == "uf"
    assert MAPEAMENTO_COLUNAS["place_id"] == "place_id"


# ── normalizar_lead ─────────────────────────────────────────────────

def test_normalizar_lead_campos_geograficos():
    lead = normalizar_lead({
        "nome": "Eletronica Sul",
        "telefone": "21999999999",
        "uf": "RJ",
        "estado": "Rio de Janeiro",
        "regiao": "sudeste",
        "source_query": "assistencia tecnica de celular em Duque de Caxias, RJ",
        "source_scope": "uf",
        "run_id": "run_20260628_120000_abc123",
        "captured_at": "2026-06-28T12:00:00",
        "place_id": "ChIJabc",
        "maps_url": "https://maps.google.com/?id=1",
    })
    assert lead["uf"] == "RJ"
    assert lead["estado"] == "Rio de Janeiro"
    assert lead["regiao"] == "sudeste"
    assert lead["place_id"] == "ChIJabc"
    assert lead["maps_url"].endswith("id=1")
    assert lead["source_scope"] == "uf"
    assert lead["run_id"].startswith("run_")


def test_normalizar_lead_geo_ausente_vira_vazio():
    lead = normalizar_lead({"nome": "X", "telefone": "21999999999"})
    for campo in CAMPOS_GEO_OPCIONAIS:
        assert lead[campo] == ""


# ── _aplicar_campos_geo ──────────────────────────────────────────────

def test_aplicar_campos_geo_preenche_payload():
    payload = {"nome": "X"}
    _aplicar_campos_geo(payload, {"uf": "RJ", "place_id": "ChIJ1", "captured_at": ""})
    assert payload["uf"] == "RJ"
    assert payload["place_id"] == "ChIJ1"
    # captured_at vazio NAO entra (TIMESTAMPTZ nao aceita "")
    assert "captured_at" not in payload


def test_aplicar_campos_geo_captured_at_com_valor():
    payload = {}
    _aplicar_campos_geo(payload, {"captured_at": "2026-06-28T12:00:00"})
    assert payload["captured_at"] == "2026-06-28T12:00:00"


# ── listar_chaves_existentes: caso completo (migration aplicada) ─────

def test_listar_chaves_completas():
    rows = [
        _row(tel="5521999999001", cidade="Duque de Caxias", pid="ChIJ1", url="u1"),
        _row(tel="5521999999002", cidade="Nova Iguaçu", pid="ChIJ2", url="u2"),
        _row(tel="5521999999001", cidade="Rio de Janeiro", pid="ChIJ1", url="u1"),
    ]
    sb = FakeSB(rows)
    chaves = listar_chaves_existentes(sb, batch_size=100)
    assert chaves["place_ids"] == {"ChIJ1", "ChIJ2"}
    assert chaves["maps_urls"] == {"u1", "u2"}
    # telefone consciente de cidade: mesma tel em 2 cidades
    assert chaves["telefones"]["5521999999001"] == {"Duque de Caxias", "Rio de Janeiro"}
    assert chaves["telefones"]["5521999999002"] == {"Nova Iguaçu"}


# ── fallback quando migration nao aplicada ──────────────────────────

def test_listar_chaves_fallback_sem_migration():
    rows = [
        _row(tel="5521A", cidade="C1"),
        _row(tel="5521B", cidade="C2"),
    ]
    # full select lanca erro de coluna ausente
    sb = FakeSB(rows, full_error=Exception('column "place_id" does not exist'))
    chaves = listar_chaves_existentes(sb, batch_size=100)
    # fallback: sem place_ids/maps_urls
    assert chaves["place_ids"] == set()
    assert chaves["maps_urls"] == set()
    # telefones ainda presentes
    assert set(chaves["telefones"]) == {"5521A", "5521B"}
    # chamou full (place_id) e depois min (sem place_id)
    cols_chamados = [c for c, _ in sb.calls]
    assert any("place_id" in c for c in cols_chamados)
    assert any("place_id" not in c and "telefone_normalizado" in c for c in cols_chamados)


def test_e_erro_coluna_detecta_marcadores():
    assert _e_erro_coluna(Exception('column "uf" does not exist'))
    assert _e_erro_coluna(Exception("Could not find the column place_id"))
    assert _e_erro_coluna(Exception("PGRST205"))


# ── erro real de conexao/auth NAO vira fallback ──────────────────────

def test_listar_chaves_erro_conexao_propaga():
    rows = []
    # erro sem marcador de coluna (conexao/auth)
    sb = FakeSB(rows, full_error=Exception("Connection refused: max retries"))
    try:
        listar_chaves_existentes(sb, batch_size=100)
        assert False, "devia propagar erro de conexao"
    except Exception as exc:
        assert "Connection refused" in str(exc)


def test_listar_chaves_erro_auth_propaga():
    sb = FakeSB([], full_error=Exception("401 Unauthorized: invalid API key"))
    try:
        listar_chaves_existentes(sb, batch_size=100)
        assert False, "devia propagar erro de auth"
    except Exception as exc:
        assert "401" in str(exc)


def test_fallback_min_com_erro_real_propaga():
    rows = []
    # full falha por coluna ausente (fallback entra), mas min falha com erro real
    sb = FakeSB(rows,
                full_error=Exception('column "place_id" does not exist'),
                min_error=Exception("Connection refused"))
    try:
        listar_chaves_existentes(sb, batch_size=100)
        assert False, "erro real no fallback min deve propagar"
    except Exception as exc:
        assert "Connection refused" in str(exc)


# ── paginacao ────────────────────────────────────────────────────────

def test_listar_chaves_paginacao():
    rows = [_row(tel=f"tel{i}", cidade=f"C{i}", pid=f"p{i}") for i in range(2500)]
    sb = FakeSB(rows)
    chaves = listar_chaves_existentes(sb, batch_size=1000)
    # 2500 linhas / batch 1000 -> 3 chamadas (1000 + 1000 + 500)
    assert len(sb.calls) == 3
    assert len(chaves["telefones"]) == 2500
    assert len(chaves["place_ids"]) == 2500
    # ranges corretos
    ranges = [r for _, r in sb.calls]
    assert ranges[0] == (0, 999)
    assert ranges[1] == (1000, 1999)
    assert ranges[2] == (2000, 2999)


def test_paginacao_para_na_ultima_parcial():
    rows = [_row(tel=f"t{i}") for i in range(1500)]
    sb = FakeSB(rows, batch_size=1000) if False else FakeSB(rows)
    listar_chaves_existentes(sb, batch_size=1000)
    # 1000 + 500 -> 2 chamadas
    assert len(sb.calls) == 2


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
            print(f"  ERROR  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n  {passou} passaram, {falhou} falharam de {len(fns)}")
    return 0 if falhou == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())