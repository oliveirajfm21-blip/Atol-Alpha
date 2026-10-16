"""Testes automáticos do Atol: cada número aqui foi validado antes (ImageJ, norma ou conta à mão).

Rodar no terminal, na pasta do Atol:   pytest
Se algum teste falhar depois de uma mudança, a mudança quebrou um resultado que já estava certo.
"""
import csv
from pathlib import Path

import numpy as np
import pytest
from pytest import approx

from atol import nucleo as atol

PASTA = Path(__file__).resolve().parent.parent / "validacao"


def ler_imagej(nome):
    """Lê a tabela exportada do ImageJ (Analyze Particles)."""
    with open(PASTA / nome, newline="") as f:
        return list(csv.DictReader(f))


def medir_pipeline(imagem, claros=True):
    """Separar do fundo (IsoData) -> Contar -> Medir, como o usuário faz no Atol."""
    binaria = atol.Limiarizar("IsoData", objetos_claros=claros).aplicar(imagem)
    contador = atol.ContarObjetos()
    contador.aplicar(binaria)
    return contador, atol.medir_objetos(contador.rotulos, atol.Calibracao())


# ---------------------------------------------------------------- Atol × ImageJ

@pytest.fixture(scope="module")
def blobs():
    return medir_pipeline(atol.carregar_imagem(str(PASTA / "blobs.tif")))


def test_blobs_contagem_igual_imagej(blobs):
    contador, _ = blobs
    assert contador.contagem == len(ler_imagej("blobs_imagej_Default.csv")) == 64


def test_blobs_areas_iguais_imagej(blobs):
    _, medidas = blobs
    areas_atol = sorted(m["area"] for m in medidas)
    areas_ij = sorted(float(l["Area"]) for l in ler_imagej("blobs_imagej_Default.csv"))
    assert areas_atol == areas_ij


def test_blobs_perimetro_igual_imagej(blobs):
    """Mesmo algoritmo de contorno traçado do ImageJ: no máximo 1 canto (0,586 px) de diferença."""
    _, medidas = blobs
    p_atol = sorted(m["perimetro"] for m in medidas)
    p_ij = sorted(float(l["Perim."]) for l in ler_imagej("blobs_imagej_Default.csv"))
    for a, b in zip(p_atol, p_ij):
        assert a == approx(b, abs=0.6)


def test_coins_contagem_igual_imagej():
    contador, _ = medir_pipeline(atol.carregar_imagem(str(PASTA / "coins.tif")))
    assert contador.contagem == len(ler_imagej("coins_imagej_default.csv")) == 96


# ---------------------------------------------------------------- Watershed × ImageJ

def test_watershed_blobs_igual_imagej():
    """Mesma máscara nos dois programas: ImageJ (Binary > Watershed) dá 68 objetos."""
    mascara = atol.carregar_imagem(str(PASTA / "mask_blobs.tif"))
    separador = atol.SepararEncostados(tolerancia=0.7)
    separador.aplicar(mascara)
    assert (separador.antes, separador.depois) == (64, 68)


# ---------------------------------------------------------------- Mediana

def test_mediana_remove_ruido_e_preserva_borda():
    linha = np.array([[10, 10, 10, 200, 200, 200, 200, 200]], dtype=np.uint8)
    imagem = np.repeat(linha, 9, axis=0)                 # 9 linhas iguais: uma borda vertical
    imagem[4, 5] = 255                                   # um único pixel de ruído
    saida = atol.FiltroMediana(raio=1).aplicar(imagem)[4]
    assert saida[5] == 200                               # o 255 isolado sumiu
    assert list(saida[2:4]) == [10, 200]                 # a borda continua no mesmo lugar


# ---------------------------------------------------------------- Tamanho de grão

@pytest.mark.parametrize("periodo, contorno", [(20, 1), (13, 2)])
def test_intercepto_listras(periodo, contorno):
    grao = np.ones((200, 400), dtype=bool)               # tudo grão (branco)
    for k in range(contorno):
        grao[:, periodo - contorno + k::periodo] = False  # contorno preto a cada "periodo" px
    resultado = atol.medir_intercepto(grao, n_linhas=10)
    assert resultado["l_h"] == approx(periodo)


@pytest.mark.parametrize("l_mm, G", [(0.320, 0.0), (0.020, 8.0), (0.010, 10.0)])
def test_numero_G_tabela_astm(l_mm, G):
    assert atol.numero_astm(l_mm) == approx(G, abs=0.05)


def test_graos_laminados_com_correcao_de_fundo():
    """Verdade no desenho limpo: l_h = 62,9 px, l_v = 25,5 px, alongamento 2,47 (tolerância 10%)."""
    imagem = atol.carregar_imagem(str(PASTA / "graos_laminados_sinteticos.tif"))
    imagem = atol.FiltroMediana(2).aplicar(imagem)
    imagem = atol.CorrigirFundo(30, objetos_claros=True).aplicar(imagem)
    limiar = atol.Limiarizar("IsoData")
    limiar.aplicar(imagem)
    r = atol.medir_intercepto(limiar.ultima_mascara, 10)
    assert r["l_h"] == approx(62.9, rel=0.10)
    assert r["l_v"] == approx(25.5, rel=0.10)
    assert r["l_h"] / r["l_v"] == approx(2.47, rel=0.10)


# ---------------------------------------------------------------- Medir e Vickers

def test_vickers():
    # HV 10 com as duas diagonais de 0,293 mm: a conta à mão dá 216,0 HV
    resultado = atol.dureza_vickers(10, 0.293, 0.293)
    assert resultado == approx(216.0, abs=0.1)


@pytest.mark.parametrize("linha, angulo", [
    ((0, 0, 10, 0), 0),          # para a direita
    ((0, 10, 0, 0), 90),         # para cima (y da imagem cresce para baixo)
    ((0, 0, 0, 10), -90),        # vertical para baixo: sem divisão por zero
    ((10, 10, 0, 0), 135),       # quadrante certo graças ao atan2
])
def test_angulo_linha(linha, angulo):
    assert atol.angulo_linha(*linha) == approx(angulo)


def test_angulo_entre_linhas():
    assert atol.angulo_entre(10, 170) == approx(20)
    assert atol.angulo_entre(0, 90) == approx(90)


# ---------------------------------------------------------------- Calibração

def test_calibracao_comprimento_e_area():
    c = atol.Calibracao()
    c.definir(d_px=100, d_real=10, unidade="mm")         # s = 10 px/mm
    assert c.comprimento(50) == approx(5)                 # L / s
    assert c.area(400) == approx(4)                       # A / s²
