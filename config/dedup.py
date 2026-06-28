"""
config/dedup.py — deduplicacao global de leads (5 niveis, dois tempos).

Diferente de config.avgestao.deduplicar_leads (que permanece intocado para
compatibilidade), este modulo implementa a dedup global usada pelo fluxo
escalonado:

Para cada lead (dois tempos):
  1. Gera TODAS as chaves disponiveis.
  2. Verifica correspondencia em TODOS os indices fortes:
       place_id, maps_url, telefone.
     Se qualquer forte bater, eh duplicata.
  3. Se nenhum forte bateu, verifica o fallback nome+endereco (exato,
     nunca fuzzy). Se bater, eh duplicata.
  4. Se o lead NAO tem nenhum identificador forte preenchido e tambem nao
     tem nome+endereco, verifica nome+cidade (ultimo fallback, exato).
  5. Sendo ineditito, registra TODAS as chaves disponiveis nos indices.

Regras especificas:
- place_id e maps_url sao fortes e unicos por localizacao.
- telefone eh forte, MAS telefone igual em cidades diferentes NAO elimina
  automaticamente uma filial: o telefone so deduplica quando as cidades sao
  iguais (ambas presentes e iguais). Cidades diferentes ou ausentes -> o
  telefone nao deduplica sozinho (protege filiais).
- nome+cidade so eh usado quando nao ha identificadores fortes.
- Sem comparacao fuzzy: nomes parecidos (mas nao identicos apos
  normalizacao) nunca colapsam dois estabelecimentos diferentes.
"""

from __future__ import annotations

from typing import Iterable, Optional

from config.avgestao import normalizar_texto
from utils.phone_utils import normalizar_telefone_br


# ══════════════════════════════════════════════════════════════════
# NORMALIZACAO DE CHAVES
# ══════════════════════════════════════════════════════════════════

def normalizar_place_id(valor) -> str:
    if not valor:
        return ""
    return str(valor).strip().casefold()


def normalizar_maps_url(valor) -> str:
    """Canonicaliza URL do Google Maps.

    Preserva identificadores de place (params `id`, `cid`, `place_id`,
    `feature` e segmentos `data=...` do path) e descarta so tracking
    cosmético (hl, gl, q de busca, fragmento). Sem isso, todas as URLs
    `https://maps.google.com/?id=X` colapsariam em `https://maps.google.com/`
    e o dedup falso rejeitaria leads distintos.
    """
    if not valor:
        return ""
    s = str(valor).strip()
    # remove fragmento
    if "#" in s:
        s = s.split("#", 1)[0]
    # separa base (path) e query
    if "?" in s:
        base, query = s.split("?", 1)
    else:
        base, query = s, ""
    # preserva apenas params de identidade de place
    if query:
        keep = []
        for kv in query.split("&"):
            k = kv.split("=", 1)[0].lower() if "=" in kv else kv.lower()
            if k in ("id", "cid", "place_id", "feature"):
                keep.append(kv)
        s = base + ("?" + "&".join(keep) if keep else "")
    return s.strip().casefold()


def _normalizar_cidade(valor) -> str:
    return normalizar_texto(valor)


def chave_dedup_global(lead: dict) -> dict:
    """Devolve TODAS as chaves de dedup disponiveis para o lead (normalizadas).

    Retorna dict com: place_id, maps_url, telefone, cidade, nome_endereco,
    nome_cidade, has_strong.
    """
    place_id = normalizar_place_id(lead.get("place_id"))
    maps_url = normalizar_maps_url(
        lead.get("link_maps") or lead.get("url_maps") or lead.get("maps_url")
    )
    telefone = normalizar_telefone_br(
        lead.get("whatsapp") or lead.get("telefone") or ""
    ) or ""
    cidade = _normalizar_cidade(lead.get("cidade"))
    nome = normalizar_texto(lead.get("nome"))
    endereco = normalizar_texto(lead.get("endereco"))
    nome_endereco = f"{nome}|{endereco}" if nome and endereco else ""
    nome_cidade = f"{nome}|{cidade}" if nome and cidade else ""
    has_strong = bool(place_id or maps_url or telefone)
    return {
        "place_id": place_id,
        "maps_url": maps_url,
        "telefone": telefone,
        "cidade": cidade,
        "nome_endereco": nome_endereco,
        "nome_cidade": nome_cidade,
        "has_strong": has_strong,
    }


# ══════════════════════════════════════════════════════════════════
# INDEXADOR STATEFUL
# ══════════════════════════════════════════════════════════════════

