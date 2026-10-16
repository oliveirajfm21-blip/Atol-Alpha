"""
Passos da linha do tempo
========================

Cada passo recebe uma imagem NumPy e devolve outra imagem NumPy.
Nenhuma linha de interface (Qt) aqui: o núcleo pode ser testado e reaproveitado sozinho.

Seções:
    1. Classe-base Passo
    2. Funções auxiliares (cinza, limiar IsoData)
    3. Ajustar a imagem: mediana, correção de fundo, contraste
    4. Analisar: separar do fundo, separar encostados, contar

Ordem na linha do tempo (definida na interface):
    Mediana -> Fundo -> Contraste -> Separar do fundo -> Separar encostados -> Contar
"""

import numpy as np
from scipy import ndimage as ndi
from skimage import color, filters, measure, morphology, restoration, segmentation


# =========================================================
# 1. Classe-base Passo
# =========================================================

class Passo:
    nome = "Passo"

    def __init__(self):
        self.ativo = True          # todo passo nasce ligado

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        raise NotImplementedError


# ---------------------------------------------------------
# Em palavras simples (1):
#   Um "passo" é uma etapa de tratamento da imagem, como um filtro.
#   Todo passo tem um nome, uma chave liga/desliga (ativo) e uma única
#   função, aplicar, que recebe a imagem e devolve a imagem tratada.
#   Como todos seguem esse mesmo formato, a interface pode enfileirar
#   quantos quiser, e um add-on futuro só precisa herdar desta classe.
# ---------------------------------------------------------


# =========================================================
# 2. Funções auxiliares
# =========================================================

def para_cinza(imagem: np.ndarray) -> np.ndarray:
    """Colorida (H, W, 3) -> cinza (H, W), em uint8. Cinza passa direto."""
    if imagem.ndim == 2:
        return imagem
    return (color.rgb2gray(imagem) * 255).round().astype(np.uint8)


def limiar_isodata(cinza: np.ndarray, tolerancia: float = 0.5) -> float:
    """IsoData (Ridler e Calvard, 1978): repete 'T = média das duas médias' até T parar de mudar."""
    T = cinza.mean()                                 # 1. chute inicial
    while True:
        fundo = cinza[cinza <= T]                    # 2. divide em dois grupos
        objeto = cinza[cinza > T]
        if fundo.size == 0 or objeto.size == 0:      # imagem de uma cor só
            return T
        novo_T = (fundo.mean() + objeto.mean()) / 2  # 3-4. ponto do meio
        if abs(novo_T - T) < tolerancia:             # 5. parou de mudar?
            return novo_T
        T = novo_T


# ---------------------------------------------------------
# Em palavras simples (2):
#   Quase toda análise trabalha com o brilho, então fotos coloridas
#   viram cinza (0 = preto, 255 = branco). O IsoData escolhe sozinho
#   a "nota de corte" entre fundo e objeto: chuta a média da imagem,
#   divide os pixels em dois grupos, põe o corte no meio das duas
#   médias e repete até o corte parar de andar. Foi escrito à mão
#   para ficar igual ao método "Default" do ImageJ.
# ---------------------------------------------------------


# =========================================================
# 3. Ajustar a imagem
# =========================================================

class FiltroMediana(Passo):
    """Troca cada pixel pela mediana dos vizinhos dentro de um disco de raio r."""
    nome = "Remover ruído (mediana)"

    def __init__(self, raio: int = 2):
        super().__init__()
        self.raio = raio                    # maior que o ruído, menor que o menor objeto
        self._cache = None

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        chave = (hash(imagem.tobytes()), imagem.shape, self.raio)
        if self._cache is not None and self._cache[0] == chave:
            return self._cache[1]
        disco = morphology.disk(self.raio).astype(bool)     # janela redonda, como o Median do Fiji
        if imagem.ndim == 2:
            resultado = ndi.median_filter(imagem, footprint=disco, mode="reflect")
        else:                                                # colorida: cada canal separado
            resultado = np.stack([ndi.median_filter(imagem[..., c], footprint=disco, mode="reflect")
                                  for c in range(imagem.shape[2])], axis=-1)
        self._cache = (chave, resultado)
        return resultado


