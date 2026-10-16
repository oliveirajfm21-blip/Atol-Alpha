"""
Janela de Resultados
====================

Janela separada com os números da análise.

Seções:
    1. Histograma (matplotlib + SciencePlots embutido no Qt)
    2. Janela de Resultados: cartões, histograma, tabela e exportar
"""
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6 import QtCore, QtGui, QtWidgets

from ..nucleo import classes_sturges
from ..saida.graficos import figura_histograma


# =========================================================
# 1. Histograma
# =========================================================

class Histograma(QtWidgets.QFrame):
    """Cartão com o histograma do diâmetro (SciencePlots), hover e botão de salvar para artigo."""

    def __init__(self):
        super().__init__()
        self.setObjectName("cartao")
        self.valores, self.unidade = np.array([]), "px"
        self.contagens, self.bordas, self.foco = np.array([]), np.array([]), -1

        titulo = QtWidgets.QLabel("DISTRIBUIÇÃO DO DIÂMETRO")
        titulo.setObjectName("cartaoRotulo")
        self.info = QtWidgets.QLabel("")
        self.info.setObjectName("cartaoDetalhe")
        self.botao_salvar = QtWidgets.QPushButton("Salvar gráfico…")
        self.botao_salvar.setObjectName("salvarGrafico")
        self.botao_salvar.setToolTip("PNG (600 dpi), PDF ou SVG, no tamanho de uma coluna de artigo (8,9 cm)")
        self.botao_salvar.clicked.connect(self.salvar)
        topo = QtWidgets.QHBoxLayout()
        topo.addWidget(titulo)
        topo.addStretch()
        topo.addWidget(self.info)
        topo.addWidget(self.botao_salvar)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(3.5, 2.4)))
        self.canvas.setMinimumHeight(220)
        self.canvas.mpl_connect("motion_notify_event", self._ao_mover)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(topo)
        layout.addWidget(self.canvas)

    def mostrar(self, valores, unidade: str):
        self.valores, self.unidade, self.foco = np.asarray(valores, dtype=float), unidade, -1
        if self.valores.size:
            self.contagens, self.bordas = np.histogram(self.valores, bins=classes_sturges(self.valores.size))
            self.info.setText(f"n = {self.valores.size} · {len(self.contagens)} classes (Sturges)")
        else:
            self.contagens, self.bordas = np.array([]), np.array([])
            self.info.setText("")
        self.botao_salvar.setEnabled(self.valores.size > 0)
        self._desenhar()

    def _desenhar(self):
        largura = max(self.canvas.width(), 200) / self.canvas.figure.dpi
        altura = max(self.canvas.height(), 150) / self.canvas.figure.dpi
        fig, _, _ = figura_histograma(self.valores, self.unidade, (largura, altura), self.foco)
        fig.set_canvas(self.canvas)
        self.canvas.figure = fig
        self.canvas.draw_idle()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        QtCore.QTimer.singleShot(0, self._desenhar)       # refaz o layout do gráfico no novo tamanho

    def _ao_mover(self, evento):
        foco = -1
        if evento.inaxes is not None and self.bordas.size and evento.xdata is not None:
            foco = int(np.searchsorted(self.bordas, evento.xdata, side="right") - 1)
            foco = foco if 0 <= foco < len(self.contagens) else -1
        if foco == self.foco:
            return
        self.foco = foco
        self._desenhar()
        if foco >= 0:
            a, b = self.bordas[foco], self.bordas[foco + 1]
            c = int(self.contagens[foco])
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(),
                f"{a:.1f} – {b:.1f} {self.unidade}".replace(".", ",") + f"\n{c} objeto{'s' if c != 1 else ''}",
                self.canvas)
        else:
            QtWidgets.QToolTip.hideText()

    def salvar(self):
        caminho, filtro = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salvar gráfico", "histograma_diametro.png",
            "Imagem PNG (*.png);;PDF vetorial (*.pdf);;SVG vetorial (*.svg)")
        if not caminho:
            return
        fig, _, _ = figura_histograma(self.valores, self.unidade)      # 3,5 pol = 1 coluna de artigo
        fig.savefig(caminho, dpi=600)


# ---------------------------------------------------------
# Em palavras simples (1):
#   O mesmo gráfico do artigo (figura_histograma) é desenhado dentro da
#   janela. Passar o mouse numa barra mostra a faixa e quantos objetos
#   caem nela; "Salvar gráfico" gera a figura em PNG, PDF ou SVG.
# ---------------------------------------------------------


# =========================================================
# 2. Janela de Resultados
# =========================================================

