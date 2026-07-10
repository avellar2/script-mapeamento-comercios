"""
config/runs.py — gestao do diretorio por execucao (run) + checkpoint.

Cada execucao tem uma pasta output/avgestao/runs/<run_id>/ com:
    config.json        — configuracao estrutural do run
    fila.json          — fila de captacao (estado por tarefa)
    checkpoint.json    — agregador de estado do run
    leads_parciais.csv — leads aceitos (append incremental)
    leads_parciais.xlsx— exportacao final
    erros.jsonl        — erros por tarefa (1 JSON por linha)
    execucao.log       — log textual
    resumo.json        — resumo final

Escrita ATOMICA: todos os JSON sao gravados via arquivo temporario +
flush + fsync + os.replace, para nunca deixar arquivo parcial visivel.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config.fila import ItemFila, salvar_fila as _salvar_fila_json, STATUS_INTERROMPIDA


OUTPUT_BASE = Path("output") / "avgestao" / "runs"
VERSAO_FILA = 1

# Colunas do CSV de leads parciais (inclui campos geograficos).
# Ordem estavel; valores ausentes viram "".
COLUNAS_CSV_GEO = [
    "nome", "telefone", "whatsapp", "telefone_normalizado",
    "endereco", "bairro", "email", "site", "instagram",
    "avaliacao", "num_avaliacoes", "place_id", "maps_url",
    "cidade", "uf", "estado", "regiao",
    "grupo", "subnicho", "subnicho_label", "msg_cat",
    "source_query", "source_scope", "run_id", "captured_at",
]


# ══════════════════════════════════════════════════════════════════
# RUN ID E CAMINHOS
# ══════════════════════════════════════════════════════════════════

def gerar_run_id() -> str:
    """Gera um run_id estavel no formato run_YYYYMMDD_HHMMSS_<hex6>."""
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    sufixo = hashlib.sha1(os.urandom(16)).hexdigest()[:6]
    return f"run_{agora}_{sufixo}"


def pasta_run(run_id: str) -> Path:
    p = OUTPUT_BASE / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def caminhos_run(run_id: str) -> dict[str, Path]:
    base = pasta_run(run_id)
    return {
        "base": base,
        "config": base / "config.json",
        "fila": base / "fila.json",
        "checkpoint": base / "checkpoint.json",
        "leads_csv": base / "leads_parciais.csv",
        "leads_xlsx": base / "leads_parciais.xlsx",
        "erros": base / "erros.jsonl",
        "log": base / "execucao.log",
        "resumo": base / "resumo.json",
        "screenshots": base / "screenshots",
    }


# ══════════════════════════════════════════════════════════════════
# ESCRITA ATOMICA
# ══════════════════════════════════════════════════════════════════

def _salvar_atomic_texto(caminho: Path, conteudo: str) -> None:
    """Escreve texto atomicamente: tmp -> flush+fsync -> os.replace."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(conteudo)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass  # alguns SOs nao suportam fsync em certos contextos
    os.replace(tmp, caminho)


def _salvar_atomic_bytes(caminho: Path, dados: bytes) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    with tmp.open("wb") as f:
        f.write(dados)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, caminho)


def salvar_json_atomico(caminho: str | Path, objeto: Any) -> Path:
    """Salva um objeto como JSON de forma atomica (UTF-8, indent=2)."""
    p = Path(caminho)
    conteudo = json.dumps(objeto, ensure_ascii=False, indent=2, default=str)
    _salvar_atomic_texto(p, conteudo)
    return p


def carregar_json(caminho: str | Path) -> Any:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════

# Campos estruturais que definem a identidade do run. Mudar qualquer um
# invalida o resume. delay/headless/max_tentativas NAO sao estruturais.
CAMPOS_ESTRUTURAIS = [
    "produto", "grupos", "escopo", "escopo_descritor",
    "municipios", "subnichos", "consultas",
    "ordem_cidades", "max_por_consulta", "max_por_cidade",
    "max_por_subnicho", "max_total", "versao_fila",
]

# campos que PODEM mudar sem invalidar o run
CAMPOS_NAO_ESTRUTURAIS = ["delay_min", "delay_max", "max_tentativas", "headless"]


def _normalizar_municipios(municipios: Any) -> list[str]:
    """Converte lista de Municipio/dict em lista canonical de 'nome|uf'."""
    out: list[str] = []
    for m in municipios or []:
        if isinstance(m, dict):
            nome = m.get("nome_normalizado") or m.get("nome") or ""
            uf = m.get("uf") or ""
        else:
            nome = getattr(m, "nome_normalizado", None) or getattr(m, "nome", "")
            uf = getattr(m, "uf", "")
        from config.avgestao import normalizar_texto
        out.append(f"{normalizar_texto(nome)}|{normalizar_texto(uf)}")
    return sorted(out)


