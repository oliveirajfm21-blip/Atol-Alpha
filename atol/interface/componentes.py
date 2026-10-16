"""
Componentes
===========

Peças reutilizáveis da interface.

Seções:
    1. Ponte NumPy -> Qt
    2. Cartão de ajuda (aparece ao parar o mouse numa ferramenta)
    3. Chave, menu suspenso e painel
"""
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..ajuda import AJUDA, CSS as CSS_AJUDA, PASTA_IMAGENS as PASTA_AJUDA
from .estilo import CORAL, OCEANO


# =========================================================
# 1. Ponte NumPy -> Qt
# =========================================================

def numpy_para_pixmap(imagem: np.ndarray) -> QtGui.QPixmap:
    imagem = np.ascontiguousarray(imagem)
    altura, largura = imagem.shape[:2]
    if imagem.ndim == 2:
        formato = QtGui.QImage.Format.Format_Grayscale8
    else:
        formato = QtGui.QImage.Format.Format_RGB888
    qimg = QtGui.QImage(imagem.data, largura, altura, imagem.strides[0], formato)
    return QtGui.QPixmap.fromImage(qimg.copy())




# =========================================================
# 2. Cartão de ajuda
# =========================================================

class CartaoAjuda(QtWidgets.QFrame):
    """Cartão que aparece ao parar o mouse numa ferramenta: técnica, fórmulas e figuras.
    Rola com a roda do mouse (em cima da chave ou do próprio cartão)."""

    def __init__(self, pai):
        super().__init__(pai, QtCore.Qt.WindowType.ToolTip | QtCore.Qt.WindowType.FramelessWindowHint)
        self.setObjectName("cartaoAjuda")
        self.resize(400, 460)
        self.texto = QtWidgets.QTextBrowser()
        self.texto.setOpenExternalLinks(False)
        self.texto.setSearchPaths([str(PASTA_AJUDA)])
        self.texto.document().setDefaultStyleSheet(CSS_AJUDA)
        self.texto.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.texto.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 6, 12)
        layout.addWidget(self.texto)
        self._alvo = None
        self.relogio_mostrar = QtCore.QTimer(self, singleShot=True, interval=450)
        self.relogio_mostrar.timeout.connect(self._mostrar)
        self.relogio_esconder = QtCore.QTimer(self, singleShot=True, interval=300)
        self.relogio_esconder.timeout.connect(self.hide)

    def pairar(self, chave: str, widget, dentro: bool):
        if chave not in AJUDA:
            return
        if dentro:
            self.relogio_esconder.stop()
            if self.isVisible() and self._alvo and self._alvo[0] == chave:
                return
            self._alvo = (chave, widget)
            self.relogio_mostrar.start()
        else:
            self.relogio_mostrar.stop()
            self.relogio_esconder.start()

    def _mostrar(self):
        chave, widget = self._alvo
        self.texto.setHtml(AJUDA[chave])
        self.texto.verticalScrollBar().setValue(0)
        ancora = getattr(widget, "ancora_ajuda", None)
        if ancora is not None:            # lista vertical: abre ao lado, sem tapar os itens de baixo
            pos = QtCore.QPoint(ancora.mapToGlobal(QtCore.QPoint(ancora.width() + 8, 0)).x(),
                                widget.mapToGlobal(QtCore.QPoint(0, -12)).y())
        else:
            pos = widget.mapToGlobal(QtCore.QPoint(0, widget.height() + 8))
        tela = widget.screen().availableGeometry()
        x = min(max(pos.x(), tela.left() + 8), tela.right() - self.width() - 8)
        y = min(pos.y(), tela.bottom() - self.height() - 8)
        self.move(x, y)
        self.show()

    def rolar(self, delta: int):
        if self.isVisible():
            barra = self.texto.verticalScrollBar()
            barra.setValue(barra.value() - delta // 2)

    def enterEvent(self, evento):
        self.relogio_esconder.stop()

    def leaveEvent(self, evento):
        self.relogio_esconder.start()


# ---------------------------------------------------------
# Em palavras simples (2):
#   Parar o mouse numa ferramenta abre um cartão com o nome da técnica,
#   o que acontece por trás, as fórmulas e a referência. Os textos ficam
#   em atol/ajuda; o cartão só sabe mostrar e rolar.
# ---------------------------------------------------------


# =========================================================
# 3. Chave, menu suspenso e painel
# =========================================================

class Chave(QtWidgets.QAbstractButton):
    """Chavinha liga/desliga com o nome ao lado."""
    pairou = QtCore.Signal(bool)         # mouse entrou (True) ou saiu (False)
    rolou = QtCore.Signal(int)           # roda do mouse em cima da chave

    def __init__(self, texto: str, pai=None, cor_texto: str = OCEANO):
        super().__init__(pai)
        self.setText(texto)
        self.setCheckable(True)
        self.cor_texto = cor_texto
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, evento):
        self.pairou.emit(True)

    def leaveEvent(self, evento):
        self.pairou.emit(False)

    def wheelEvent(self, evento):
        self.rolou.emit(evento.angleDelta().y())
        evento.accept()

    def sizeHint(self):
        largura = 34 + 8 + self.fontMetrics().horizontalAdvance(self.text())
        return QtCore.QSize(largura, 26)

    def paintEvent(self, evento):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        trilho = QtCore.QRectF(0, 5, 34, 16)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QColor(CORAL if self.isChecked() else "#9DB6BA"))
        p.drawRoundedRect(trilho, 8, 8)
        x = 20 if self.isChecked() else 2
        p.setBrush(QtGui.QColor("#FFFFFF"))
        p.drawEllipse(QtCore.QRectF(x, 7, 12, 12))
        if self.hasFocus():
            p.setPen(QtGui.QPen(QtGui.QColor("#C2364A"), 2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(trilho.adjusted(-2, -2, 2, 2), 10, 10)
        p.setPen(QtGui.QColor(self.cor_texto if self.isEnabled() else "#9DB6BA"))
        p.drawText(QtCore.QRectF(42, 0, self.width() - 42, 26),
                   QtCore.Qt.AlignmentFlag.AlignVCenter, self.text())
        p.end()


class MenuTema(QtWidgets.QFrame):
    """Lista que desce do botão do tema e some quando o mouse sai dela (e do botão)."""

    def __init__(self, pai, botao, cartao_ajuda):
        super().__init__(pai)
        self.setObjectName("menuTema")
        self.botao = botao
        self.cartao_ajuda = cartao_ajuda
        self.layout_ = QtWidgets.QVBoxLayout(self)
        self.layout_.setContentsMargins(12, 10, 16, 12)
        self.layout_.setSpacing(8)
        self.relogio_fechar = QtCore.QTimer(self, singleShot=True, interval=280)  # folga para o mouse
        self.relogio_fechar.timeout.connect(self._talvez_fechar)
        sombra = QtWidgets.QGraphicsDropShadowEffect(self, blurRadius=18, offset=QtCore.QPointF(0, 4))
        sombra.setColor(QtGui.QColor(11, 51, 64, 70))
        self.setGraphicsEffect(sombra)
        self.hide()

    def add(self, w):
        self.layout_.addWidget(w)

    def abrir(self):
        self.adjustSize()
        canto = self.botao.mapTo(self.parentWidget(), QtCore.QPoint(0, self.botao.height() + 6))
        canto.setX(min(canto.x(), self.parentWidget().width() - self.width() - 8))   # cabe na janela
        self.move(canto)
        self.show()
        self.raise_()
        self.botao.setChecked(True)

    manter_marcado = staticmethod(lambda: False)     # o Tutor fica marcado enquanto há roteiro ativo

    def fechar(self):
        self.hide()
        self.botao.setChecked(self.manter_marcado())

    def _mouse_dentro(self):
        pos = QtGui.QCursor.pos()
        for w in (self, self.botao, self.cartao_ajuda):
            if w.isVisible() and w.rect().contains(w.mapFromGlobal(pos)):
                return True
        return False

    def _talvez_fechar(self):
        if self._mouse_dentro():
            self.relogio_fechar.start()      # ainda está em cima: confere de novo daqui a pouco
        else:
            self.fechar()

    def enterEvent(self, evento):
        self.relogio_fechar.stop()

    def leaveEvent(self, evento):
        self.relogio_fechar.start()


class Painel(QtWidgets.QFrame):
    """Bloco de uma ferramenta na barra lateral: título, explicação e controles."""

    def __init__(self, titulo: str, explicacao: str):
        super().__init__()
        self.setObjectName("painel")
        self.layout_ = QtWidgets.QVBoxLayout(self)
        self.layout_.setContentsMargins(16, 14, 16, 14)
        self.layout_.setSpacing(6)
        t = QtWidgets.QLabel(titulo)
        t.setObjectName("painelTitulo")
        self.titulo = t
        e = QtWidgets.QLabel(explicacao)
        e.setObjectName("painelExplicacao")
        e.setWordWrap(True)
        self.layout_.addWidget(t)
        self.layout_.addWidget(e)

    def add(self, *widgets):
        for w in widgets:
            self.layout_.addWidget(w)

# ---------------------------------------------------------
# Em palavras simples (3):
#   Chave: a chavinha liga/desliga desenhada à mão, com o nome ao lado.
#   MenuTema: a lista que desce do botão do tema e some quando o mouse
#   sai. Painel: o bloco da lateral com título, explicação e controles.
# ---------------------------------------------------------
