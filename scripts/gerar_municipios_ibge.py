"""
Gera config/data/municipios_br.csv a partir da API publica do IBGE.

Runtime NAO depende de rede: este script eh executado uma vez (ou sob
demanda) para regenerar a base local. O territorio.py so le o CSV.

Colunas do CSV:
    codigo_ibge,nome,uf,uf_nome,regiao,capital,populacao

Observacoes:
- codigo_ibge: codigo IBGE de 7 digitos (zero-padded).
- regiao: normalizada para norte|nordeste|centro_oeste|sudeste|sul.
- capital: True para a capital do estado (tabela fixa de 27 capitais).
- populacao: best-effort. Nesta versao eh 0 (a API de localidades nao
  entrega populacao). A ordem "maiores" cai em alfabetica quando todas as
  populacoes sao 0. Para popular, atualize a base com uma fonte de
  estimativas populacionais do IBGE em outro momento.

Gera tambem config/data/municipios_br.meta.json com:
    fonte, data_geracao, quantidade_municipios, versao_base, colunas,
    checksum_sha256 (SHA-256 do conteudo do CSV, obrigatorio).

Uso:
    py -3.12 scripts/gerar_municipios_ibge.py
"""

import csv
import gzip
import hashlib
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

# 27 capitais (sigla -> nome exato conforme IBGE)
CAPITAIS = {
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

_REGIAO_MAP = {
    "Norte": "norte",
    "Nordeste": "nordeste",
    "Centro-Oeste": "centro_oeste",
    "Sudeste": "sudeste",
    "Sul": "sul",
}

COLUNAS = ["codigo_ibge", "nome", "uf", "uf_nome", "regiao", "capital", "populacao"]
API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


def _fetch_municipios() -> list[dict]:
    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "mapear-comercios/1.0", "Accept-Encoding": "gzip"},
    )
    raw = urllib.request.urlopen(req, timeout=120).read()
    try:
        text = gzip.decompress(raw).decode("utf-8")
    except Exception:
        text = raw.decode("utf-8")
    return json.loads(text)


def _codigo_ibge(id_ibge) -> str:
    """Converte id numerico em codigo de 7 digitos zero-padded."""
    return str(id_ibge).zfill(7)


def _extrair_uf(m: dict):
    """Extrai o dict da UF de qualquer dos caminhos disponiveis no IBGE.

    Brasilia (DF) e alguns municipios nao tem microrregiao/mesorregiao,
    entao tenta regiao-imediata -> regiao-intermediaria -> UF.
    """
    micro = m.get("microrregiao")
    if micro:
        uf = micro.get("mesorregiao", {}).get("UF")
        if uf:
            return uf
    imediata = m.get("regiao-imediata")
    if imediata:
        inter = imediata.get("regiao-intermediaria")
        if inter:
            uf = inter.get("UF")
            if uf:
                return uf
    return None


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent / "config" / "data"
    base_dir.mkdir(parents=True, exist_ok=True)
    csv_path = base_dir / "municipios_br.csv"
    meta_path = base_dir / "municipios_br.meta.json"

    print(f"[gerar] baixando municipios do IBGE: {API_URL}")
    dados = _fetch_municipios()
    print(f"[gerar] {len(dados)} municipios recebidos")

    # dedup defensiva por codigo_ibge
    vistos = set()
    linhas = []
    for m in dados:
        uf = _extrair_uf(m)
        if not uf:
            # sem UF identificavel: pula (nao deve ocorrer, mas defensivo)
            continue
        sigla = uf["sigla"]
        uf_nome = uf["nome"]
        regiao_nome = uf["regiao"]["nome"]
        regiao = _REGIAO_MAP.get(regiao_nome, regiao_nome.casefold())
        codigo = _codigo_ibge(m["id"])
        if codigo in vistos:
            continue
        vistos.add(codigo)
        nome = m["nome"].strip()
        capital = bool(CAPITAIS.get(sigla) == nome)
        linhas.append({
            "codigo_ibge": codigo,
            "nome": nome,
            "uf": sigla,
            "uf_nome": uf_nome,
            "regiao": regiao,
            "capital": "true" if capital else "false",
            "populacao": "0",
        })

    # ordena por uf, depois nome (alfabetica) para estabilidade
    linhas.sort(key=lambda r: (r["uf"], r["nome"]))

    # escreve CSV em UTF-8 (sem BOM), em MODO BINARIO para preservar \n e
    # garantir que o SHA-256 computado aqui confira com o lido do disco.
    # (write_text no Windows converte \n -> \r\n e quebraria o checksum.)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUNAS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(linhas)
    conteudo = buf.getvalue()
    csv_path.write_bytes(conteudo.encode("utf-8"))

    checksum = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()

    meta = {
        "fonte": "IBGE - API de Localidades (https://servicodados.ibge.gov.br/api/v1/localidades/municipios)",
        "data_geracao": date.today().isoformat(),
        "quantidade_municipios": len(linhas),
        "versao_base": 1,
        "colunas": COLUNAS,
        "encoding": "utf-8",
        "checksum_sha256": checksum,
        "observacao_populacao": (
            "populacao = 0 nesta versao (a API de localidades nao entrega populacao). "
            "A ordem 'maiores' cai em alfabetica quando todas as populacoes sao 0."
        ),
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[gerar] CSV:     {csv_path}")
    print(f"[gerar] Meta:   {meta_path}")
    print(f"[gerar] SHA-256: {checksum}")
    print(f"[gerar] total:  {len(linhas)} municipios")
    return 0


if __name__ == "__main__":
    sys.exit(main())