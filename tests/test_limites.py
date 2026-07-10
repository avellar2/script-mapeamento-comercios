"""
Testes de config/limites.py (limites por leads unicos aceitos, ignorada_limite).

Roda de duas formas:
    py -3.12 tests/test_limites.py
    pytest tests/test_limites.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.avgestao import get_grupo
from config.territorios import Municipio, normalizar_nome_cidade
from config.fila import (
    gerar_fila,
    STATUS_PENDENTE,
    STATUS_EM_ANDAMENTO,
    STATUS_IGNORADA_LIMITE,
)
from config.limites import (
    ContadoresLimites,
    Limites,
    MotorLimites,
    limite_total_atingido,
    limite_cidade_atingido,
    limite_subnicho_atingido,
    recontar_resumo_limites,
)


def _mun(nome, uf, regiao="sudeste"):
    return Municipio(
        nome=nome,
        nome_normalizado=normalizar_nome_cidade(nome),
        uf=uf,
        uf_nome=uf,
        regiao=regiao,
        capital=False,
        populacao=0,
        codigo_ibge="0000000",
    )


CIDADES = [_mun("Duque de Caxias", "RJ"), _mun("Nova Iguacu", "RJ")]


def _fila():
    # 1 grupo (6 subnichos) x 2 cidades = 12 itens
    return gerar_fila([get_grupo("assistencias")], CIDADES, max_por_consulta=20)


# ── contadores: contam leads unicos aceitos ─────────────────────────

def test_contadores_registram_aceitos():
    cont = ContadoresLimites()
    for _ in range(5):
        cont.registrar_aceito("Duque de Caxias", "celular")
    assert cont.unicos_por_cidade["Duque de Caxias"] == 5
    assert cont.unicos_por_subnicho["celular"] == 5
    assert cont.unicos_total == 5


def test_contadores_reset():
    cont = ContadoresLimites()
    cont.registrar_aceito("X", "y")
    cont.reset()
    assert cont.unicos_total == 0
    assert cont.unicos_por_cidade == {}


# ── limites por subnicho ─────────────────────────────────────────────

def test_limite_subnicho_atingido():
    cont = ContadoresLimites()
    lim = Limites(max_por_subnicho=5)
    for _ in range(5):
        cont.registrar_aceito("Cidade", "celular")
    assert limite_subnicho_atingido(cont, lim, "celular")
    assert not limite_subnicho_atingido(cont, lim, "computadores")


def test_motor_limite_subnicho_marca_ignorada_nao_erro():
    fila = _fila()
    motor = MotorLimites(limites=Limites(max_por_subnicho=5),
                         contadores=ContadoresLimites())
    # 5 leads aceitos do subnicho celular
    for _ in range(5):
        motor.contadores.registrar_aceito("Duque de Caxias", "celular")
    # 6a tarefa do mesmo subnicho -> nao despacha
    item_cel = next(i for i in fila if i.subnicho == "celular")
    pode, status = motor.pode_despachar(item_cel)
    assert pode is False
    assert status == STATUS_IGNORADA_LIMITE
    # outro subnicho ainda pode
    item_outro = next(i for i in fila if i.subnicho != "celular")
    pode2, status2 = motor.pode_despachar(item_outro)
    assert pode2 is True


# ── limites por cidade ───────────────────────────────────────────────

def test_motor_limite_cidade_marca_ignorada():
    fila = _fila()
    motor = MotorLimites(limites=Limites(max_por_cidade=10),
                         contadores=ContadoresLimites())
    for _ in range(10):
        motor.contadores.registrar_aceito("Duque de Caxias", "celular")
    # proxima tarefa da mesma cidade -> ignorada_limite
    item_mesma = next(i for i in fila if i.cidade == "Duque de Caxias")
    pode, status = motor.pode_despachar(item_mesma)
    assert pode is False
    assert status == STATUS_IGNORADA_LIMITE
    # cidade diferente pode
    item_outra = next(i for i in fila if i.cidade != "Duque de Caxias")
    assert motor.pode_despachar(item_outra)[0] is True


# ── max_total ─────────────────────────────────────────────────────────

def test_motor_max_total_atingido_encerra():
    fila = _fila()
    motor = MotorLimites(limites=Limites(max_total=10),
                         contadores=ContadoresLimites())
    for _ in range(10):
        motor.contadores.registrar_aceito("Duque de Caxias", "celular")
    # qualquer tarefa -> nao despacha e total_atingido fica True
    pode, status = motor.pode_despachar(fila[0])
    assert pode is False
    assert status == STATUS_IGNORADA_LIMITE
    assert motor.total_atingido is True
    # chamadas seguintes continuam bloqueando
    pode2, _ = motor.pode_despachar(fila[1])
    assert pode2 is False


def test_max_total_zero_ou_none_nao_limita():
    fila = _fila()
    motor = MotorLimites(limites=Limites(max_total=None),
                         contadores=ContadoresLimites())
    for _ in range(1000):
        motor.contadores.registrar_aceito("X", "y")
    assert motor.pode_despachar(fila[0])[0] is True


# ── marcar restantes: fila nao truncada ──────────────────────────────

def test_marcar_ignoradas_a_partir_de_nao_trunca_fila():
    fila = _fila()
    tamanho = len(fila)
    motor = MotorLimites(limites=Limites(max_total=3),
                         contadores=ContadoresLimites())
    for _ in range(3):
        motor.contadores.registrar_aceito("X", "y")
    n = motor.marcar_ignoradas_a_partir_de(fila, 2)
    # a fila continua do mesmo tamanho (so status mudou)
    assert len(fila) == tamanho
    assert n > 0
    # itens marcados a partir do indice 2 ficam ignorada_limite
    for item in fila[2:]:
        assert item.status == STATUS_IGNORADA_LIMITE
    # itens antes do indice nao foram tocados
    for item in fila[:2]:
        assert item.status == STATUS_PENDENTE


def test_marcar_ignoradas_preserva_concluida():
    fila = _fila()
    fila[0].status = "concluida"
    fila[1].status = "erro"
    motor = MotorLimites(limites=Limites(max_total=1),
                         contadores=ContadoresLimites())
    motor.contadores.registrar_aceito("X", "y")
    motor.marcar_ignoradas_a_partir_de(fila, 0)
    # concluida e erro nao viram ignorada_limite
    assert fila[0].status == "concluida"
    assert fila[1].status == "erro"
    # pendentes viram ignorada_limite
    assert fila[2].status == STATUS_IGNORADA_LIMITE


# ── ignorada_limite nao e erro nem interrompida ──────────────────────

def test_ignorada_limite_status_distinto_de_erro_interrompida():
    fila = _fila()
    motor = MotorLimites(limites=Limites(max_por_subnicho=1),
                         contadores=ContadoresLimites())
    motor.contadores.registrar_aceito("Duque de Caxias", "celular")
    item = next(i for i in fila if i.subnicho == "celular")
    _, status = motor.pode_despachar(item)
    assert status == STATUS_IGNORADA_LIMITE
    assert status != "erro"
    assert status != "interrompida"


# ── limites inativos ─────────────────────────────────────────────────

def test_limites_inativos_deixam_despachar():
    fila = _fila()
    motor = MotorLimites(limites=Limites(), contadores=ContadoresLimites())
    assert motor.limites.ativos() is False
    for item in fila:
        pode, _ = motor.pode_despachar(item)
        assert pode is True


# ── recontar resumo ──────────────────────────────────────────────────

def test_recontar_resumo_limites_status_e_contadores():
    fila = _fila()
    fila[0].status = "concluida"
    fila[1].status = STATUS_IGNORADA_LIMITE
    cont = ContadoresLimites()
    cont.registrar_aceito("Duque de Caxias", "celular")
    resumo = recontar_resumo_limites(fila, cont)
    assert resumo["concluidas"] == 1
    assert resumo["ignoradas_limite"] == 1
    assert resumo["unicos_total"] == 1
    assert resumo["unicos_por_subnicho"]["celular"] == 1


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