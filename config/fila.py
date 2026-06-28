"""
config/fila.py — geracao e persistencia da fila de captacao.

A fila eh gerada ANTES de abrir o navegador e representa TODAS as consultas
planejadas (produto cartesiano grupo x municipio x subnicho). Os limites
(max_por_cidade / max_por_subnicho / max_total) NAO truncam a fila na geracao:
eles sao verificados em runtime pelo orquestrador, marcando as tarefas nao
executadas com status ignorada_limite / pausada_limite (nunca erro/interrompida).

Cada item mapeia 1:1 para uma chamada de buscar_categoria.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from config.avgestao import GrupoConfig
from config.territorios import Municipio


STATUS_PENDENTE = "pendente"
STATUS_EM_ANDAMENTO = "em_andamento"
STATUS_CONCLUIDA = "concluida"
STATUS_ERRO = "erro"
STATUS_INTERROMPIDA = "interrompida"
STATUS_IGNORADA_LIMITE = "ignorada_limite"
STATUS_PAUSADA_LIMITE = "pausada_limite"

STATUS_TODOS = (
    STATUS_PENDENTE,
    STATUS_EM_ANDAMENTO,
    STATUS_CONCLUIDA,
    STATUS_ERRO,
    STATUS_INTERROMPIDA,
    STATUS_IGNORADA_LIMITE,
    STATUS_PAUSADA_LIMITE,
)

# tarefas que ainda devem ser executadas (ou re-executadas) no resume
STATUS_EXECUTAVEIS = (STATUS_PENDENTE, STATUS_EM_ANDAMENTO, STATUS_ERRO)


@dataclass
class ItemFila:
    id_tarefa: str
    cidade: str            # nome exibido (acentuado)
    uf: str
    regiao: str
    grupo: str              # chave do grupo
    subnicho: str           # chave curta
    subnicho_label: str
    msg_cat: str
    query: str              # termo pronto para o Google Maps
    status: str = STATUS_PENDENTE
    tentativas: int = 0
    captados: int = 0
    iniciado_em: Optional[str] = None
    concluido_em: Optional[str] = None
    erro: str = ""


def _id_tarefa(grupo_key: str, query_subnicho: str, municipio: Municipio) -> str:
    """Id deterministico: mesmo plano -> mesmos ids (estavel entre gerar/executar)."""
    base = f"{grupo_key}|{query_subnicho}|{municipio.chave()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def gerar_fila(
    grupos: list[GrupoConfig],
    municipios: list[Municipio],
    *,
    max_por_consulta: int = 20,
    run_id: Optional[str] = None,
) -> list[ItemFila]:
    """Gera a fila completa (produto cartesiano grupo x municipio x subnicho).

    Os limites max_por_cidade/max_por_subnicho/max_total NAO sao aplicados
    aqui — a fila representa todas as consultas planejadas. Eles sao
    verificados em runtime pelo orquestrador.

    A ordem eh municipio-outer (na ordem recebida de territorios.resolver_cidades,
    ja respeitando --ordem-cidades) e subnicho-inner.
    """
    fila: list[ItemFila] = []
    for municipio in municipios:
        for grupo in grupos:
            for sub in grupo.subnichos:
                query = f"{sub.query} em {municipio.nome}, {municipio.uf}"
                fila.append(ItemFila(
                    id_tarefa=_id_tarefa(grupo.key, sub.query, municipio),
                    cidade=municipio.nome,
                    uf=municipio.uf,
                    regiao=municipio.regiao,
                    grupo=grupo.key,
                    subnicho=sub.subnicho_key,
                    subnicho_label=sub.label,
                    msg_cat=sub.msg_cat,
                    query=query,
                ))
    return fila


def distribuicao_estimada(
    fila: list[ItemFila], max_por_consulta: int = 20
) -> dict:
    """Agrega a fila por uf/regiao/grupo/subnicho e estima o maximo de leads.

    estimativa_maxima = len(fila) * max_por_consulta (teto teorico).
    """
    por_uf: dict[str, int] = {}
    por_regiao: dict[str, int] = {}
    por_grupo: dict[str, int] = {}
    por_subnicho: dict[str, int] = {}
    por_cidade: dict[str, int] = {}
    for item in fila:
        por_uf[item.uf] = por_uf.get(item.uf, 0) + 1
        por_regiao[item.regiao] = por_regiao.get(item.regiao, 0) + 1
        por_grupo[item.grupo] = por_grupo.get(item.grupo, 0) + 1
        chave_sub = f"{item.grupo}:{item.subnicho}"
        por_subnicho[chave_sub] = por_subnicho.get(chave_sub, 0) + 1
        chave_cid = f"{item.cidade},{item.uf}"
        por_cidade[chave_cid] = por_cidade.get(chave_cid, 0) + 1
    return {
        "total_tarefas": len(fila),
        "estimativa_maxima_leads": len(fila) * max(0, max_por_consulta),
        "max_por_consulta": max_por_consulta,
        "por_uf": por_uf,
        "por_regiao": por_regiao,
        "por_grupo": por_grupo,
        "por_subnicho": por_subnicho,
        "por_cidade": por_cidade,
        "cidades": len(por_cidade),
        "ufs": len(por_uf),
    }


def salvar_fila(fila: list[ItemFila], caminho: str | Path) -> Path:
    """Salva a fila em JSON (UTF-8, sem quebra de linha final ambigua)."""
    p = Path(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    dados = [asdict(item) for item in fila]
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def carregar_fila(caminho: str | Path) -> list[ItemFila]:
    """Carrega a fila de um JSON, reconstruindo os dataclasses."""
    p = Path(caminho)
    dados = json.loads(p.read_text(encoding="utf-8"))
    fila: list[ItemFila] = []
    for d in dados:
        # tolerancia a campos ausentes em filas antigas
        fila.append(ItemFila(
            id_tarefa=d["id_tarefa"],
            cidade=d["cidade"],
            uf=d["uf"],
            regiao=d.get("regiao", ""),
            grupo=d["grupo"],
            subnicho=d["subnicho"],
            subnicho_label=d["subnicho_label"],
            msg_cat=d["msg_cat"],
            query=d["query"],
            status=d.get("status", STATUS_PENDENTE),
            tentativas=d.get("tentativas", 0),
            captados=d.get("captados", 0),
            iniciado_em=d.get("iniciado_em"),
            concluido_em=d.get("concluido_em"),
            erro=d.get("erro", ""),
        ))
    return fila


def atualizar_status_item(
    fila: list[ItemFila], id_tarefa: str, **campos
) -> Optional[ItemFila]:
    """Atualiza campos de um item in-place; devolve o item ou None."""
    for item in fila:
        if item.id_tarefa == id_tarefa:
            for k, v in campos.items():
                if hasattr(item, k):
                    setattr(item, k, v)
            return item
    return None


def buscar_item(fila: list[ItemFila], id_tarefa: str) -> Optional[ItemFila]:
    for item in fila:
        if item.id_tarefa == id_tarefa:
            return item
    return None


def filtrar_por_status(fila: list[ItemFila], status: tuple[str, ...]) -> list[ItemFila]:
    return [item for item in fila if item.status in status]


def contagem_por_status(fila: list[ItemFila]) -> dict[str, int]:
    cont: dict[str, int] = {}
    for item in fila:
        cont[item.status] = cont.get(item.status, 0) + 1
    return cont