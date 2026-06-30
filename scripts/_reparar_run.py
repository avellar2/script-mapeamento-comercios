"""
Script de reparo do run canônico.
Reconcilia fila, checkpoint e resumo sem recomeçar.
"""
import json
import csv
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

RUN_ID = "run_20260629_014644_583c55"
RUN_DIR = Path("output/avgestao/runs") / RUN_ID


def reparar():
    # Load fila
    fila_path = RUN_DIR / "fila.json"
    fila = json.loads(fila_path.read_text(encoding="utf-8"))

    # Load checkpoint
    cp_path = RUN_DIR / "checkpoint.json"
    cp = json.loads(cp_path.read_text(encoding="utf-8"))

    # Load resumo
    resumo_path = RUN_DIR / "resumo.json"
    resumo = json.loads(resumo_path.read_text(encoding="utf-8"))

    print("=== ESTADO ANTES DO REPARO ===")
    print(f"Total tarefas: {len(fila)}")
    print(f"Checkpoint: concl={cp['concluidas']} pend={cp['pendentes']} "
          f"andamento={cp['em_andamento']} erro={cp['erro']} interr={cp['interrompidas']}")
    print(f"Resumo: captados={resumo.get('captados_total', 0)}")

    status_count = Counter(it["status"] for it in fila)
    print(f"Fila status: {dict(status_count)}")

    # Find em_andamento tasks
    em_andamento = [it for it in fila if it["status"] == "em_andamento"]
    print(f"\nTarefas em_andamento: {len(em_andamento)}")
    for t in em_andamento:
        print(f"  {t['id_tarefa']} - {t['cidade']} - {t['subnicho_label']}")

    # Change em_andamento to interrompida
    changes = []
    for it in fila:
        if it["status"] == "em_andamento":
            it["status"] = "interrompida"
            it["erro"] = "interrompida: processo encerrado durante recuperacao"
            changes.append(
                f"{it['id_tarefa']}: em_andamento -> interrompida "
                f"({it['cidade']} - {it['subnicho_label']})"
            )

    # Recalculate checkpoint
    status_count = Counter(it["status"] for it in fila)
    cp["concluidas"] = status_count.get("concluida", 0)
    cp["pendentes"] = status_count.get("pendente", 0)
    cp["em_andamento"] = status_count.get("em_andamento", 0)
    cp["erro"] = status_count.get("erro", 0)
    cp["interrompidas"] = status_count.get("interrompida", 0)
    cp["ignoradas_limite"] = status_count.get("ignorada_limite", 0)
    cp["atualizado_em"] = datetime.now(timezone.utc).isoformat()
    cp["status_run"] = "interrompido"
    cp["motivo_interrupcao"] = "reparo apos execucao concorrente"

    # Save fila
    fila_path.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFila salva: {fila_path}")

    # Save checkpoint
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Checkpoint salvo: {cp_path}")

    # Update resumo
    resumo["status_run"] = "interrompido"
    resumo_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumo salvo: {resumo_path}")

    # Validate leads_parciais.csv
    leads_path = RUN_DIR / "leads_parciais.csv"
    if leads_path.exists():
        with leads_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            leads = list(reader)
        print(f"\nLeads parciais: {len(leads)} registros")
        place_ids = [l.get("place_id", "") for l in leads if l.get("place_id", "")]
        unique_place_ids = set(place_ids)
        if len(place_ids) != len(unique_place_ids):
            print(f"  WARNING: {len(place_ids) - len(unique_place_ids)} place_ids duplicados")
        else:
            print(f"  OK: place_ids unicos")
    else:
        print("\nWARNING: leads_parciais.csv nao encontrado")
        leads = []

    print("\n=== ALTERACOES REALIZADAS ===")
    for c in changes:
        print(f"  {c}")

    print(f"\n=== ESTADO APOS REPARO ===")
    print(f"Checkpoint: concl={cp['concluidas']} pend={cp['pendentes']} "
          f"andamento={cp['em_andamento']} erro={cp['erro']} interr={cp['interrompidas']}")
    print(f"Leads preservados: {len(leads)}")

    # Find first pending task
    pendentes = [it for it in fila if it["status"] == "pendente"]
    if pendentes:
        first = pendentes[0]
        print(f"\nPrimeira tarefa pendente: {first['cidade']} - {first['subnicho_label']} "
              f"(id: {first['id_tarefa']})")

    # Save repair report
    report = {
        "run_id": RUN_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "estado_antes": {
            "concluidas": status_count.get("concluida", 0) - (1 if changes else 0),
            "em_andamento": 1,
            "interrompidas": status_count.get("interrompida", 0) - (1 if changes else 0),
            "pendentes": status_count.get("pendente", 0),
        },
        "alteracoes": changes,
        "total_preservado": len(leads),
        "total_reparado": len(changes),
        "leads_preservados": len(leads),
        "primeira_tarefa_retomada": pendentes[0]["id_tarefa"] if pendentes else None,
        "cidade_retomada": pendentes[0]["cidade"] if pendentes else None,
    }
    report_path = RUN_DIR / f"reparo_{RUN_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatorio de reparo salvo: {report_path}")


if __name__ == "__main__":
    reparar()