def _extrair_estrutura(config: dict) -> dict:
    """Extrai o sub-dict estrutural canonico para hash/diff."""
    from config.avgestao import normalizar_texto

    def _norm_lista(v):
        if v is None:
            return []
        return sorted([normalizar_texto(x) for x in v])

    return {
        "produto": config.get("produto", ""),
        "grupos": _norm_lista(config.get("grupos")),
        "escopo": config.get("escopo", ""),
        "escopo_descritor": config.get("escopo_descritor", ""),
        "municipios": _normalizar_municipios(config.get("municipios")),
        "subnichos": _norm_lista(config.get("subnichos")),
        "consultas": _norm_lista(config.get("consultas")),
        "ordem_cidades": config.get("ordem_cidades", ""),
        "max_por_consulta": config.get("max_por_consulta"),
        "max_por_cidade": config.get("max_por_cidade"),
        "max_por_subnicho": config.get("max_por_subnicho"),
        "max_total": config.get("max_total"),
        "versao_fila": config.get("versao_fila", VERSAO_FILA),
    }


def config_hash(config: dict) -> str:
    """Hash deterministico (SHA-256) da configuracao estrutural do run.

    delay_min/delay_max/headless/max_tentativas NAO entram no hash, entao
    podem mudar entre resume sem invalidar o run.
    """
    estrutura = _extrair_estrutura(config)
    canonico = json.dumps(estrutura, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def salvar_config(run_id: str, config: dict) -> Path:
    config = dict(config)
    config.setdefault("run_id", run_id)
    config.setdefault("versao_fila", VERSAO_FILA)
    config["config_hash"] = config_hash(config)
    return salvar_json_atomico(caminhos_run(run_id)["config"], config)


def carregar_config(run_id: str) -> dict:
    return carregar_json(caminhos_run(run_id)["config"])


def verificar_compatibilidade_resume(config_salvo: dict, config_atual: dict) -> list[str]:
    """Devolve lista de motivos de incompatibilidade (vazia se compativel).

    Compara apenas campos estruturais. delay/headless/max_tentativas podem
    differ sem invalidar.
    """
    motivos: list[str] = []
    # valida hash se o salvo tiver
    hash_salvo = config_salvo.get("config_hash")
    hash_atual = config_hash(config_atual)
    if hash_salvo and hash_salvo != hash_atual:
        # diff campo a campo para mensagem legivel
        est_salvo = _extrair_estrutura(config_salvo)
        est_atual = _extrair_estrutura(config_atual)
        for campo in CAMPOS_ESTRUTURAIS:
            if est_salvo.get(campo) != est_atual.get(campo):
                motivos.append(
                    f"campo estrutural divergente: {campo} "
                    f"(salvo={est_salvo.get(campo)!r} vs atual={est_atual.get(campo)!r})"
                )
        if not motivos:
            motivos.append("config_hash diverge mas nenhum campo estrutural "
                           "identificado (revise versao_fila ou municipios)")
    elif not hash_salvo:
        # run antigo sem hash: compara estrutural direto
        est_salvo = _extrair_estrutura(config_salvo)
        est_atual = _extrair_estrutura(config_atual)
        for campo in CAMPOS_ESTRUTURAIS:
            if est_salvo.get(campo) != est_atual.get(campo):
                motivos.append(f"campo estrutural divergente: {campo}")
    return motivos


# ══════════════════════════════════════════════════════════════════
# CHECKPOINT
# ══════════════════════════════════════════════════════════════════

def novo_checkpoint(run_id: str, total_tarefas: int) -> dict:
    return {
        "run_id": run_id,
        "atualizado_em": None,
        "status_run": "em_andamento",
        "total_tarefas": total_tarefas,
        "concluidas": 0,
        "pendentes": total_tarefas,
        "em_andamento": 0,
        "erro": 0,
        "interrompidas": 0,
        "ignoradas_limite": 0,
        "pausadas_limite": 0,
        "unicos_por_cidade": {},
        "unicos_por_subnicho": {},
        "unicos_total": 0,
        "captados_total": 0,
        "por_subnicho": {},
        "por_cidade": {},
        "por_uf": {},
        "ultima_tarefa": None,
        "captcha_detectado": False,
        "motivo_interrupcao": "",
        "config_hash": None,
    }


def salvar_checkpoint(run_id: str, checkpoint: dict) -> Path:
    return salvar_json_atomico(caminhos_run(run_id)["checkpoint"], checkpoint)


def carregar_checkpoint(run_id: str) -> dict:
    p = caminhos_run(run_id)["checkpoint"]
    if not p.exists():
        return {}
    return carregar_json(p)


# ══════════════════════════════════════════════════════════════════
# FILA (alias atomico sobre config/fila)
# ══════════════════════════════════════════════════════════════════

def salvar_fila_run(run_id: str, fila: list[ItemFila]) -> Path:
    """Salva fila.json atomicamente (escreve tmp+fsync+replace por item)."""
    caminho = caminhos_run(run_id)["fila"]
    dados = [asdict(item) for item in fila]
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    _salvar_atomic_texto(caminho, conteudo)
    return caminho


# ══════════════════════════════════════════════════════════════════
# RESUMO
# ══════════════════════════════════════════════════════════════════

def salvar_resumo(run_id: str, resumo: dict) -> Path:
    return salvar_json_atomico(caminhos_run(run_id)["resumo"], resumo)


def carregar_resumo(run_id: str) -> dict:
    p = caminhos_run(run_id)["resumo"]
    if not p.exists():
        return {}
    return carregar_json(p)


# ══════════════════════════════════════════════════════════════════
# LEADS PARCIAIS (CSV incremental)
# ══════════════════════════════════════════════════════════════════

def anexar_linha_csv(run_id: str, leads: list[dict]) -> Path:
    """Append incremental em leads_parciais.csv. Escreve cabeçalho se novo."""
    caminho = caminhos_run(run_id)["leads_csv"]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo_arquivo = not caminho.exists()
    # append nao-atomico por linha eh aceitavel para CSV incremental; se o
    # processo cair, linhas ja escritas permanecem e o resume as le.
    with caminho.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS_CSV_GEO, extrasaction="ignore")
        if novo_arquivo:
            writer.writeheader()
        for lead in leads:
            writer.writerow({col: lead.get(col, "") for col in COLUNAS_CSV_GEO})
    return caminho


