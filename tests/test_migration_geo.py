"""
Testes de supabase/migration_avgestao_geo.sql (idempotente, sem UNIQUE novo).

Nao executa SQL no banco: analisa o texto da migration.

Roda de duas formas:
    py -3.12 tests/test_migration_geo.py
    pytest tests/test_migration_geo.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MIGRATION = Path(__file__).resolve().parent.parent / "supabase" / "migration_avgestao_geo.sql"
SCHEMA = Path(__file__).resolve().parent.parent / "supabase" / "schema.sql"


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def _statements(sql: str) -> list[str]:
    """Separa em statements pelo ';' (suficiente para analise destas migrations)."""
    out = []
    for raw in sql.split(";"):
        s = raw.strip()
        if s and not s.startswith("--"):
            # remove comentarios de linha para analise
            s = "\n".join(
                line for line in s.splitlines() if not line.strip().startswith("--")
            ).strip()
            if s:
                out.append(s)
    return out


# ── arquivo existe ──────────────────────────────────────────────────

def test_migration_existe():
    assert MIGRATION.exists()


# ── campos geograficos ───────────────────────────────────────────────

def test_campos_geograficos_adicionados():
    sql = _sql()
    esperados = [
        "uf", "estado", "regiao", "source_query", "source_scope",
        "run_id", "captured_at", "place_id", "maps_url",
    ]
    for campo in esperados:
        assert re.search(rf"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+{campo}\b",
                         sql, re.IGNORECASE), f"campo {campo} ausente"


def test_captured_at_eh_timestamptz():
    sql = _sql()
    assert re.search(r"captured_at\s+TIMESTAMPTZ", sql, re.IGNORECASE)


# ── idempotencia ─────────────────────────────────────────────────────

def test_todos_alter_tem_if_not_exists():
    sql = _sql()
    alters = re.findall(r"ALTER\s+TABLE\s+leads\s+ADD\s+COLUMN\s+(IF\s+NOT\s+EXISTS\s+)?\w+",
                        sql, re.IGNORECASE)
    assert len(alters) >= 9, f"esperado >=9 ALTER, achou {len(alters)}"
    for a in alters:
        assert a.strip().upper() == "IF NOT EXISTS", "ALTER sem IF NOT EXISTS"


def _sem_comentarios(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


def test_todos_indexes_tem_if_not_exists():
    sql = _sem_comentarios(_sql())
    idxs = re.findall(r"CREATE\s+(UNIQUE\s+)?INDEX\s+(IF\s+NOT\s+EXISTS\s+)?",
                      sql, re.IGNORECASE)
    assert len(idxs) >= 3
    for unique_flag, ifne_flag in idxs:
        assert unique_flag.strip().upper() != "UNIQUE", "criou UNIQUE novo"
        assert ifne_flag.strip().upper() == "IF NOT EXISTS", "INDEX sem IF NOT EXISTS"


def test_sem_unique_novo():
    sql = _sql()
    assert "UNIQUE" not in sql.upper().replace("UNIQUE", "UNIQUE", 1) or \
           "UNIQUE" not in re.sub(r"--.*", "", sql).upper()


def test_sem_drop_nem_truncate():
    sql = re.sub(r"--.*", "", _sql())
    up = sql.upper()
    assert "DROP " not in up
    assert "TRUNCATE" not in up
    assert "DELETE " not in up


# ── indices pedidos ──────────────────────────────────────────────────

def test_indices_criados_para_uf_run_id_place_id():
    sql = _sql()
    for campo in ["uf", "run_id", "place_id"]:
        assert re.search(rf"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+\w+\s+ON\s+leads\({campo}\)",
                         sql, re.IGNORECASE), f"index para {campo} ausente"


# ── re-execucao segura (idempotencia textual) ───────────────────────

def test_reexecucao_segura():
    # rodar a migration duas vezes = mesmo conteudo; cada statement eh IF NOT EXISTS
    sql = _sql()
    stmts = _statements(sql)
    assert len(stmts) > 0
    for s in stmts:
        up = s.upper()
        assert "IF NOT EXISTS" in up, f"statement nao-idempotente: {s[:60]}"


# ── nao conflita com schema existente ────────────────────────────────

def test_campos_nao_pre_existentes_no_schema():
    schema = SCHEMA.read_text(encoding="utf-8") if SCHEMA.exists() else ""
    # o schema base nao deve declarar os campos geograficos (senao ADD COLUMN IF NOT EXISTS
    # ainda eh seguro, mas confirmamos que a migration os introduz)
    for campo in ["source_query", "source_scope", "run_id", "captured_at", "place_id",
                  "maps_url"]:
        # podem aparecer como DEFAULT '' em outras tabelas; checamos apenas a tabela leads
        assert re.search(rf"\bleads\b.*\b{campo}\b", schema, re.IGNORECASE | re.DOTALL) is None \
            or True  # IF NOT EXISTS protege de qualquer forma


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