class JanelaResultados(QtWidgets.QWidget):
    """Tabela de resultados numa janela própria, ligada à janela principal."""
    fechada = QtCore.Signal()
    linhaEscolhida = QtCore.Signal(int)           # índice da linha (-1 = nenhuma)

    COLUNAS = [("#", "rotulo", None), ("Área", "area", 2), ("Perímetro", "perimetro", 1),
               ("Diâmetro", "diametro", 1), ("Circularidade", "circularidade", 3), ("X", "x", 1), ("Y", "y", 1)]

    def __init__(self, principal):
        # pai = janela principal + flag Window: janela separada, mas fecha junto e fica à frente dela
        super().__init__(principal, QtCore.Qt.WindowType.Window)
        self.principal = principal
        self.setWindowTitle("Atol — Resultados")
        self.resize(720, 760)
        self.setObjectName("resultados")

        cartao = QtWidgets.QFrame()
        cartao.setObjectName("cartao")
        rotulo = QtWidgets.QLabel("TAMANHO MÉDIO (DIÂMETRO)")
        rotulo.setObjectName("cartaoRotulo")
        self.cartao_valor = QtWidgets.QLabel("—")
        self.cartao_valor.setObjectName("cartaoValor")
        self.cartao_detalhe = QtWidgets.QLabel("Ligue \"Contar objetos\" para ver os resultados.")
        self.cartao_detalhe.setObjectName("cartaoDetalhe")
        lc = QtWidgets.QVBoxLayout(cartao)
        lc.setSpacing(2)
        for w in (rotulo, self.cartao_valor, self.cartao_detalhe):
            lc.addWidget(w)

        cartao_f = QtWidgets.QFrame()
        cartao_f.setObjectName("cartao")
        rotulo_f = QtWidgets.QLabel("FRAÇÃO DE ÁREA")
        rotulo_f.setObjectName("cartaoRotulo")
        self.fracao_valor = QtWidgets.QLabel("—")
        self.fracao_valor.setObjectName("cartaoValor")
        self.fracao_detalhe = QtWidgets.QLabel("Área de objeto ÷ área da imagem")
        self.fracao_detalhe.setObjectName("cartaoDetalhe")
        lf = QtWidgets.QVBoxLayout(cartao_f)
        lf.setSpacing(2)
        for w in (rotulo_f, self.fracao_valor, self.fracao_detalhe):
            lf.addWidget(w)

        cartoes = QtWidgets.QHBoxLayout()
        cartoes.setSpacing(12)
        cartoes.addWidget(cartao, stretch=1)
        cartoes.addWidget(cartao_f, stretch=1)

        self.histograma = Histograma()

        self.tabela = QtWidgets.QTableWidget(0, len(self.COLUNAS))
        self.tabela.setObjectName("tabelaArtigo")
        self.tabela.setShowGrid(False)            # estilo de artigo: sem grade, só 3 linhas horizontais
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        cab = self.tabela.horizontalHeader()
        cab.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        cab.setStretchLastSection(True)
        self.tabela.itemSelectionChanged.connect(self._ao_selecionar)

        self.botao_exportar = QtWidgets.QPushButton("Exportar para Excel…")
        self.botao_exportar.setObjectName("exportar")
        self.botao_exportar.clicked.connect(self.principal.ao_exportar)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(cartoes)
        layout.addWidget(self.histograma)
        layout.addWidget(self.tabela, stretch=1)
        layout.addWidget(self.botao_exportar)

    def mostrar_medidas(self, medidas: list, unidade: str, fracao=None):
        if fracao is None:
            self.fracao_valor.setText("—")
        else:
            self.fracao_valor.setText(f"{fracao:.1f} %".replace(".", ","))
        self.histograma.mostrar([m["diametro"] for m in medidas], unidade)
        if not medidas:
            self.tabela.setRowCount(0)
            self.cartao_valor.setText("—")
            self.cartao_detalhe.setText("Ligue \"Contar objetos\" para ver os resultados.")
            self.botao_exportar.setEnabled(False)
            return
        d = np.array([m["diametro"] for m in medidas])
        desvio = d.std(ddof=1) if len(d) > 1 else 0.0           # desvio padrão da amostra (n − 1)
        self.cartao_valor.setText(f"{d.mean():.2f} ± {desvio:.2f} {unidade}".replace(".", ","))
        self.cartao_detalhe.setText(f"Média ± desvio padrão de {len(d)} objetos")
        unidades = {"area": f"{unidade}²", "perimetro": unidade, "diametro": unidade, "x": unidade, "y": unidade}
        self.tabela.setHorizontalHeaderLabels(
            [c[0] + (f" ({unidades[c[1]]})" if c[1] in unidades else "") for c in self.COLUNAS])
        self.tabela.blockSignals(True)
        self.tabela.setRowCount(len(medidas))
        for i, m in enumerate(medidas):
            for j, (_, chave, casas) in enumerate(self.COLUNAS):
                texto = str(m[chave]) if casas is None else f"{m[chave]:.{casas}f}".replace(".", ",")
                item = QtWidgets.QTableWidgetItem(texto)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(i, j, item)
        self.tabela.blockSignals(False)
        self.botao_exportar.setEnabled(True)

    def _ao_selecionar(self):
        linhas = self.tabela.selectionModel().selectedRows()
        self.linhaEscolhida.emit(linhas[0].row() if linhas else -1)

    def closeEvent(self, evento):
        self.fechada.emit()
        super().closeEvent(evento)

# ---------------------------------------------------------
# Em palavras simples (2):
#   Dois cartões no topo: tamanho médio (média ± desvio padrão do
#   diâmetro) e fração de área. Embaixo, o histograma e a tabela com uma
#   linha por objeto; clicar numa linha destaca o objeto na imagem.
#   A tabela segue o estilo de artigo: sem grade, só três linhas.
# ---------------------------------------------------------
