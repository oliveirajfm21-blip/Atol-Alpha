"""
Medidas
=======

Números tirados de uma imagem já separada (objeto branco, fundo preto) ou de linhas
desenhadas pelo usuário. Tudo em NumPy, sem interface.

Seções:
    1. Medidas por objeto: área, perímetro (igual ao ImageJ), diâmetro, circularidade
    2. Distância, ângulo e dureza Vickers
    3. Tamanho de grão pelo método do intercepto (ASTM E112)

Validação: tests/test_atol.py e validacao/RELATORIO.md.
"""

import numpy as np
from skimage import measure


# =========================================================
# 1. Medidas por objeto
# =========================================================

def contorno_externo(mascara):
    """Vértices (x, y) do contorno externo, andando pelas bordas dos pixels, objeto à direita."""
    m = np.pad(mascara.astype(bool), 1)
    saidas = {}
    linhas, colunas = np.nonzero(m)
    for r, c in zip(linhas, colunas):
        if not m[r-1, c]: saidas.setdefault((c, r), []).append((c+1, r))         # topo
        if not m[r, c+1]: saidas.setdefault((c+1, r), []).append((c+1, r+1))     # direita
        if not m[r+1, c]: saidas.setdefault((c+1, r+1), []).append((c, r+1))     # baixo
        if not m[r, c-1]: saidas.setdefault((c, r+1), []).append((c, r))         # esquerda
    r0, c0 = linhas[0], colunas[0]           # primeiro pixel na varredura (como o ImageJ)
    inicio = (c0, r0); atual = inicio; direcao = (1, 0)
    pontos = []
    while True:
        opcoes = saidas[atual]
        if len(opcoes) == 1:
            prox = opcoes[0]
        else:   # canto diagonal: vira à esquerda primeiro, como o rastreador do ImageJ
            dx, dy = direcao
            pref = [(dy, -dx), (dx, dy), (-dy, dx)]
            prox = next(p for d in pref for p in opcoes if (p[0]-atual[0], p[1]-atual[1]) == d)
        opcoes.remove(prox)
        nova = (prox[0]-atual[0], prox[1]-atual[1])
        if nova != direcao or not pontos:
            pontos.append(atual)
        direcao, atual = nova, prox
        if atual == inicio and not saidas.get(inicio):
            break
    # o ponto de partida só é vértice se a direção muda nele
    if len(pontos) > 2:
        a, b, c = pontos[-1], pontos[0], pontos[1]
        d1 = (np.sign(b[0]-a[0]), np.sign(b[1]-a[1])); d2 = (np.sign(c[0]-b[0]), np.sign(c[1]-b[1]))
        if d1 == d2:
            pontos = pontos[1:]
    return [(x-1, y-1) for x, y in pontos]


def perimetro_tracado(pts):
    """Fórmula do ImageJ (PolygonRoi.getTracedPerimeter): soma das arestas menos (2 − √2) por canto."""
    n = len(pts); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    dx1, dy1 = xs[0]-xs[n-1], ys[0]-ys[n-1]
    side1 = abs(dx1)+abs(dy1); corner = False; sdx = sdy = 0; nc = 0
    for i in range(n):
        j = (i+1) % n
        dx2, dy2 = xs[j]-xs[i], ys[j]-ys[i]
        sdx += abs(dx1); sdy += abs(dy1)
        side2 = abs(dx2)+abs(dy2)
        if side1 > 1 or not corner:
            corner = True; nc += 1
        else:
            corner = False
        dx1, dy1, side1 = dx2, dy2, side2
    return sdx + sdy - nc*(2.0-np.sqrt(2.0))