class IndexadorDedup:
    """Mantem os indices de dedup de uma execucao (entre cidades/estados/run).

    Alimentar com:
    - chaves existentes do Supabase (mesclar_chaves_existentes)
    - leads parciais do run (rehydratacao no resume)
    - leads de cada consulta ao final dela
    """

    def __init__(self) -> None:
        self.vistos_place: set[str] = set()
        self.vistos_maps: set[str] = set()
        # telefone -> set de cidades (normalizadas) onde ja foi visto
        self.vistos_tel: dict[str, set[str]] = {}
        self.vistos_nome_end: set[str] = set()
        self.vistos_nome_cidade: set[str] = set()
        self.aceitos: int = 0
        self.descartados: int = 0

    # ── verificacao de telefone consciente de cidade ──────────────
    def _tel_dup(self, tel: str, cidade: str) -> bool:
        """Telefone so deduplica quando as cidades sao iguais.

        Protege filiais: telefone igual em cidades diferentes (ou cidade
        ausente) NAO elimina automaticamente. So ha duplicata se a mesma
        cidade (ambas presentes e iguais) ja registrou esse telefone.
        """
        if tel not in self.vistos_tel:
            return False
        existing = self.vistos_tel[tel]
        if not cidade:
            return False  # cidade desconhecida -> protege filial
        return cidade in existing  # True apenas se mesma cidade

    # ── núcleo de dois tempos ───────────────────────────────────────
    def add(self, lead: dict) -> bool:
        """Adiciona o lead se for ineditito. Devolve True se aceito.

        Dois tempos:
        1. gera todas as chaves; verifica TODOS os fortes.
        2. se nenhum forte bateu, verifica fallback nome+endereco.
           se o lead nao tem fortes e nem nome+endereco, verifica nome+cidade.
        3. se ineditito, registra TODAS as chaves disponiveis.
        """
        ch = chave_dedup_global(lead)
        pid = ch["place_id"]
        url = ch["maps_url"]
        tel = ch["telefone"]
        cidade = ch["cidade"]
        nome_end = ch["nome_endereco"]
        nome_cid = ch["nome_cidade"]
        has_strong = ch["has_strong"]

        # TEMPO 1: indices fortes
        duplicata = False
        if pid and pid in self.vistos_place:
            duplicata = True
        elif url and url in self.vistos_maps:
            duplicata = True
        elif tel and self._tel_dup(tel, cidade):
            duplicata = True

        # TEMPO 2: fallback nome+endereco (apos fortes falharem)
        if not duplicata and nome_end and nome_end in self.vistos_nome_end:
            duplicata = True

        # TEMPO 2 (ultimo fallback): nome+cidade — so sem fortes e sem nome+end
        if (
            not duplicata
            and not has_strong
            and not nome_end
            and nome_cid
            and nome_cid in self.vistos_nome_cidade
        ):
            duplicata = True

        if duplicata:
            self.descartados += 1
            return False

        # REGISTRO de todas as chaves disponiveis
        if pid:
            self.vistos_place.add(pid)
        if url:
            self.vistos_maps.add(url)
        if tel:
            self.vistos_tel.setdefault(tel, set()).add(cidade)
        if nome_end:
            self.vistos_nome_end.add(nome_end)
        # nome+cidade so eh registrado quando nao ha identificadores fortes
        if not has_strong and nome_cid:
            self.vistos_nome_cidade.add(nome_cid)

        self.aceitos += 1
        return True

    # ── pre-carga de chaves externas ───────────────────────────────
    def mesclar_chaves_existentes(self, chaves: dict) -> None:
        """Pre-carrega chaves ja existentes (Supabase ou outra fonte).

        chaves = {
            "place_ids": set[str],
            "maps_urls": set[str],
            "telefones": set[str] | dict[str, set[str]]  # tel -> cidades
        }
        Telefones sem cidade informada ficam com cidade "" (desconhecida),
        o que NAO elimina filiais (cidade ausente protege).
        """
        for pid in chaves.get("place_ids", ()) or ():
            if pid:
                self.vistos_place.add(normalizar_place_id(pid))
        for url in chaves.get("maps_urls", ()) or ():
            if url:
                self.vistos_maps.add(normalizar_maps_url(url))
        tels = chaves.get("telefones")
        if isinstance(tels, dict):
            for tel, cidades in tels.items():
                if not tel:
                    continue
                bucket = self.vistos_tel.setdefault(tel, set())
                for c in cidades:
                    bucket.add(_normalizar_cidade(c))
        elif isinstance(tels, (set, list, tuple)):
            for tel in tels:
                if tel:
                    self.vistos_tel.setdefault(tel, set()).add("")


# ══════════════════════════════════════════════════════════════════
# FUNCAO PURA
# ══════════════════════════════════════════════════════════════════

def deduplicar_leads_global(leads: Iterable[dict]) -> list[dict]:
    """Deduplica uma lista de leads (funcao pura, sem Supabase).

    Mesma semantica de dois tempos do IndexadorDedup. Usada na exportacao
    final e em testes.
    """
    idx = IndexadorDedup()
    unicos: list[dict] = []
    for lead in leads:
        if idx.add(lead):
            unicos.append(lead)
    return unicos


def mesclar_chaves_existentes(indexador: IndexadorDedup, chaves: dict) -> None:
    """Atalho de compatibilidade."""
    indexador.mesclar_chaves_existentes(chaves)