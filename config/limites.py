"""
config/limites.py — controle de volume por leads unicos aceitos.

Os limites max_por_cidade, max_por_subnicho e max_total contam LEADS UNICOS
ACEITOS durante a execucao (que passaram pela dedup e foram gravados), NAO a
quantidade de tarefas criadas. A fila continua representando todas as
consultas planejadas.

Quando um limite eh atingido, as tarefas nao executadas recebem status
ignorada_limite (nunca erro/interrompida). Alterar limites exige um novo run:
nao ha retomada aumentando limites no mesmo run (o config_hash invalida).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from config.fila import (
    ItemFila,
    STATUS_EM_ANDAMENTO,
    STATUS_IGNORADA_LIMITE,
    STATUS_PENDENTE,
    atualizar_status_item,
)


@dataclass
class ContadoresLimites:
    """Contadores de leads unicos aceitos (nao de tarefas)."""
    unicos_por_cidade: dict[str, int] = field(default_factory=dict)
    unicos_por_subnicho: dict[str, int] = field(default_factory=dict)
    unicos_total: int = 0

    def registrar_aceito(self, cidade: str, subnicho: str) -> None:
        chave_cid = cidade or ""
        chave_sub = subnicho or ""
        self.unicos_por_cidade[chave_cid] = self.unicos_por_cidade.get(chave_cid, 0) + 1
        self.unicos_por_subnicho[chave_sub] = self.unicos_por_subnicho.get(chave_sub, 0) + 1
        self.unicos_total += 1

    def reset(self) -> None:
        self.unicos_por_cidade.clear()
        self.unicos_por_subnicho.clear()
        self.unicos_total = 0


@dataclass
class Limites:
    max_por_cidade: Optional[int] = None
    max_por_subnicho: Optional[int] = None
    max_total: Optional[int] = None

    def ativos(self) -> bool:
        return any(v is not None and v > 0 for v in (
            self.max_por_cidade, self.max_por_subnicho, self.max_total))


def limite_total_atingido(cont: ContadoresLimites, lim: Limites) -> bool:
    return lim.max_total is not None and lim.max_total > 0 and cont.unicos_total >= lim.max_total


def limite_cidade_atingido(cont: ContadoresLimites, lim: Limites, cidade: str) -> bool:
    if lim.max_por_cidade is None or lim.max_por_cidade <= 0:
        return False
    return cont.unicos_por_cidade.get(cidade or "", 0) >= lim.max_por_cidade


def limite_subnicho_atingido(cont: ContadoresLimites, lim: Limites, subnicho: str) -> bool:
    if lim.max_por_subnicho is None or lim.max_por_subnicho <= 0:
        return False
    return cont.unicos_por_subnicho.get(subnicho or "", 0) >= lim.max_por_subnicho


@dataclass
class MotorLimites:
    """Decide se uma tarefa pode ser despachada com base nos limites.

    Marca tarefas puladas por limite como ignorada_limite (in-place na fila).
    """
    limites: Limites
    contadores: ContadoresLimites
    total_atingido: bool = False

    def pode_despachar(self, item: ItemFila) -> tuple[bool, str]:
        """Retorna (pode, status_a_aplicar_se_nao_pode).

        status_a_aplicar eh STATUS_IGNORADA_LIMITE quando nao pode por limite.
        """
        if self.total_atingido:
            return False, STATUS_IGNORADA_LIMITE
        if limite_total_atingido(self.contadores, self.limites):
            self.total_atingido = True
            return False, STATUS_IGNORADA_LIMITE
        if limite_subnicho_atingido(self.contadores, self.limites, item.subnicho):
            return False, STATUS_IGNORADA_LIMITE
        if limite_cidade_atingido(self.contadores, self.limites, item.cidade):
            return False, STATUS_IGNORADA_LIMITE
        return True, STATUS_PENDENTE

    def registrar_aceito(self, item: ItemFila) -> None:
        """Chamar apos aceitar leads unicos da tarefa."""
        self.contadores.registrar_aceito(item.cidade, item.subnicho)

    def marcar_ignoradas_a_partir_de(self, fila: list[ItemFila], indice: int) -> int:
        """Marca como ignorada_limite todas as tarefas pendentes a partir de indice.

        Usado quando max_total eh atingido. Devolve a quantidade marcada.
        Nao trunca a fila (so muda status). Tarefas concluidas/erro nao sao tocadas.
        """
        n = 0
        for item in fila[indice:]:
            if item.status in (STATUS_PENDENTE, STATUS_EM_ANDAMENTO):
                item.status = STATUS_IGNORADA_LIMITE
                n += 1
        return n


def recontar_resumo_limites(fila: list[ItemFila], cont: ContadoresLimites) -> dict:
    """Resumo de status + contadores para checkpoint/resumo."""
    status = {
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
        k = mapa.get(item.status)
        if k:
            status[k] += 1
    status["unicos_total"] = cont.unicos_total
    status["unicos_por_cidade"] = dict(cont.unicos_por_cidade)
    status["unicos_por_subnicho"] = dict(cont.unicos_por_subnicho)
    return status