def medir_objetos(rotulos: np.ndarray, calibracao) -> list:
    """Uma linha por objeto, já nas unidades da calibração."""
    linhas = []
    for regiao in measure.regionprops(rotulos):
        A_px = float(regiao.area)                 # buracos internos não contam (padrão do ImageJ)
        # perímetro da borda de fora, com o mesmo algoritmo do ImageJ: traça o contorno pelas
        # bordas dos pixels e desconta (2 − √2) por canto, para não somar a "escada"
        P_px = perimetro_tracado(contorno_externo(regiao.image_filled))
        d_px = 2 * (A_px / np.pi) ** 0.5          # diâmetro equivalente: d = 2·√(A/π)
        C = 4 * np.pi * A_px / P_px ** 2 if P_px > 0 else 0.0   # adimensional: não depende da escala
        y, x = regiao.centroid                    # regionprops devolve (linha, coluna)
        linhas.append({
            "rotulo": regiao.label,
            "_cx": x + 0.5, "_cy": y + 0.5,          # centro em pixels (para o visor)
            "area": calibracao.area(A_px),
            "perimetro": calibracao.comprimento(P_px),
            "diametro": calibracao.comprimento(d_px),
            "circularidade": min(C, 1.0),          # como o ImageJ: arredondamento de pixel pode passar de 1
            "x": calibracao.comprimento(x + 0.5),  # +0,5: centro do pixel
            "y": calibracao.comprimento(y + 0.5),
        })
    return linhas


def classes_sturges(n: int) -> int:
    """Regra de Sturges: k = ⌈log₂ n⌉ + 1 classes no histograma."""
    return int(np.ceil(np.log2(n))) + 1 if n > 1 else 1


# ---------------------------------------------------------
# Em palavras simples (1):
#   Para cada objeto contado, o Atol mede:
#   - área: quantos pixels ele tem;
#   - perímetro: o comprimento da borda de fora. Somar as arestas dos
#     pixels dá uma "escada" cerca de 27% maior que a borda real, então
#     cada canto desconta um pedaço, exatamente como o ImageJ faz. Esse
#     detalhe foi o que fez o Atol bater com o ImageJ nos perímetros;
#   - diâmetro equivalente: o diâmetro do círculo de mesma área;
#   - circularidade: 1 para um círculo perfeito, perto de 0 para uma
#     forma alongada ou recortada.
#   Tudo sai já em mm ou µm se a escala estiver calibrada.
# ---------------------------------------------------------


# =========================================================
# 2. Distância, ângulo e dureza Vickers
# =========================================================

def comprimento_px(x1, y1, x2, y2) -> float:
    """Pitágoras: comprimento da linha em pixels."""
    return float(np.hypot(x2 - x1, y2 - y1))


def angulo_linha(x1, y1, x2, y2) -> float:
    """Ângulo com a horizontal, em graus, de -180 a 180, anti-horário.
    atan2 recebe Δy e Δx separados: nunca divide por zero e sabe o quadrante.
    O sinal de menos em Δy existe porque, na imagem, o eixo y cresce para baixo."""
    return float(np.degrees(np.arctan2(-(y2 - y1), x2 - x1))) + 0.0     # + 0.0 transforma -0,0 em 0,0


def angulo_entre(a: float, b: float) -> float:
    """Menor ângulo entre duas linhas (sem sentido), de 0 a 90 graus."""
    d = abs(a - b) % 180
    return min(d, 180 - d)


def dureza_vickers(F_kgf: float, d1_mm: float, d2_mm: float) -> float:
    """HV = 2 F sen(136°/2) / d² ≈ 1,8544 F / d², com d = média das diagonais (mm) e F em kgf."""
    d = (d1_mm + d2_mm) / 2
    return 2 * F_kgf * np.sin(np.radians(136 / 2)) / d ** 2


# ---------------------------------------------------------
# Em palavras simples (2):
#   Comprimento é Pitágoras entre os dois cliques. O ângulo usaria a
#   tangente (Δy/Δx), mas dividir quebraria numa linha vertical (Δx = 0)
#   e confundiria "para a direita e para cima" com "para a esquerda e
#   para baixo". O atan2 recebe os dois separados e resolve as duas
#   coisas. No ensaio Vickers, uma pirâmide de diamante deixa uma marca
#   no metal: quanto maior a marca, mais mole o metal. A dureza é a
#   força dividida pela área da marca; como a diagonal aparece ao
#   quadrado, errar 5% na diagonal dá cerca de 10% de erro na dureza.
# ---------------------------------------------------------