class CorrigirFundo(Passo):
    """Rolling ball (Sternberg, 1983): estima o fundo F rolando uma bola por baixo do brilho e calcula I - F."""
    nome = "Corrigir iluminação do fundo"

    def __init__(self, raio: int = 40, objetos_claros: bool = True):
        super().__init__()
        self.raio = raio                    # maior que o maior objeto, menor que a mancha de luz
        self.objetos_claros = objetos_claros
        self._cache = None                  # (chave, resultado): a bola é lenta, não refaz à toa

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        cinza = para_cinza(imagem).astype(np.float32)
        chave = (hash(cinza.tobytes()), self.raio, self.objetos_claros)
        if self._cache is not None and self._cache[0] == chave:
            return self._cache[1]

        if not self.objetos_claros:
            cinza = 255 - cinza                # objetos escuros: inverte, corrige, desinverte
        F = restoration.rolling_ball(cinza, radius=self.raio)   # 1. estima o fundo
        corrigida = cinza - F                                   # 2. subtrai
        corrigida = np.clip(corrigida, 0, 255)                  # 3. nada abaixo de 0
        if not self.objetos_claros:
            corrigida = 255 - corrigida
        resultado = corrigida.round().astype(np.uint8)          # 4. volta para uint8

        self._cache = (chave, resultado)
        return resultado


class AjustarContraste(Passo):
    nome = "Ajustar contraste"

    def __init__(self, fator: float = 1.0):
        super().__init__()         # cria o self.ativo da classe-base
        self.fator = fator

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        resultado = imagem.astype(np.float32) * self.fator   # em float: 200 x 2 = 400 não "dá a volta"
        resultado = np.clip(resultado, 0, 255)
        return resultado.astype(np.uint8)


# ---------------------------------------------------------
# Em palavras simples (3):
#   Antes de medir, a foto é limpa.
#   - Mediana: cada pixel vira o valor do meio dos vizinhos. Um ponto
#     de ruído isolado some, e as bordas não borram, porque a mediana
#     nunca inventa um tom que não existia.
#   - Correção de fundo: microscópios iluminam mais um lado que o outro.
#     Uma "bola" grande rola por baixo do relevo de brilho, acompanha só
#     a variação lenta da luz, e essa variação é subtraída.
#   - Contraste: multiplica o brilho por um fator. A conta é feita com
#     casas decimais e travada em 255; em 8 bits, 400 viraria 144.
#   Mediana e fundo guardam o último resultado (cache), porque são os
#   passos lentos e a interface recalcula tudo a cada clique.
# ---------------------------------------------------------


# =========================================================
# 4. Analisar
# =========================================================

class Limiarizar(Passo):
    nome = "Separar do fundo"
    METODOS = ("IsoData", "Otsu")

    def __init__(self, metodo: str = "IsoData", objetos_claros: bool = True):
        super().__init__()
        self.metodo = metodo
        self.objetos_claros = objetos_claros
        self.ultimo_T = None       # guardado para a interface mostrar
        self.fracao_area = None    # % de pixels de objeto (antes de cortes e filtros)
        self.ultima_mascara = None # objeto = True; usada pelo tamanho de grão

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        cinza = para_cinza(imagem)
        if self.metodo == "IsoData":
            T = limiar_isodata(cinza.astype(np.float64))
        else:
            T = filters.threshold_otsu(cinza)
        self.ultimo_T = float(T)
        if self.objetos_claros:
            mascara = cinza > T
        else:
            mascara = cinza <= T
        # Fração de área: todo pixel de objeto conta, inclusive os de objetos na borda
        # (princípio de Delesse: fração de área estima a fração de volume)
        self.fracao_area = 100.0 * mascara.mean()
        self.ultima_mascara = mascara
        return mascara.astype(np.uint8) * 255      # objeto branco, fundo preto


