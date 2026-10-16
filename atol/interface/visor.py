"""
Visor
=====

Mostra a imagem e tudo o que é desenhado por cima dela (camadas), sem mudar nenhum pixel.

Seções:
    1. Visor: zoom, arrastar, cliques de linha (calibrar e medir) e camadas
    2. Diálogo da escala

Conversão entre tela e imagem (z = zoom, o = deslocamento da imagem na tela):
    x_imagem = (x_tela - o) / z
"""
from PySide6 import QtCore, QtGui, QtWidgets


# =========================================================
# 1. Visor
# =========================================================

class Visor(QtWidgets.QLabel):
    """Mostra a imagem e, no modo calibrar, recebe dois cliques e desenha a linha."""
    linhaDesenhada = QtCore.Signal(float, float, float, float)   # x1, y1, x2, y2 em pixels da imagem
    zoomMudou = QtCore.Signal(float)

    def __init__(self):
        super().__init__(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self.modo_calibrar = False
        self.p1 = None          # primeiro clique (coordenadas da imagem)
        self.p_mouse = None     # posição atual do mouse, para a linha "elástica"
        self.linha = None       # última linha de calibração (x1, y1, x2, y2)
        # camada "tamanho dos objetos": só visualização, não muda pixels nem medidas
        self.etiquetas = {}     # rótulo -> (x, y, texto) em pixels da imagem
        self.rotulos = None     # matriz de rótulos, para saber qual objeto está sob o mouse
        self.rotulo_mouse = 0   # objeto sob o mouse (0 = nenhum)
        self.LIMITE = 60        # acima disso, mostra só o objeto sob o mouse
        self.contornos_destaque = []   # contorno do objeto escolhido na tabela (pixels da imagem)
        self.linhas_teste = []         # tamanho de grão: linhas de teste (x1, y1, x2, y2)
        self.medicoes = []             # medir: (x1, y1, x2, y2, rótulo) em pixels da imagem
        self.pontos_teste = []         # e as interseções com os contornos (x, y)
        # zoom: só visualização (não muda pixels nem medidas)
        self.base = None        # pixmap em tamanho real (100%)
        self.zoom = 1.0         # z: 1 pixel da imagem ocupa z pixels da tela
        self.ajustar = True     # True = acompanha o tamanho da janela
        self._arrasto = None    # posição do último ponto ao arrastar com o mouse

    # ---- zoom ----
    def mostrar(self, pixmap):
        """Recebe a imagem em tamanho real e redesenha com o zoom atual."""
        self.base = pixmap
        if self.ajustar:
            self.zoom = self.zoom_para_caber()
        self._aplicar_zoom()

    def area_visivel(self):
        rolagem = self.parent().parent() if self.parent() else None   # QScrollArea
        return rolagem.viewport().size() if rolagem else self.size()

    def zoom_para_caber(self):
        if self.base is None:
            return 1.0
        v = self.area_visivel()
        return max(0.05, min(v.width() / self.base.width(), v.height() / self.base.height()))

    def _aplicar_zoom(self):
        if self.base is None:
            return
        w = max(1, round(self.base.width() * self.zoom))
        h = max(1, round(self.base.height() * self.zoom))
        # FastTransformation = vizinho mais próximo: cada pixel vira um quadrado nítido,
        # sem suavizar (suavizar inventaria tons que não existem na imagem científica)
        self.setPixmap(self.base.scaled(w, h, QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                                        QtCore.Qt.TransformationMode.FastTransformation))
        self.setMinimumSize(w, h)
        self.zoomMudou.emit(self.zoom)

    def definir_zoom(self, novo, ancora=None):
        """Muda o zoom mantendo parado o ponto da imagem sob a âncora (posição na tela)."""
        novo = max(0.05, min(32.0, novo))
        rolagem = self.parent().parent() if self.parent() else None
        ponto = self.tela_para_imagem(ancora) if ancora is not None else None
        antes = ancora
        self.ajustar = False
        self.zoom = novo
        self._aplicar_zoom()
        if rolagem is not None and ponto is not None:
            QtWidgets.QApplication.processEvents()           # deixa o layout pegar o tamanho novo
            depois = self.imagem_para_tela(*ponto)
            barra_h, barra_v = rolagem.horizontalScrollBar(), rolagem.verticalScrollBar()
            barra_h.setValue(barra_h.value() + round(depois.x() - antes.x()))
            barra_v.setValue(barra_v.value() + round(depois.y() - antes.y()))

    def ajustar_a_janela(self):
        self.ajustar = True
        self.zoom = self.zoom_para_caber()
        self._aplicar_zoom()

    def wheelEvent(self, evento):
        if evento.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            fator = 1.25 if evento.angleDelta().y() > 0 else 1 / 1.25
            self.definir_zoom(self.zoom * fator, evento.position())
            evento.accept()
        else:
            evento.ignore()                                    # rolagem normal

    # ---- conversão tela <-> imagem ----
    # x_tela = x_imagem · z + deslocamento   <=>   x_imagem = (x_tela − deslocamento) / z
    def _deslocamento(self):
        pix = self.pixmap()
        if pix is None or pix.isNull():
            return None
        return ((self.width() - pix.width()) / 2, (self.height() - pix.height()) / 2,
                pix.width(), pix.height())

    def tela_para_imagem(self, pos):
        d = self._deslocamento()
        if d is None:
            return None
        ox, oy, w, h = d
        x, y = (pos.x() - ox) / self.zoom, (pos.y() - oy) / self.zoom
        if 0 <= x < self.base.width() and 0 <= y < self.base.height():
            return (x, y)
        return None             # clique fora da imagem

    def imagem_para_tela(self, x, y):
        ox, oy, _, _ = self._deslocamento()
        return QtCore.QPointF(x * self.zoom + ox, y * self.zoom + oy)

    # ---- eventos do mouse ----
    def iniciar_calibracao(self, proposito: str = "calibrar"):
        self.proposito = proposito             # "calibrar" guarda a linha; "medir" só avisa
        self.modo_calibrar = True
        self.p1 = None
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)

    def cancelar(self):
        self.modo_calibrar = False
        self.p1 = None
        self.unsetCursor()
        self.update()

    def mousePressEvent(self, evento):
        if not self.modo_calibrar:
            self._arrasto = evento.globalPosition()            # começa a arrastar a imagem
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            return
        ponto = self.tela_para_imagem(evento.position())
        if ponto is None:
            return
        if self.p1 is None:
            self.p1 = ponto                                  # 1º clique: uma ponta
        else:
            x1, y1 = self.p1                                 # 2º clique: a outra ponta
            x2, y2 = ponto
            if getattr(self, "proposito", "calibrar") == "calibrar":
                self.linha = (x1, y1, x2, y2)
            self.cancelar()
            self.linhaDesenhada.emit(x1, y1, x2, y2)
        self.update()

    def mouseReleaseEvent(self, evento):
        if self._arrasto is not None:
            self._arrasto = None
            self.unsetCursor()

    def mouseMoveEvent(self, evento):
        if self._arrasto is not None:
            rolagem = self.parent().parent() if self.parent() else None
            if rolagem is not None:
                delta = evento.globalPosition() - self._arrasto
                self._arrasto = evento.globalPosition()
                rolagem.horizontalScrollBar().setValue(rolagem.horizontalScrollBar().value() - round(delta.x()))
                rolagem.verticalScrollBar().setValue(rolagem.verticalScrollBar().value() - round(delta.y()))
        self.p_mouse = self.tela_para_imagem(evento.position())
        if self.modo_calibrar and self.p1 is not None:
            self.update()
        if self.rotulos is not None and self.etiquetas:
            novo = 0
            if self.p_mouse is not None:
                x, y = self.p_mouse
                novo = int(self.rotulos[int(y), int(x)])
            if novo != self.rotulo_mouse:
                self.rotulo_mouse = novo
                self.update()

    def _desenhar_etiqueta(self, pintor, x, y, texto):
        centro = self.imagem_para_tela(x, y)
        metricas = pintor.fontMetrics()
        largura = metricas.horizontalAdvance(texto) + 8
        altura = metricas.height() + 2
        caixa = QtCore.QRectF(centro.x() - largura / 2, centro.y() - altura / 2, largura, altura)
        pintor.setPen(QtCore.Qt.PenStyle.NoPen)
        pintor.setBrush(QtGui.QColor(11, 51, 64, 210))          # oceano, quase opaco
        pintor.drawRoundedRect(caixa, 3, 3)
        pintor.setPen(QtGui.QColor("#EFF5F4"))                  # espuma
        pintor.drawText(caixa, QtCore.Qt.AlignmentFlag.AlignCenter, texto)

    def paintEvent(self, evento):
        super().paintEvent(evento)                           # desenha a imagem
        if self._deslocamento() is None:
            return
        pintor = QtGui.QPainter(self)
        pintor.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self.etiquetas:
            fonte = pintor.font()
            fonte.setPointSizeF(8.5)
            pintor.setFont(fonte)
            if len(self.etiquetas) <= self.LIMITE:
                visiveis = self.etiquetas.values()
            else:
                visiveis = [self.etiquetas[self.rotulo_mouse]] if self.rotulo_mouse in self.etiquetas else []
            for x, y, texto in visiveis:
                self._desenhar_etiqueta(pintor, x + 0.5, y + 0.5, texto)   # centro do pixel
        if self.linhas_teste:
            pintor.setPen(QtGui.QPen(QtGui.QColor("#1FA89C"), 1.5))
            for x1, y1, x2, y2 in self.linhas_teste:
                pintor.drawLine(self.imagem_para_tela(x1, y1), self.imagem_para_tela(x2, y2))
            pintor.setPen(QtGui.QPen(QtGui.QColor("#FFFFFF"), 1))
            pintor.setBrush(QtGui.QColor("#F2606F"))
            for x, y in self.pontos_teste:
                pintor.drawEllipse(self.imagem_para_tela(x, y), 3.5, 3.5)
        if self.medicoes:
            for x1, y1, x2, y2, rotulo in self.medicoes:
                a, b = self.imagem_para_tela(x1, y1), self.imagem_para_tela(x2, y2)
                pintor.setPen(QtGui.QPen(QtGui.QColor("#FFFFFF"), 4))       # contorno branco: lê em qualquer fundo
                pintor.drawLine(a, b)
                pintor.setPen(QtGui.QPen(QtGui.QColor("#1FA89C"), 2))
                pintor.drawLine(a, b)
                self._desenhar_etiqueta(pintor, (x1 + x2) / 2, (y1 + y2) / 2, rotulo)
        if self.contornos_destaque:
            pintor.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            pintor.setPen(QtGui.QPen(QtGui.QColor("#F2606F"), 3))   # coral: o selecionado
            for contorno in self.contornos_destaque:
                pontos = [self.imagem_para_tela(c + 0.5, l + 0.5) for l, c in contorno]
                pintor.drawPolygon(QtGui.QPolygonF(pontos))
        caneta = QtGui.QPen(QtGui.QColor("#F2606F"), 2)      # coral: o que está selecionado
        pintor.setPen(caneta)
        if self.modo_calibrar and self.p1 is not None and self.p_mouse is not None:
            pintor.drawLine(self.imagem_para_tela(*self.p1), self.imagem_para_tela(*self.p_mouse))
        elif self.linha is not None:
            x1, y1, x2, y2 = self.linha
            pintor.drawLine(self.imagem_para_tela(x1, y1), self.imagem_para_tela(x2, y2))
        pintor.end()