# =========================================================
# 3. Tamanho de grão: método do intercepto (ASTM E112)
# =========================================================

PARA_MM = {"nm": 1e-6, "µm": 1e-3, "mm": 1.0, "cm": 10.0, "m": 1000.0}


def contornos_na_linha(grao: np.ndarray) -> list:
    """Numa linha de pixels (True = grão), acha cada trecho de contorno (False) que tem grão
    dos dois lados. Cada trecho é uma interseção da linha de teste com um contorno.
    Devolve a posição do meio de cada trecho."""
    g = grao.astype(np.int8)
    muda = np.diff(g)                       # -1: grão -> contorno ; +1: contorno -> grão
    descidas = np.flatnonzero(muda == -1) + 1
    subidas = np.flatnonzero(muda == 1) + 1
    pontos = []
    for ini in descidas:                    # começo de um trecho de contorno
        fim = subidas[subidas > ini]
        if fim.size:                        # só conta se voltar a ser grão (não na ponta da linha)
            pontos.append((ini + fim[0] - 1) / 2)
    return pontos


def medir_intercepto(grao: np.ndarray, n_linhas: int = 10) -> dict:
    """Lança n linhas horizontais e n verticais, conta as interseções com os contornos e calcula
    o intercepto médio  l = L / P  em cada direção (em pixels).
    Para não errar nas pontas (grão cortado pela borda), cada linha só vale entre o primeiro e o
    último contorno cruzado: L = x_último - x_primeiro e P = nº de cruzamentos - 1 (grãos inteiros)."""
    altura, largura = grao.shape
    res = {"linhas": [], "pontos": []}
    for direcao in ("h", "v"):
        tamanho = altura if direcao == "h" else largura          # distribui as linhas na outra direção
        posicoes = np.linspace(0, tamanho, n_linhas + 2)[1:-1].round().astype(int)
        L, P, total = 0.0, 0, 0
        for pos in posicoes:
            perfil = grao[pos, :] if direcao == "h" else grao[:, pos]
            cruzes = contornos_na_linha(perfil)
            total += len(cruzes)
            if len(cruzes) >= 2:
                L += cruzes[-1] - cruzes[0]
                P += len(cruzes) - 1
            if direcao == "h":
                res["linhas"].append((0, pos + 0.5, largura, pos + 0.5))
                res["pontos"] += [(x + 0.5, pos + 0.5) for x in cruzes]
            else:
                res["linhas"].append((pos + 0.5, 0, pos + 0.5, altura))
                res["pontos"] += [(pos + 0.5, y + 0.5) for y in cruzes]
        res["L_" + direcao], res["P_" + direcao], res["N_" + direcao] = L, P, total
        res["l_" + direcao] = L / P if P else None
    P = res["P_h"] + res["P_v"]
    res["l"] = (res["L_h"] + res["L_v"]) / P if P else None
    return res


def numero_astm(l_mm: float) -> float:
    """Número de tamanho de grão ASTM E112 a partir do intercepto médio em mm."""
    return -6.643856 * np.log10(l_mm) - 3.288


# ---------------------------------------------------------
# Em palavras simples (3):
#   Num metal polido, os grãos são áreas claras separadas por linhas
#   escuras finas (os contornos). O Atol traça linhas retas sobre a
#   imagem e conta quantas vezes cada uma atravessa um contorno. O
#   comprimento da linha dividido pelo número de grãos atravessados é o
#   "tamanho médio" do grão, e a norma ASTM E112 converte esse valor no
#   número G (G maior = grão mais fino). Medindo na horizontal e na
#   vertical separadamente, dá para ver se os grãos foram esticados,
#   como acontece num material laminado. Um contorno com uma falha só
#   atrapalha as poucas linhas que passam pela falha, por isso o método
#   é mais robusto que tentar contar os grãos um por um.
# ---------------------------------------------------------