class SepararEncostados(Passo):
    """Watershed na transformada de distância: corta objetos encostados com uma linha de 1 px."""
    nome = "Separar objetos encostados"

    def __init__(self, tolerancia: float = 0.7, preencher_buracos: bool = False):
        super().__init__()
        # 0,7 reproduz o Binary › Watershed do ImageJ (validado nas Blobs: mesmos cortes)
        self.tolerancia = tolerancia
        self.preencher_buracos = preencher_buracos
        self.antes = None          # nº de manchas antes do corte
        self.depois = None         # nº de objetos depois

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        binaria = para_cinza(imagem) > 0                       # espera a saída do Limiarizar
        if self.preencher_buracos:
            binaria = ndi.binary_fill_holes(binaria)
        D = ndi.distance_transform_edt(binaria)                # 1. distância até o fundo
        picos = morphology.h_maxima(D, self.tolerancia)        # 2. só máximos com proeminência >= h
        sementes = measure.label(picos, connectivity=2)        #    cada pico vira uma semente
        rotulos = segmentation.watershed(-D, sementes, mask=binaria, connectivity=2)  # 3. inunda as bacias de -D
        # 4. barragem de 1 px: apaga o pixel que encosta (inclusive na diagonal) num rótulo maior.
        #    Feito à mão porque watershed_line=True com vizinhança-8 leva ~35 s numa imagem pequena.
        vizinho_maior = ndi.maximum_filter(rotulos, size=3) > rotulos
        separada = (rotulos > 0) & ~vizinho_maior
        self.antes = int(measure.label(binaria, connectivity=2).max())
        self.depois = int(measure.label(separada, connectivity=2).max())
        return separada.astype(np.uint8) * 255


class ContarObjetos(Passo):
    """Rotula componentes conexos (o 'balde de tinta') e pinta cada objeto."""
    nome = "Contar objetos"

    def __init__(self, area_minima: int = 0, excluir_borda: bool = False):
        super().__init__()
        self.area_minima = area_minima       # px²; como o "Size" do Fiji
        self.excluir_borda = excluir_borda   # como o "Exclude on edges" do Fiji
        self.contagem = None
        self.rotulos = None        # matriz: 0 = fundo, 1..N = número do objeto

    def aplicar(self, imagem: np.ndarray) -> np.ndarray:
        binaria = para_cinza(imagem) > 0          # espera a saída do Limiarizar
        # connectivity=2 -> vizinhança-8 (diagonais contam), como no Fiji
        rotulos = measure.label(binaria, connectivity=2)

        if self.excluir_borda:
            rotulos = segmentation.clear_border(rotulos)   # zera quem toca a borda

        if self.area_minima > 0:
            areas = np.bincount(rotulos.ravel())   # areas[k] = nº de pixels do objeto k
            pequenos = areas < self.area_minima
            pequenos[0] = False                    # o rótulo 0 é o fundo
            rotulos[pequenos[rotulos]] = 0         # apaga os objetos pequenos

        # renumera 1..N sem buracos e conta
        self.rotulos, _, _ = segmentation.relabel_sequential(rotulos)
        self.contagem = int(self.rotulos.max())
        pintada = color.label2rgb(self.rotulos, bg_label=0)
        return (pintada * 255).astype(np.uint8)


# ---------------------------------------------------------
# Em palavras simples (4):
#   - Separar do fundo: cada pixel acima da nota de corte vira objeto
#     (branco) e o resto vira fundo (preto). A saída é sempre "objeto
#     branco", mesmo quando os objetos da foto são escuros, para os
#     passos seguintes não precisarem saber disso.
#   - Separar encostados: duas moedas que se tocam viram uma mancha só.
#     Medindo a distância de cada pixel até o fundo, o centro de cada
#     moeda vira um morro; enchendo os vales de "água", onde as águas
#     se encontram fica a linha de corte (por isso "watershed",
#     divisor de águas). Morrinhos baixos demais (borda serrilhada)
#     são ignorados pela tolerância, que evita cortar uma moeda ao meio.
#   - Contar: como o balde de tinta do Paint, cada grupo de pixels
#     brancos encostados (diagonal conta, como no Fiji) recebe um número.
#   Os três foram conferidos contra o ImageJ: mesmo limiar, mesma
#   contagem e os mesmos cortes (ver validacao/RELATORIO.md).
# ---------------------------------------------------------
