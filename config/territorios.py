"""
config/territorios.py — fonte unica de geografia (sem rede em runtime).

Toda regra geografica fica aqui. Nenhum outro modulo deve espalhar nomes de
cidade/UF/regiao. O runtime so le o CSV local (config/data/municipios_br.csv);
se ele estiver ausente ou com checksum invalido, usa o fallback bundled minimo
apenas para escopos de cidade; escopos amplos (uf/ufs/regiao/brasil) abortam
com erro claro, a menos que --permitir-base-incompleta seja informado.

Reusa normalizar_texto de config.avgestao para consistencia.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config.avgestao import normalizar_texto


# ══════════════════════════════════════════════════════════════════
# CONSTANTES GEOGRAFICAS
# ══════════════════════════════════════════════════════════════════

REGIOES: dict[str, list[str]] = {
    "norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "centro_oeste": ["DF", "GO", "MT", "MS"],
    "sudeste": ["ES", "MG", "RJ", "SP"],
    "sul": ["PR", "RS", "SC"],
}

_REGIAO_NOMES: dict[str, str] = {
    "norte": "Norte",
    "nordeste": "Nordeste",
    "centro_oeste": "Centro-Oeste",
    "sudeste": "Sudeste",
    "sul": "Sul",
}

# 27 capitais (sigla -> nome com acento, conforme IBGE)
CAPITAIS: dict[str, str] = {
    "AC": "Rio Branco",
    "AL": "Maceió",
    "AP": "Macapá",
    "AM": "Manaus",
    "BA": "Salvador",
    "CE": "Fortaleza",
    "DF": "Brasília",
    "ES": "Vitória",
    "GO": "Goiânia",
    "MA": "São Luís",
    "MT": "Cuiabá",
    "MS": "Campo Grande",
    "MG": "Belo Horizonte",
    "PA": "Belém",
    "PB": "João Pessoa",
    "PR": "Curitiba",
    "PE": "Recife",
    "PI": "Teresina",
    "RJ": "Rio de Janeiro",
    "RN": "Natal",
    "RS": "Porto Alegre",
    "RO": "Porto Velho",
    "RR": "Boa Vista",
    "SC": "Florianópolis",
    "SP": "São Paulo",
    "SE": "Aracaju",
    "TO": "Palmas",
}

# sigla -> nome do estado (acentuado)
UF_NOMES: dict[str, str] = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

TODAS_UFS: list[str] = sorted(UF_NOMES.keys())

CAMPOS_GEOGRAFICOS = ["uf", "estado", "regiao", "source_query", "source_scope",
                      "run_id", "captured_at", "place_id", "maps_url"]


# ══════════════════════════════════════════════════════════════════
# DATACLASS
# ══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Municipio:
    nome: str               # acentuado, forma exibida
    nome_normalizado: str   # sem acento/casefold, para comparacao
    uf: str                 # sigla 2 chars
    uf_nome: str            # nome do estado acentuado
    regiao: str             # norte|nordeste|centro_oeste|sudeste|sul
    capital: bool
    populacao: int
    codigo_ibge: str        # 7 digitos

    def chave(self) -> str:
        """Chave unica de dedup de municipio: nome_normalizado|uf."""
        return f"{self.nome_normalizado}|{self.uf}"

    def nome_uf(self) -> str:
        return f"{self.nome}, {self.uf}"


# ══════════════════════════════════════════════════════════════════
# CAMINHOS DA BASE
# ══════════════════════════════════════════════════════════════════

_DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PATH = _DATA_DIR / "municipios_br.csv"
META_PATH = _DATA_DIR / "municipios_br.meta.json"

_CACHE_ALL: Optional[list[Municipio]] = None
_CACHE_POR_UF: dict[str, list[Municipio]] = {}
_STATUS_CACHE: Optional[dict] = None


# ══════════════════════════════════════════════════════════════════
# NORMALIZACAO
# ══════════════════════════════════════════════════════════════════

def normalizar_nome_cidade(valor) -> str:
    """Normaliza nome de cidade para comparacao (casefold, sem acento/pontuacao)."""
    return normalizar_texto(valor)


def normalizar_uf(valor) -> str:
    """Normaliza sigla de UF: aceita 'rj', 'RJ', 'r.j.', 'Rio de Janeiro' -> 'RJ'."""
    if valor is None:
        return ""
    s = normalizar_texto(valor)
    if not s:
        return ""
    # sigla direta
    up = s.upper().replace(" ", "")
    if up in UF_NOMES:
        return up
    # por nome de estado
    for sigla, nome in UF_NOMES.items():
        if normalizar_texto(nome) == s:
            return sigla
    return up  # devolve uppercased; chamador valida contra UF_NOMES


def nome_exibicao(nome_ou_bruto: str, uf: str = "") -> str:
    """Devolve o nome acentuado do municipio quando encontrado na base.

    Se nao encontrar, devolve o input limpo (title case), sem forjar acentos
    inexistentes. Preserva acentos: a forma exibida vem da base, nao do input.
    """
    if not nome_ou_bruto:
        return ""
    base = _carregar_base_se_disponivel()
    if base:
        norm = normalizar_nome_cidade(nome_ou_bruto)
        uf_up = normalizar_uf(uf) if uf else ""
        for m in base:
            if m.nome_normalizado == norm and (not uf_up or m.uf == uf_up):
                return m.nome
    # fallback: title case do bruto, preservando acentos do input
    return " ".join(p.capitalize() if p else p for p in str(nome_ou_bruto).split())


def _parse_cidade_uf(valor: str) -> tuple[str, str]:
    """Separar 'Cidade, UF' em (nome, uf_sigla). UF pode estar vazia."""
    if valor is None:
        return "", ""
    s = str(valor).strip()
    if "," in s:
        nome, _, uf = s.partition(",")
        return nome.strip(), normalizar_uf(uf.strip())
    return s.strip(), ""


# ══════════════════════════════════════════════════════════════════
# STATUS DA BASE
# ══════════════════════════════════════════════════════════════════

def status_base() -> dict:
    """Status da base local de municipios.

    Retorna dict com:
        completa: bool      — CSV presente E checksum SHA-256 valido E
                              quantidade confere com o metadado.
        quantidade: int     — municipios carregados do CSV (0 se incompleta).
        checksum_ok: bool
        motivo: str          — descricao do problema ("" se ok).
        checksum_esperado: str
        checksum_encontrado: str
    """
    global _STATUS_CACHE
    if _STATUS_CACHE is not None:
        return _STATUS_CACHE

    resultado = {
        "completa": False,
        "quantidade": 0,
        "checksum_ok": False,
        "motivo": "",
        "checksum_esperado": "",
        "checksum_encontrado": "",
    }
    if not CSV_PATH.exists():
        resultado["motivo"] = f"CSV ausente: {CSV_PATH}"
        _STATUS_CACHE = resultado
        return resultado
    if not META_PATH.exists():
        resultado["motivo"] = f"metadado ausente: {META_PATH}"
        _STATUS_CACHE = resultado
        return resultado

    try:
        conteudo = CSV_PATH.read_bytes()
        checksum = hashlib.sha256(conteudo).hexdigest()
    except Exception as e:
        resultado["motivo"] = f"erro ao ler CSV: {e}"
        _STATUS_CACHE = resultado
        return resultado

    try:
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        resultado["motivo"] = f"metadado invalido: {e}"
        _STATUS_CACHE = resultado
        return resultado

    esperado = meta.get("checksum_sha256", "")
    resultado["checksum_esperado"] = esperado
    resultado["checksum_encontrado"] = checksum
    if not esperado:
        resultado["motivo"] = "metadado sem checksum_sha256 (obrigatorio)"
        _STATUS_CACHE = resultado
        return resultado
    if checksum != esperado:
        resultado["motivo"] = "checksum SHA-256 do CSV nao confere com o metadado"
        _STATUS_CACHE = resultado
        return resultado

    resultado["checksum_ok"] = True
    # conta linhas de dados (exclui cabecalho)
    try:
        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            qtd = sum(1 for _ in csv.DictReader(f))
    except Exception as e:
        resultado["motivo"] = f"erro ao contar municpios: {e}"
        _STATUS_CACHE = resultado
        return resultado

    esperado_qtd = meta.get("quantidade_municipios")
    if esperado_qtd is not None and qtd != esperado_qtd:
        resultado["motivo"] = f"quantidade diverge: CSV={qtd}, meta={esperado_qtd}"
        _STATUS_CACHE = resultado
        return resultado

    resultado["completa"] = True
    resultado["quantidade"] = qtd
    _STATUS_CACHE = resultado
    return resultado


def base_completa() -> bool:
    """True se a base local completa e valida (CSV + checksum + quantidade)."""
    return bool(status_base().get("completa"))


def _reset_status_cache() -> None:
    """Para testes: limpa cache de status/base."""
    global _STATUS_CACHE, _CACHE_ALL, _CACHE_POR_UF
    _STATUS_CACHE = None
    _CACHE_ALL = None
    _CACHE_POR_UF = {}


# ══════════════════════════════════════════════════════════════════
# CARREGAMENTO
# ══════════════════════════════════════════════════════════════════

def _carregar_base_se_disponivel() -> Optional[list[Municipio]]:
    """Carrega a base completa se valida; senao None (nao levanta)."""
    if not base_completa():
        return None
    return _carregar_csv_forcado()


def _carregar_csv_forcado() -> list[Municipio]:
    global _CACHE_ALL
    if _CACHE_ALL is not None:
        return _CACHE_ALL
    municipios: list[Municipio] = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            municipios.append(_row_para_municipio(row))
    _CACHE_ALL = municipios
    return municipios


def _row_para_municipio(row: dict) -> Municipio:
    nome = (row.get("nome") or "").strip()
    uf = (row.get("uf") or "").strip().upper()
    uf_nome = (row.get("uf_nome") or UF_NOMES.get(uf, "")).strip()
    regiao = (row.get("regiao") or "").strip().casefold()
    capital = (row.get("capital") or "").strip().lower() in ("true", "1", "sim", "yes")
    try:
        populacao = int(row.get("populacao") or 0)
    except ValueError:
        populacao = 0
    codigo = (row.get("codigo_ibge") or "").strip()
    return Municipio(
        nome=nome,
        nome_normalizado=normalizar_nome_cidade(nome),
        uf=uf,
        uf_nome=uf_nome,
        regiao=regiao,
        capital=capital,
        populacao=populacao,
        codigo_ibge=codigo,
    )


def _bundled_minimo() -> list[Municipio]:
    """Fallback offline: 27 capitais + cidades de config/regioes.py (Baixada/Rio).

    Usado apenas quando a base completa esta ausente/invalida e o escopo
    permite (cidade/cidades/arquivo). Escopos amplos exigem abort.
    """
    municipios: list[Municipio] = []
    vistos: set[str] = set()

    def _add(nome: str, uf: str, capital: bool, codigo: str = ""):
        uf = uf.upper()
        norm = normalizar_nome_cidade(nome)
        chave = f"{norm}|{uf}"
        if chave in vistos:
            return
        vistos.add(chave)
        regiao = _regiao_da_uf(uf)
        municipios.append(Municipio(
            nome=nome,
            nome_normalizado=norm,
            uf=uf,
            uf_nome=UF_NOMES.get(uf, uf),
            regiao=regiao,
            capital=capital,
            populacao=0,
            codigo_ibge=codigo,
        ))

    # 27 capitais
    for sigla, nome in CAPITAIS.items():
        _add(nome, sigla, capital=True)

    # cidades da Baixada e Rio Premium (importacao lazy para evitar custo)
    try:
        from config.regioes import BAIXADA, RIO_PREMIUM
        for regiao_cfg in (BAIXADA, RIO_PREMIUM):
            for entry in getattr(regiao_cfg, "cidades", []):
                nome, uf = _parse_cidade_uf(entry)
                if nome:
                    _add(nome, uf or "RJ", capital=False)
    except Exception:
        pass

    return municipios


def _regiao_da_uf(uf: str) -> str:
    uf = uf.upper()
    for regiao, ufs in REGIOES.items():
        if uf in ufs:
            return regiao
    return ""


# ══════════════════════════════════════════════════════════════════
# CONSULTAS DE BASE
# ══════════════════════════════════════════════════════════════════

def listar_ufs() -> list[str]:
    return list(TODAS_UFS)


def listar_regioes() -> list[str]:
    return list(REGIOES.keys())


def ufs_da_regiao(regiao: str) -> list[str]:
    return list(REGIOES.get(regiao.casefold(), []))


def municipios_uf(uf: str) -> list[Municipio]:
    """Municipios de uma UF. Exige base completa."""
    uf_up = normalizar_uf(uf)
    if uf_up not in UF_NOMES:
        raise ValueError(f"UF invalida: {uf!r}")
    base = _carregar_base_se_disponivel()
    if base is None:
        raise BaseIncompletaError(
            "base de municipios incompleta para escopo UF. "
            "Gere config/data/municipios_br.csv via scripts/gerar_municipios_ibge.py "
            "ou use --permitir-base-incompleta."
        )
    return [m for m in base if m.uf == uf_up]


def municipios_regiao(regiao: str) -> list[Municipio]:
    ufs = ufs_da_regiao(regiao)
    if not ufs:
        raise ValueError(f"regiao invalida: {regiao!r}")
    base = _carregar_base_se_disponivel()
    if base is None:
        raise BaseIncompletaError(
            "base de municipios incompleta para escopo regiao."
        )
    set_ufs = set(ufs)
    return [m for m in base if m.uf in set_ufs]


def municipios_brasil() -> list[Municipio]:
    base = _carregar_base_se_disponivel()
    if base is None:
        raise BaseIncompletaError(
            "base de municipios incompleta para escopo brasil."
        )
    return list(base)


def capital_uf(uf: str) -> Municipio:
    uf_up = normalizar_uf(uf)
    nome_cap = CAPITAIS.get(uf_up)
    if not nome_cap:
        raise ValueError(f"UF invalida: {uf!r}")
    # tenta na base completa
    base = _carregar_base_se_disponivel()
    if base is not None:
        for m in base:
            if m.uf == uf_up and m.capital:
                return m
        # fallback por nome
        for m in base:
            if m.uf == uf_up and m.nome_normalizado == normalizar_nome_cidade(nome_cap):
                return m
    # fallback bundled
    for m in _bundled_minimo():
        if m.uf == uf_up and m.nome_normalizado == normalizar_nome_cidade(nome_cap):
            return m
    raise ValueError(f"capital nao encontrada para UF {uf_up}")


def maiores_municipios(uf: str | None = None, regiao: str | None = None,
                       n: int = 50) -> list[Municipio]:
    """Maiores municipios por populacao (desc); empate por ordem alfabetica.

    Quando todas as populacoes sao 0 (base sem populacao), equivale a
    ordem alfabetica — comportamento seguro e previsivel.
    """
    if uf:
        base = municipios_uf(uf)
    elif regiao:
        base = municipios_regiao(regiao)
    else:
        base = municipios_brasil()
    ordenados = sorted(base, key=lambda m: (-m.populacao, m.nome_normalizado))
    return ordenados[:n] if n > 0 else ordenados


def buscar_municipio(nome_ou_sigla: str, uf: str = "") -> Optional[Municipio]:
    """Busca um municipio por nome (com ou sem UF).

    Aceita 'Nova Iguacu', 'Nova Iguaçu', 'Nova Iguaçu, RJ', 'nova iguaçu, rj'.
    Devolve o Municipio com nome acentuado, ou None se nao achar.
    """
    if not nome_ou_sigla:
        return None
    nome, uf_sigla = _parse_cidade_uf(nome_ou_sigla) if not uf else (
        str(nome_ou_sigla).strip(), normalizar_uf(uf)
    )
    nome_norm = normalizar_nome_cidade(nome)
    uf_up = normalizar_uf(uf_sigla) if uf_sigla else ""

    # tenta base completa; senao bundled
    base = _carregar_base_se_disponivel()
    candidatos = base if base is not None else _bundled_minimo()
    for m in candidatos:
        if m.nome_normalizado == nome_norm and (not uf_up or m.uf == uf_up):
            return m
    return None


# ══════════════════════════════════════════════════════════════════
# ORDENACAO
# ══════════════════════════════════════════════════════════════════

def ordenar(municipios: list[Municipio], ordem: str,
             seed: str | None = None) -> list[Municipio]:
    """Aplica estrategia de ordenacao. Devolve nova lista."""
    ord = (ordem or "fornecida").casefold()
    if ord == "fornecida":
        return list(municipios)
    if ord == "alfabetica":
        return sorted(municipios, key=lambda m: (m.nome_normalizado, m.uf))
    if ord == "capitais":
        return sorted(
            municipios,
            key=lambda m: (0 if m.capital else 1, m.nome_normalizado, m.uf),
        )
    if ord == "maiores":
        # por populacao (desc); no empate, alfabetica por nome (e uf) — quando
        # todas as populacoes sao 0, equivale a alfabetica.
        return sorted(
            municipios,
            key=lambda m: (-m.populacao, m.nome_normalizado, m.uf),
        )
    if ord == "aleatoria":
        rng = random.Random(seed)
        copia = list(municipios)
        rng.shuffle(copia)
        return copia
    raise ValueError(
        f"ordem invalida: {ordem!r}. Opcoes: fornecida|capitais|maiores|alfabetica|aleatoria"
    )


# ══════════════════════════════════════════════════════════════════
# RESOLUCAO DE ESCOPOS (CLI -> lista de Municipio)
# ══════════════════════════════════════════════════════════════════

ESCOPOS_VALIDOS = {"cidade", "cidades", "uf", "ufs", "regiao", "brasil", "arquivo"}
ESCOPOS_AMPLOS = {"uf", "ufs", "regiao", "brasil"}


class BaseIncompletaError(Exception):
    """Levantada quando a base completa e exigida mas esta ausente/invalida."""


def _dedup_municipios(municipios: list[Municipio]) -> list[Municipio]:
    vistos: set[str] = set()
    unicos: list[Municipio] = []
    for m in municipios:
        if m.chave() in vistos:
            continue
        vistos.add(m.chave())
        unicos.append(m)
    return unicos


def resolver_cidades(
    *,
    escopo: str,
    cidade: str | None = None,
    cidades: list[str] | None = None,
    uf: list[str] | None = None,
    ufs: list[str] | None = None,
    regiao: str | None = None,
    cidades_arquivo: str | None = None,
    limite_cidades: int | None = None,
    ordem: str = "fornecida",
    run_id: str | None = None,
    permitir_base_incompleta: bool = False,
) -> list[Municipio]:
    """Resolve um escopo geografico em lista de Municipio.

    Regras de base incompleta:
    - escopos amplos (uf/ufs/regiao/brasil): exigem base completa; se
      incompleta, aborta com erro claro, a menos que permitir_base_incompleta.
    - escopos de cidade (cidade/cidades/arquivo): permitem fallback bundled
      apenas para as cidades informadas que existirem no fallback; se uma
      cidade nao existir, aborta.
    """
    esc = (escopo or "").casefold()
    if esc not in ESCOPOS_VALIDOS:
        raise ValueError(
            f"escopo invalido: {escopo!r}. Opcoes: {sorted(ESCOPOS_VALIDOS)}"
        )

    completa = base_completa()
    usando_bundled = not completa

    if usando_bundled and esc in ESCOPOS_AMPLOS and not permitir_base_incompleta:
        raise BaseIncompletaError(
            f"base de municipios incompleta para escopo '{esc}'. "
            f"Motivo: {status_base().get('motivo') or 'CSV ausente/invalido'}. "
            "Gere config/data/municipios_br.csv via scripts/gerar_municipios_ibge.py "
            "ou use --permitir-base-incompleta para prosseguir sob risco."
        )

    if esc == "brasil":
        if usando_bundled and permitir_base_incompleta:
            municipios = _bundled_minimo()
        else:
            municipios = municipios_brasil()

    elif esc in ("uf", "ufs"):
        siglas = list(ufs or uf or [])
        if not siglas:
            raise ValueError("escopo uf/ufs exige --uf/--ufs")
        municipios: list[Municipio] = []
        for s in siglas:
            s_up = normalizar_uf(s)
            if s_up not in UF_NOMES:
                raise ValueError(f"UF invalida: {s!r}")
            if usando_bundled and permitir_base_incompleta:
                for m in _bundled_minimo():
                    if m.uf == s_up:
                        municipios.append(m)
            else:
                municipios.extend(municipios_uf(s_up))

    elif esc == "regiao":
        if not regiao:
            raise ValueError("escopo regiao exige --regiao")
        ufs_reg = ufs_da_regiao(regiao)
        if not ufs_reg:
            raise ValueError(f"regiao invalida: {regiao!r}")
        if usando_bundled and permitir_base_incompleta:
            set_ufs = set(ufs_reg)
            municipios = [m for m in _bundled_minimo() if m.uf in set_ufs]
        else:
            municipios = municipios_regiao(regiao)

    elif esc == "cidade":
        if not cidade:
            raise ValueError("escopo cidade exige --cidade")
        municipios = _resolver_lista_cidades([cidade], usando_bundled)

    elif esc == "cidades":
        if not cidades:
            raise ValueError("escopo cidades exige --cidades")
        municipios = _resolver_lista_cidades(cidades, usando_bundled)

    elif esc == "arquivo":
        if not cidades_arquivo:
            raise ValueError("escopo arquivo exige --cidades-arquivo")
        entradas = _ler_arquivo_cidades(cidades_arquivo)
        municipios = _resolver_lista_cidades(entradas, usando_bundled)

    else:
        raise ValueError(f"escopo nao tratado: {esc!r}")

    municipios = _dedup_municipios(municipios)

    if ordem and ordem != "fornecida":
        municipios = ordenar(municipios, ordem, seed=run_id)
    elif ordem == "fornecida" or not ordem:
        # fornecida mantem a ordem de resolucao
        municipios = list(municipios)

    if limite_cidades is not None and limite_cidades > 0:
        municipios = municipios[:limite_cidades]

    return municipios


def _resolver_lista_cidades(entradas: list[str], usando_bundled: bool) -> list[Municipio]:
    """Resolve uma lista de strings 'Cidade, UF' em Municipios.

    Se base completa: busca na base. Se bundled: busca no fallback; se uma
    cidade nao for encontrada, aborta com erro claro.
    """
    base = _carregar_base_se_disponivel()
    candidatos_base = base if base is not None else _bundled_minimo()
    # indice por nome_normalizado -> list (para desambiguar por UF)
    por_nome: dict[str, list[Municipio]] = {}
    for m in candidatos_base:
        por_nome.setdefault(m.nome_normalizado, []).append(m)

    resultado: list[Municipio] = []
    for entrada in entradas:
        nome, uf_sigla = _parse_cidade_uf(entrada)
        if not nome:
            continue
        norm = normalizar_nome_cidade(nome)
        uf_up = normalizar_uf(uf_sigla) if uf_sigla else ""
        candidatos = por_nome.get(norm, [])
        if not candidatos:
            raise BaseIncompletaError(
                f"cidade nao encontrada na base: {entrada!r}. "
                "Gere config/data/municipios_br.csv completa ou verifique o nome/UF."
            )
        if uf_up:
            escolhido = next((m for m in candidatos if m.uf == uf_up), None)
            if not escolhido:
                raise BaseIncompletaError(
                    f"cidade {norm!r} nao encontrada na UF {uf_up}. Verifique a UF."
                )
        else:
            # sem UF: se houver mais de uma, escolhe a primeira mas avisa
            escolhido = candidatos[0]
        resultado.append(escolhido)
    return resultado


def _ler_arquivo_cidades(caminho: str) -> list[str]:
    """Le um arquivo de cidades (uma por linha, ignora vazias/comentarios)."""
    p = Path(caminho)
    if not p.exists():
        raise FileNotFoundError(f"arquivo de cidades nao encontrado: {caminho}")
    entradas: list[str] = []
    for linha in p.read_text(encoding="utf-8-sig").splitlines():
        s = linha.strip()
        if not s or s.startswith("#"):
            continue
        entradas.append(s)
    return entradas