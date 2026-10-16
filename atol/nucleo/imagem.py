"""
Imagem
======

Abrir arquivos de imagem e aplicar a linha do tempo de passos.

Seções:
    1. Abrir qualquer formato e devolver uint8 (cinza ou RGB)
    2. Linha do tempo: aplicar, em ordem, só os passos ligados
"""

import numpy as np
from skimage import exposure, io, util


# =========================================================
# 1. Abrir imagem
# =========================================================

def carregar_imagem(caminho: str) -> np.ndarray:
    """Lê um arquivo e devolve uint8 em cinza (H, W) ou colorido (H, W, 3)."""
    imagem = io.imread(caminho)
    imagem = np.squeeze(imagem)                 # tira eixos de tamanho 1
    if imagem.ndim == 4 or (imagem.ndim == 3 and imagem.shape[-1] not in (3, 4)):
        imagem = imagem[0]                      # GIF/TIFF com vários quadros: usa o 1º
    if imagem.ndim == 3 and imagem.shape[-1] == 4:
        imagem = imagem[..., :3]                # descarta a transparência (canal alfa)
    if imagem.dtype == bool:
        imagem = imagem.astype(np.uint8) * 255
    elif imagem.dtype != np.uint8:
        imagem = util.img_as_ubyte(exposure.rescale_intensity(imagem, out_range=(0.0, 1.0)))
    return imagem

# ---------------------------------------------------------
# Em palavras simples (1):
#   Microscópios e câmeras salvam imagens de jeitos diferentes: 8 ou 16
#   bits, com transparência, com vários quadros num TIFF, preto e branco
#   puro. Esta função traduz tudo para um formato só (0 a 255, cinza ou
#   colorido), para o resto do Atol não precisar se preocupar com isso.
# ---------------------------------------------------------


# =========================================================
# 2. Linha do tempo
# =========================================================

def aplicar_linha_do_tempo(original: np.ndarray, passos: list) -> np.ndarray:
    imagem = original
    for passo in passos:
        if passo.ativo:
            imagem = passo.aplicar(imagem)
    return imagem

# ---------------------------------------------------------
# Em palavras simples (2):
#   A imagem original nunca é alterada. A cada mudança na interface, a
#   linha do tempo recomeça da original e aplica, em ordem, só os passos
#   ligados. Assim, desligar um passo não perde nada: é só pular ele.
# ---------------------------------------------------------
