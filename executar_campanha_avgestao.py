#!/usr/bin/env python3
"""
Orquestrador AVGESTAO
=====================
Executa o fluxo completo de campanha AVGESTAO em um unico comando,
reutilizando o mesmo run_id em todas as etapas:

  1. mapear   (captura leads no Google Maps)
  2. prospectar (qualifica, calcula score, gera mensagens)
  3. campanha (gera planilha de abordagem com links wa.me)

NUNCA envia mensagens automaticamente. NUNCA usa shell=True.

Uso:
  python executar_campanha_avgestao.py --grupo assistencias --escopo uf --uf RJ --max-total 300 --top 20
  python executar_campanha_avgestao.py --grupo assistencias --escopo uf --uf RJ --max-total 300 --dry-run
  python executar_campanha_avgestao.py --resume --run-id <RUN_ID>
  python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-por-consulta 5
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
PYTHON = sys.executable
MAPEADOR = str(BASE_DIR / "mapear_comercios.py")
PROSPECTAR = str(BASE_DIR / "prospectar_leads.py")
CAMPANHA = str(BASE_DIR / "campanha_diaria.py")
RUNS_DIR = BASE_DIR / "output" / "avgestao" / "runs"

ARG_GEOGRAFICOS = [
    "grupo", "escopo", "cidade", "cidades", "uf", "ufs", "regiao",
    "cidades_arquivo", "limite_cidades", "max_por_cidade",
    "max_por_subnicho", "max_total", "max_por_consulta",
    "ordem_cidades", "delay_min", "delay_max", "max_tentativas",
    "headless",
]

ARG_RESUME = ["resume", "run_id", "permitir_base_incompleta", "confirmar_grande_execucao"]


def _gerar_run_id() -> str:
    import hashlib
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    sufixo = hashlib.sha1(os.urandom(16)).hexdigest()[:6]
    return f"run_{agora}_{sufixo}"


def _flags_mapear(args, run_id):
    cmd = [PYTHON, MAPEADOR, "--produto", "avgestao"]
    for flag in ARG_GEOGRAFICOS:
        val = getattr(args, flag, None)
        if val is not None and val is not False:
            arg_name = f"--{flag.replace('_', '-')}"
            if isinstance(val, list):
                for v in val:
                    cmd.extend([arg_name, str(v)])
            elif val is True:
                cmd.append(arg_name)
            else:
                cmd.extend([arg_name, str(val)])
    for flag in ARG_RESUME:
        val = getattr(args, flag, None)
        if val is not None and val is not False:
            arg_name = f"--{flag.replace('_', '-')}"
            if isinstance(val, list):
                for v in val:
                    cmd.extend([arg_name, str(v)])
            elif val is True:
                cmd.append(arg_name)
            else:
                cmd.extend([arg_name, str(val)])
    if not args.resume and not args.run_id:
        cmd.extend(["--run-id", run_id])
    if args.dry_run:
        cmd.append("--dry-run")
    if args.somente_gerar_fila:
        cmd.append("--somente-gerar-fila")
    return cmd


def _flags_prospectar(args, arquivo):
    cmd = [PYTHON, PROSPECTAR, "--produto", "avgestao"]
    if args.grupo:
        cmd.extend(["--grupo", args.grupo])
    if args.cidade:
        cmd.extend(["--cidade", args.cidade])
    cmd.extend(["--arquivo", str(arquivo)])
    return cmd


def _flags_campanha(args, arquivo):
    cmd = [PYTHON, CAMPANHA, "--produto", "avgestao"]
    if args.grupo:
        cmd.extend(["--grupo", args.grupo])
    if args.top:
        cmd.extend(["--top", str(args.top)])
    if args.somente_confirmados:
        cmd.append("--somente-confirmados")
    if args.score_minimo is not None:
        cmd.extend(["--score-minimo", str(args.score_minimo)])
    cmd.extend(["--arquivo", str(arquivo)])
    return cmd


def _encontrar_xlsx_geo(run_dir):
    geo = sorted(run_dir.glob("leads_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return geo[0] if geo else None


def _mostrar_comando(etapa, cmd, run_id, run_dir):
    print()
    print("=" * 70)
    print(f"  ETAPA: {etapa}")
    print(f"  Run ID: {run_id}")
    print(f"  Pasta:  {run_dir}")
    print(f"  Comando: {' '.join(cmd)}")
    print("=" * 70)
    print()


def _executar(etapa, cmd, run_id, run_dir):
    _mostrar_comando(etapa, cmd, run_id, run_dir)
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print()
        print(f"❌ ETAPA '{etapa}' FALHOU (codigo {result.returncode})")
        checkpoint = run_dir / "checkpoint.json"
        if checkpoint.exists():
            print(f"   Checkpoint: {checkpoint}")
        print(f"   Para retomar: python executar_campanha_avgestao.py --resume --run-id {run_id}")
        return False
    print(f"   ✅ {etapa} concluida")
    return True


def _listar_arquivos(run_dir):
    print()
    print("-" * 70)
    print(f"  ARQUIVOS GERADOS — {run_dir}")
    print("-" * 70)
    encontrados = False
    nomes = [
        "config.json", "fila.json", "checkpoint.json",
        "leads_parciais.csv", "leads_parciais.xlsx", "resumo.json",
    ]
    for nome in nomes:
        p = run_dir / nome
        if p.exists():
            print(f"  ✓ {nome}")
            encontrados = True
    geos = sorted(run_dir.glob("leads_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    for g in geos:
        print(f"  ✓ {g.name} (XLSX geografico final)")
        encontrados = True
    prospect = BASE_DIR / "output" / "avgestao"
    prosps = sorted(prospect.glob("prospeccao_avgestao_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in prosps[:1]:
        if p.exists():
            print(f"  ✓ {p.relative_to(BASE_DIR)} (prospeccao)")
            encontrados = True
    camps = sorted(prospect.glob("leads_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in camps[:1]:
        if c.exists():
            print(f"  ✓ {c.relative_to(BASE_DIR)} (campanha)")
            encontrados = True
    if not encontrados:
        print("  (nenhum arquivo encontrado)")
    print("-" * 70)
    print()


def _modo_status(args):
    """Modo status: consulta estado do run sem abrir navegador nem alterar arquivos."""
    from config.lock import verificar_lock_global

    if args.run_id:
        run_dir = RUNS_DIR / args.run_id
        if not run_dir.exists() or not (run_dir / "config.json").exists():
            print(f"❌ Run inexistente: {args.run_id}")
            sys.exit(1)

        # Le arquivos (somente leitura)
        import json
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        cp = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
        resumo = json.loads((run_dir / "resumo.json").read_text(encoding="utf-8")) \
            if (run_dir / "resumo.json").exists() else {}
        fila = json.loads((run_dir / "fila.json").read_text(encoding="utf-8"))
        leads_csv = run_dir / "leads_parciais.csv"
        n_leads = len(leads_csv.read_text(encoding="utf-8-sig").strip().splitlines()) - 1 \
            if leads_csv.exists() and leads_csv.stat().st_size > 0 else 0

        # Verifica se ha processo ativo
        lock_info = verificar_lock_global()
        ativo = lock_info and lock_info.get("run_id") == args.run_id

        # Encontra cidade atual
        cidade_atual = ""
        for it in fila:
            if it.get("status") in ("em_andamento",):
                cidade_atual = f"{it['cidade']} - {it['subnicho_label']}"
                break
        if not cidade_atual:
            for it in fila:
                if it.get("status") == "pendente":
                    cidade_atual = f"{it['cidade']} - {it['subnicho_label']}"
                    break

        print()
        print("=" * 60)
        print(f"  STATUS DO RUN: {args.run_id}")
        print("=" * 60)
        print(f"  Run ID:        {args.run_id}")
        print(f"  Status:        {cp.get('status_run', 'desconhecido')}")
        print(f"  Escopo:        {config.get('escopo', '?')} - {config.get('escopo_descritor', '?')}")
        print(f"  Grupo:         {', '.join(config.get('grupos', []))}")
        print(f"  Cidade atual:  {cidade_atual or 'N/A'}")
        print(f"  Captador ativo: {'SIM' if ativo else 'NÃO'}")
        if ativo and lock_info:
            print(f"    PID: {lock_info.get('pid')}")
            print(f"    Início: {lock_info.get('inicio')}")
        print()
        print(f"  Tarefas:")
        print(f"    Total:       {cp.get('total_tarefas', len(fila))}")
        print(f"    Concluídas:  {cp.get('concluidas', 0)}")
        print(f"    Pendentes:   {cp.get('pendentes', 0)}")
        print(f"    Em andamento: {cp.get('em_andamento', 0)}")
        print(f"    Erro:        {cp.get('erro', 0)}")
        print(f"    Interrompidas: {cp.get('interrompidas', 0)}")
        print(f"    Ignoradas:   {cp.get('ignoradas_limite', 0)}")
        print()
        print(f"  Leads captados: {resumo.get('captados_total', n_leads)}")
        print(f"  Última atualização: {cp.get('atualizado_em', 'N/A')}")
        print(f"  Última tarefa: {cp.get('ultima_tarefa', 'N/A')}")
        print(f"  Motivo interrupção: {cp.get('motivo_interrupcao', 'N/A')}")
        print()
        print(f"  Arquivos:")
        print(f"    Config:     {run_dir / 'config.json'}")
        print(f"    Checkpoint: {run_dir / 'checkpoint.json'}")
        print(f"    Fila:       {run_dir / 'fila.json'}")
        print(f"    Leads CSV:  {run_dir / 'leads_parciais.csv'} ({n_leads} registros)")
        print(f"    Resumo:     {run_dir / 'resumo.json'}")
        print("=" * 60)
    else:
        # Lista runs recentes
        runs = sorted(RUNS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        print()
        print("=" * 60)
        print("  RUNS RECENTES")
        print("=" * 60)
        for r in runs[:15]:
            if not r.is_dir():
                continue
            cp_path = r / "checkpoint.json"
            cfg_path = r / "config.json"
            if cp_path.exists() and cfg_path.exists():
                import json
                cp = json.loads(cp_path.read_text(encoding="utf-8"))
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                escopo = cfg.get("escopo_descritor", cfg.get("escopo", "?"))
                print(f"  {r.name}")
                print(f"    Status: {cp.get('status_run', '?')} | "
                      f"Concl: {cp.get('concluidas', 0)} | "
                      f"Pend: {cp.get('pendentes', 0)} | "
                      f"Erro: {cp.get('erro', 0)} | "
                      f"Leads: {cp.get('captados_total', 0)}")
                print(f"    Escopo: {escopo} | "
                      f"Atualizado: {str(cp.get('atualizado_em', '?'))[:19]}")
                print()
        print("  Use: python executar_campanha_avgestao.py --status --run-id <RUN_ID>")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador AVGESTAO — mapear, prospectar e gerar campanha em um comando",
    )
    parser.add_argument("--etapas", default="mapear,prospectar,campanha",
                        help="Etapas a executar (separadas por virgula). Padrao: mapear,prospectar,campanha")
    parser.add_argument("--top", type=int, default=50,
                        help="Quantos leads na campanha final (padrao: 50)")
    parser.add_argument("--somente-confirmados", action="store_true",
                        help="Filtrar apenas leads com faz_assistencia=CONFIRMADO na campanha")
    parser.add_argument("--score-minimo", type=int, default=None,
                        help="Score AVGESTAO minimo para entrar na campanha")
    parser.add_argument("--grupo", default=None,
                        help="Grupo AVGESTAO")
    parser.add_argument("--escopo", default=None,
                        help="Escopo geografico")
    parser.add_argument("--cidade", default=None)
    parser.add_argument("--cidades", nargs="+", default=None)
    parser.add_argument("--uf", nargs="+", default=None)
    parser.add_argument("--ufs", nargs="+", default=None, dest="ufs")
    parser.add_argument("--regiao", default=None)
    parser.add_argument("--cidades-arquivo", default=None)
    parser.add_argument("--limite-cidades", type=int, default=None)
    parser.add_argument("--max-por-cidade", type=int, default=None)
    parser.add_argument("--max-por-subnicho", type=int, default=None)
    parser.add_argument("--max-total", type=int, default=None)
    parser.add_argument("--max-por-consulta", type=int, default=None)
    parser.add_argument("--ordem-cidades", default=None)
    parser.add_argument("--delay-min", type=float, default=None)
    parser.add_argument("--delay-max", type=float, default=None)
    parser.add_argument("--max-tentativas", type=int, default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--somente-gerar-fila", action="store_true")
    parser.add_argument("--permitir-base-incompleta", action="store_true")
    parser.add_argument("--confirmar-grande-execucao", action="store_true")
    parser.add_argument("--status", action="store_true",
                        help="Modo status: consulta estado do run sem abrir navegador")
    args = parser.parse_args()

    # ── MODO STATUS (somente leitura, sem abrir navegador) ────────────
    if args.status:
        _modo_status(args)
        return

    etapas = [e.strip() for e in args.etapas.split(",") if e.strip()]
    if not etapas:
        print("❌ Nenhuma etapa informada.")
        sys.exit(1)

    run_id = args.run_id
    if args.resume:
        if not args.run_id:
            print("❌ --resume exige --run-id")
            sys.exit(1)
        run_dir = RUNS_DIR / args.run_id
        if not run_dir.exists() or not (run_dir / "config.json").exists():
            print(f"❌ Run inexistente ou invalido: {args.run_id}")
            sys.exit(1)
    else:
        if args.run_id:
            run_dir = RUNS_DIR / args.run_id
            run_dir.mkdir(parents=True, exist_ok=True)
        else:
            run_id = _gerar_run_id()
            run_dir = RUNS_DIR / run_id

    print()
    print("=" * 70)
    print("  ORQUESTRADOR AVGESTAO")
    print(f"  Run ID: {run_id}")
    print(f"  Etapas: {', '.join(etapas)}")
    print("=" * 70)

    rodar_mapear = "mapear" in etapas
    rodar_prospectar = "prospectar" in etapas
    rodar_campanha = "campanha" in etapas

    is_dry = args.dry_run or args.somente_gerar_fila

    if rodar_mapear:
        cmd = _flags_mapear(args, run_id)
        if not _executar("mapear", cmd, run_id, run_dir):
            _listar_arquivos(run_dir)
            sys.exit(1)

        if is_dry:
            print("   (dry-run / somente-gerar-fila — fluxo termina apos geracao da fila)")
            _listar_arquivos(run_dir)
            return

    if rodar_prospectar:
        geo = _encontrar_xlsx_geo(run_dir)
        if not geo:
            print("❌ Nenhum XLSX geografico encontrado no run — a etapa mapear gerou saida?")
            sys.exit(1)
        cmd = _flags_prospectar(args, geo)
        if not _executar("prospectar", cmd, run_id, run_dir):
            _listar_arquivos(run_dir)
            sys.exit(1)

    if rodar_campanha:
        prospect_xlsx = BASE_DIR / "output" / "avgestao" / f"prospeccao_avgestao_{args.grupo or 'todos'}.xlsx"
        if not prospect_xlsx.exists():
            geos = sorted(run_dir.glob("leads_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
            if geos:
                prospect_xlsx = geos[0]
            else:
                print("❌ Nenhum XLSX de prospeccao encontrado — a etapa prospectar gerou saida?")
                sys.exit(1)
        cmd = _flags_campanha(args, prospect_xlsx)
        if not _executar("campanha", cmd, run_id, run_dir):
            _listar_arquivos(run_dir)
            sys.exit(1)

    _listar_arquivos(run_dir)
    print("✅ Orquestrador concluido. NENHUMA mensagem foi enviada.")
    print(f"   Para retomar: python executar_campanha_avgestao.py --resume --run-id {run_id}")


if __name__ == "__main__":
    main()
