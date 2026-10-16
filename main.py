"""
Atol
====

Análise de imagens científicas para quem está começando.
Desenvolvido por João Filipe M. de Oliveira (Unicamp, laboratório do Prof. Dr. Gilberto Prandi).

Uso:
    python main.py              # abre o Atol com uma imagem de exemplo
    pytest                      # roda os testes de validação
    python -m atol.ajuda.gerar  # refaz as figuras dos cartões de ajuda
"""
import sys

from PySide6 import QtWidgets
from skimage import data

from atol.interface import JanelaAtol


def principal():
    app = QtWidgets.QApplication(sys.argv)
    janela = JanelaAtol(data.coins())        # imagem de exemplo até o usuário abrir a dele
    janela.resize(1200, 760)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    principal()