def ler_leads_parciais(run_id: str) -> list[dict]:
    """Le todos os leads parciais do run (para dedup/retomada)."""
    caminho = caminhos_run(run_id)["leads_csv"]
    if not caminho.exists():
        return []
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ══════════════════════════════════════════════════════════════════
# ERROS (JSONL)
# ══════════════════════════════════════════════════════════════════

def registrar_erro(run_id: str, item: dict | None, exc: BaseException | str) -> None:
    caminho = caminhos_run(run_id)["erros"]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "timestamp": datetime.now().isoformat(),
        "id_tarefa": (item.get("id_tarefa") if isinstance(item, dict) else None),
        "cidade": (item.get("cidade") if isinstance(item, dict) else None),
        "subnicho": (item.get("subnicho") if isinstance(item, dict) else None),
        "erro": str(exc),
    }
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


# ══════════════════════════════════════════════════════════════════
# RESGATE DE INTERRUPCAO (KeyboardInterrupt / CancelledError)
# ══════════════════════════════════════════════════════════════════

def salvar_estado_interrupcao(
    run_id: str,
    fila: list[ItemFila],
    checkpoint: dict,
    id_tarefa_atual: Optional[str],
    motivo: str,
) -> None:
    """Marca a tarefa atual como interrompida e salva fila+checkpoint atomicamente.

    Usado pelo orquestrador ao capturar KeyboardInterrupt/asyncio.CancelledError
    (e ao detectar CAPTCHA). Garante estado persistido antes de encerrar.
    """
    agora = datetime.now().isoformat()
    if id_tarefa_atual:
        for item in fila:
            if item.id_tarefa == id_tarefa_atual and item.status not in (
                STATUS_INTERROMPIDA, "concluida",
            ):
                item.status = STATUS_INTERROMPIDA
                item.erro = (item.erro or "") + f" | interrompido: {motivo}"
                break
    checkpoint["atualizado_em"] = agora
    checkpoint["status_run"] = "interrompido"
    checkpoint["motivo_interrupcao"] = motivo
    # reconta status
    cont = _contar_status(fila)
    checkpoint.update(cont)
    salvar_fila_run(run_id, fila)
    salvar_checkpoint(run_id, checkpoint)


def _contar_status(fila: list[ItemFila]) -> dict:
    cont = {
        "concluidas": 0, "pendentes": 0, "em_andamento": 0,
        "erro": 0, "interrompidas": 0, "ignoradas_limite": 0, "pausadas_limite": 0,
    }
    mapa = {
        "concluida": "concluidas", "pendente": "pendentes",
        "em_andamento": "em_andamento", "erro": "erro",
        "interrompida": "interrompidas",
        "ignorada_limite": "ignoradas_limite", "pausada_limite": "pausadas_limite",
    }
    for item in fila:
        chave = mapa.get(item.status)
        if chave:
            cont[chave] += 1
    return cont


def listar_runs() -> list[str]:
    """Lista run_ids existentes ordenados por mtime desc (mais recente primeiro)."""
    if not OUTPUT_BASE.exists():
        return []
    runs = []
    for p in OUTPUT_BASE.iterdir():
        if p.is_dir():
            try:
                runs.append((p.stat().st_mtime, p.name))
            except OSError:
                continue
    runs.sort(reverse=True)
    return [nome for _, nome in runs]