# ---------------------------------------------------------
# Em palavras simples (1):
#   O visor é uma "janela" sobre a imagem. O zoom só muda o tamanho com
#   que os pixels são desenhados; as medidas continuam na imagem real.
#   Por isso todo clique é convertido da tela para a imagem antes de ser
#   usado. Etiquetas de diâmetro, contorno destacado, linhas de medida e
#   linhas do tamanho de grão são camadas: desenhadas por cima, nunca
#   gravadas na imagem.
# ---------------------------------------------------------


# =========================================================
# 2. Diálogo da escala
# =========================================================

class DialogoEscala(QtWidgets.QDialog):
    """Pergunta quanto a linha desenhada mede de verdade."""
    UNIDADES = ("nm", "µm", "mm", "cm", "m")

    def __init__(self, d_px: float, pai=None):
        super().__init__(pai)
        self.setWindowTitle("Calibrar escala")
        texto = QtWidgets.QLabel(f"A linha tem {d_px:.1f} pixels.\nQuanto ela mede de verdade?".replace(".", ",", 1))
        self.campo_valor = QtWidgets.QDoubleSpinBox()
        self.campo_valor.setRange(0.0001, 1_000_000)
        self.campo_valor.setDecimals(4)
        self.campo_valor.setValue(10)
        self.campo_unidade = QtWidgets.QComboBox()
        self.campo_unidade.addItems(self.UNIDADES)
        self.campo_unidade.setCurrentText("mm")
        linha = QtWidgets.QHBoxLayout()
        linha.addWidget(self.campo_valor)
        linha.addWidget(self.campo_unidade)
        botoes = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok |
                                            QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(texto)
        layout.addLayout(linha)
        layout.addWidget(botoes)



