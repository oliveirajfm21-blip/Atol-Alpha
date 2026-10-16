"""
Gráficos no padrão de artigo
============================

Histograma do diâmetro equivalente com matplotlib + SciencePlots (estilo "science").
Não depende de Qt: a mesma figura aparece na janela de Resultados e é salva para o artigo.

Seções:
    1. Estilo (SciencePlots, vírgula decimal)
    2. Histograma
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from ..nucleo.medidas import classes_sturges


# =========================================================
# 1. Estilo
# =========================================================

try:
    import scienceplots  # noqa: F401  (registra os estilos "science", "no-latex"...)
    ESTILO_GRAFICO = ["science", "no-latex"]      # no-latex: não exige LaTeX instalado no computador
except ImportError:                                # sem o pacote: gráfico simples, mas o Atol funciona
    ESTILO_GRAFICO = ["default"]

VIRGULA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))   # 1,5 em vez de 1.5

# ---------------------------------------------------------
# Em palavras simples (1):
#   O professor pediu gráficos no padrão de artigo. O SciencePlots ajusta
#   fonte, marcas dos eixos e cores como nas revistas. O modo "no-latex"
#   evita exigir LaTeX instalado no computador dos alunos. Se o pacote
#   não estiver instalado, o Atol continua funcionando com o estilo comum.
# ---------------------------------------------------------


# =========================================================
# 2. Histograma
# =========================================================


def figura_histograma(valores, unidade: str, tamanho=(3.5, 2.4), foco: int = -1):
    """Histograma (classes de Sturges) no estilo SciencePlots. Devolve (figura, barras, bordas)."""
    with plt.style.context(ESTILO_GRAFICO):
        fig = Figure(figsize=tamanho)
        ax = fig.add_subplot()
        valores = np.asarray(valores, dtype=float)
        if valores.size == 0:
            ax.text(0.5, 0.5, "Sem objetos", ha="center", va="center", transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
            return fig, [], np.array([])
        contagens, bordas = np.histogram(valores, bins=classes_sturges(valores.size))
        barras = ax.bar(bordas[:-1], contagens, width=np.diff(bordas), align="edge",
                        color="0.75", edgecolor="black", linewidth=0.6)
        if 0 <= foco < len(barras):
            barras[foco].set_facecolor("0.45")
        media = valores.mean()
        ax.axvline(media, color="black", linestyle="--", linewidth=0.8)
        ax.annotate(f"média = {media:.1f}".replace(".", ","), (media, contagens.max()),
                    xytext=(4, 0), textcoords="offset points", fontsize=7, va="top")
        ax.set_xlabel(f"Diâmetro equivalente ({unidade})")
        ax.set_ylabel("Número de objetos")
        ax.set_xlim(bordas[0], bordas[-1])
        ax.set_ylim(0, contagens.max() * 1.12)
        ax.xaxis.set_major_formatter(VIRGULA)
        ax.yaxis.get_major_locator().set_params(integer=True)
        fig.tight_layout()
        return fig, barras, bordas

# ---------------------------------------------------------
# Em palavras simples (2):
#   O histograma mostra quantos objetos caem em cada faixa de tamanho. O
#   número de faixas segue a regra de Sturges (k = ⌈log₂ n⌉ + 1): poucas
#   faixas escondem detalhes, faixas demais viram ruído. A linha tracejada
#   marca a média. Para o artigo, a figura sai com 8,9 cm de largura, o
#   tamanho de uma coluna de revista.
# ---------------------------------------------------------
