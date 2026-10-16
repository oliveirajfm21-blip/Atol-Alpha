"""
Janela principal
================

A janela do Atol: barra de temas em cima, painéis das ferramentas à esquerda e o visor no centro.
É aqui que cada chavinha da interface é ligada a um passo do núcleo.

Seções (dentro da classe JanelaAtol):
    1. Topo: marca, menus dos temas, avisos e Tutor
    2. Lateral: painéis das ferramentas e roteiro do Tutor
    3. Centro: visor e barra de zoom
    4. Chaves: ligar/desligar ferramentas e dependências
    5. Controles: o que cada campo dos painéis faz
    6. Desenho: recalcular a linha do tempo e atualizar a tela
"""
import numpy as np
from scipy import ndimage as ndi
from skimage import measure
from PySide6 import QtCore, QtGui, QtWidgets

from .. import __version__
from ..nucleo import (AjustarContraste, Calibracao, ContarObjetos, CorrigirFundo, FiltroMediana, Limiarizar,
                      SepararEncostados, PARA_MM, angulo_entre, angulo_linha, aplicar_linha_do_tempo,
                      carregar_imagem, comprimento_px, dureza_vickers, medir_intercepto, medir_objetos,
                      numero_astm)
from ..saida import exportar_excel
from ..tutor import TEMAS, PRECISA, ROTEIRO, ROTEIROS
from .componentes import CartaoAjuda, Chave, MenuTema, Painel, numpy_para_pixmap
from .estilo import ESPUMA, ESTILO, SIMBOLO_SVG
from .resultados import JanelaResultados
from .visor import DialogoEscala, Visor


class JanelaAtol(QtWidgets.QWidget):
    # temas da barra de cima e, em cada um, as ferramentas (chave, nome)
    TEMAS, PRECISA = TEMAS, PRECISA          # dados em atol/tutor/roteiros.py

    def __init__(self, imagem: np.ndarray):
        super().__init__()
        self.setWindowTitle("Atol " + __version__.replace("a", " alfa ").replace("b", " beta "))
        self.original = imagem
        self.calibracao = Calibracao()     # propriedade da imagem, fora da linha do tempo
        self.medidas = []

        # Linha do tempo: lista de passos aplicados em ordem
        self.mediana = FiltroMediana(raio=2)
        self.fundo = CorrigirFundo(raio=40)
        self.contraste = AjustarContraste(fator=1.0)
        self.limiar = Limiarizar()
        self.separador = SepararEncostados()
        self.contador = ContarObjetos()
        self.passos = [self.mediana, self.fundo, self.contraste, self.limiar, self.separador, self.contador]   # a ordem importa!
        for p in self.passos:
            p.ativo = False

        self.chaves = {}        # nome -> Chave
        self.paineis = {}       # nome -> Painel
        self.janela_resultados = None

        raiz = QtWidgets.QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self.criar_topo())
        corpo = QtWidgets.QHBoxLayout()
        corpo.setSpacing(0)
        corpo.addWidget(self.criar_lateral())
        corpo.addLayout(self.criar_centro(), stretch=1)
        raiz.addLayout(corpo, stretch=1)
        self.criar_menus()                 # depois do corpo: os menus flutuam por cima dele
        self.criar_roteiro()
        self.escolher_roteiro(None)

        self.setStyleSheet(ESTILO)
        self.atualizar_lateral()
        self.renderizar()

    # =========================================================
    # 1. Topo: marca, menus dos temas, avisos e Tutor
    # =========================================================
    def criar_topo(self):
        topo = QtWidgets.QFrame()
        topo.setObjectName("topo")
        layout = QtWidgets.QHBoxLayout(topo)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(6)

        simbolo = QtWidgets.QLabel()
        pix = QtGui.QPixmap()
        pix.loadFromData(SIMBOLO_SVG, "SVG")
        simbolo.setPixmap(pix.scaled(28, 28, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                     QtCore.Qt.TransformationMode.SmoothTransformation))
        nome = QtWidgets.QLabel("Atol")
        nome.setObjectName("marca")
        layout.addWidget(simbolo)
        layout.addWidget(nome)
        layout.addSpacing(24)

        self.botoes_tema = {}
        for tema in self.TEMAS:
            b = QtWidgets.QPushButton(tema)
            b.setObjectName("tema")
            b.setCheckable(True)                     # "marcado" = menu aberto
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, t=tema: self.alternar_menu(t))
            self.botoes_tema[tema] = b
            layout.addWidget(b)
        layout.addStretch()

        self.aviso = QtWidgets.QLabel("")
        self.aviso.setObjectName("aviso")
        self.relogio_aviso = QtCore.QTimer(self)          # o aviso some sozinho depois de alguns segundos
        self.relogio_aviso.setSingleShot(True)
        self.relogio_aviso.timeout.connect(lambda: self.aviso.setText(""))
        layout.addWidget(self.aviso)
        layout.addSpacing(12)

        self.botao_tutor = QtWidgets.QPushButton("Tutor")
        self.botao_tutor.setObjectName("tutor")
        self.botao_tutor.setCheckable(True)
        self.botao_tutor.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.botao_tutor.setToolTip("Escolha o que quer analisar: a esquerda mostra só os passos daquela análise.")
        self.botao_tutor.clicked.connect(lambda: self.alternar_menu("Tutor"))
        layout.addWidget(self.botao_tutor)
        return topo

    def criar_menus(self):
        """Um menu suspenso por tema, com as chavinhas uma embaixo da outra."""
        self.cartao_ajuda = CartaoAjuda(self)
        self.menus = {}
        for tema, itens in self.TEMAS.items():
            menu = MenuTema(self, self.botoes_tema[tema], self.cartao_ajuda)
            if tema == "Imagem":
                self.botao_abrir = QtWidgets.QPushButton("Abrir imagem…")
                self.botao_abrir.setObjectName("acao")
                self.botao_abrir.clicked.connect(lambda: (menu.fechar(), self.ao_clicar_abrir()))
                menu.add(self.botao_abrir)
            for chave, texto in itens:
                c = Chave(texto, menu)
                c.ancora_ajuda = menu
                c.toggled.connect(lambda ligado, k=chave: self.ao_alternar(k, ligado))
                c.pairou.connect(lambda dentro, k=chave, w=c: self.cartao_ajuda.pairar(k, w, dentro))
                c.rolou.connect(self.cartao_ajuda.rolar)
                self.chaves[chave] = c
                menu.add(c)
            self.menus[tema] = menu

    def alternar_menu(self, tema: str):
        menu = self.menus[tema]
        aberto = menu.isVisible()
        for m in self.menus.values():
            m.fechar()
        if not aberto:
            menu.abrir()

    # =========================================================
    # 2. Lateral: painéis das ferramentas e roteiro do Tutor
    # =========================================================
    def criar_lateral(self):
        lateral = QtWidgets.QFrame()
        lateral.setObjectName("lateral")
        self.lateral = lateral
        self.modo_tutor = False
        lateral.setFixedWidth(292)
        externo = QtWidgets.QVBoxLayout(lateral)
        externo.setContentsMargins(0, 0, 0, 0)

        rolagem = QtWidgets.QScrollArea()
        rolagem.setObjectName("rolagemLateral")
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        conteudo = QtWidgets.QWidget()
        conteudo.setObjectName("conteudoLateral")
        self.layout_lateral = QtWidgets.QVBoxLayout(conteudo)
        self.layout_lateral.setContentsMargins(0, 0, 0, 0)
        self.layout_lateral.setSpacing(0)
        rolagem.setWidget(conteudo)
        externo.addWidget(rolagem)

        self.nome_arquivo = QtWidgets.QLabel("Exemplo: moedas (coins)")
        self.nome_arquivo.setObjectName("arquivo")
        self.nome_arquivo.setWordWrap(True)
        self.layout_lateral.addWidget(self.nome_arquivo)

        self.vazio = QtWidgets.QLabel("Clique num tema lá em cima (Imagem, Ajustar…) e ligue uma ferramenta: "
                                      "os ajustes dela aparecem aqui. Ou clique em Tutor e escolha o que quer analisar.")
        self.vazio.setObjectName("vazio")
        self.vazio.setWordWrap(True)
        self.layout_lateral.addWidget(self.vazio)

        # --- Calibrar escala ---
        p = Painel("Calibrar escala", "Desenhe uma linha sobre algo de tamanho conhecido, como uma régua.")
        self.botao_escala = QtWidgets.QPushButton("Desenhar linha de referência")
        self.botao_escala.setObjectName("secundario")
        self.botao_escala.clicked.connect(self.ao_clicar_escala)
        self.rotulo_escala = QtWidgets.QLabel(self.calibracao.texto())
        self.rotulo_escala.setWordWrap(True)
        p.add(self.botao_escala, self.rotulo_escala)
        self.paineis["escala"] = p

        # --- Medir ---
        p = Painel("Medir distância e ângulo",
                   "Clique nas duas pontas de cada medida. Continua medindo até apertar Esc.")
        self.botao_medir = QtWidgets.QPushButton("Desenhar linhas de medida")
        self.botao_medir.setObjectName("secundario")
        self.botao_medir.clicked.connect(self.ao_clicar_medir)
        self.tabela_medir = QtWidgets.QTableWidget(0, 3)
        self.tabela_medir.setObjectName("tabelaArtigo")
        self.tabela_medir.setShowGrid(False)
        self.tabela_medir.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_medir.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela_medir.itemSelectionChanged.connect(self._texto_apagar)
        self.tabela_medir.verticalHeader().setVisible(False)
        self.tabela_medir.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_medir.horizontalHeader().setStretchLastSection(True)
        self.tabela_medir.setMinimumHeight(120)
        self.rotulo_entre = QtWidgets.QLabel("")
        self.rotulo_entre.setWordWrap(True)
        self.botao_apagar_uma = QtWidgets.QPushButton("Apagar a última")
        self.botao_apagar_uma.setObjectName("secundario")
        self.botao_apagar_uma.setToolTip("Selecione uma linha da tabela para apagar só ela; sem seleção, apaga a última.")
        self.botao_apagar_uma.clicked.connect(self.ao_apagar_uma)
        self.botao_apagar_medidas = QtWidgets.QPushButton("Apagar todas")
        self.botao_apagar_medidas.setObjectName("secundario")
        self.botao_apagar_medidas.clicked.connect(self.ao_apagar_medidas)
        botoes = QtWidgets.QWidget()
        lb = QtWidgets.QHBoxLayout(botoes)
        lb.setContentsMargins(0, 0, 0, 0)
        lb.addWidget(self.botao_apagar_uma)
        lb.addWidget(self.botao_apagar_medidas)
        # dureza Vickers: as 2 últimas linhas são as diagonais da marca
        self.escolha_carga = QtWidgets.QComboBox()
        for nome, kgf in (("HV 0,1 (0,1 kgf)", 0.1), ("HV 0,5 (0,5 kgf)", 0.5), ("HV 1 (1 kgf)", 1.0),
                          ("HV 5 (5 kgf)", 5.0), ("HV 10 (10 kgf)", 10.0), ("HV 30 (30 kgf)", 30.0)):
            self.escolha_carga.addItem(nome, kgf)
        self.escolha_carga.setCurrentIndex(4)
        self.escolha_carga.currentIndexChanged.connect(lambda _: self.atualizar_medidas())
        self.rotulo_vickers = QtWidgets.QLabel("")
        self.rotulo_vickers.setObjectName("destaque")
        self.rotulo_vickers.setWordWrap(True)
        self.aviso_vickers = QtWidgets.QLabel("")
        self.aviso_vickers.setWordWrap(True)
        titulo_hv = QtWidgets.QLabel("Dureza Vickers (2 últimas linhas = diagonais)")
        p.add(self.botao_medir, self.tabela_medir, self.rotulo_entre, botoes,
              titulo_hv, self.escolha_carga, self.rotulo_vickers, self.aviso_vickers)
        self.paineis["medir"] = p
        self.linhas_medidas = []          # (x1, y1, x2, y2) em pixels; o valor real sai da escala atual

        # --- Mediana ---
        p = Painel("Remover ruído (mediana)",
                   "Troca cada pixel pela mediana dos vizinhos. Tira pontinhos sem borrar as bordas.")
        self.campo_mediana = QtWidgets.QSpinBox()
        self.campo_mediana.setRange(1, 20)
        self.campo_mediana.setValue(2)
        self.campo_mediana.setSuffix(" px")
        self.campo_mediana.setKeyboardTracking(False)
        self.campo_mediana.valueChanged.connect(self.ao_mudar_mediana)
        p.add(QtWidgets.QLabel("Raio da janela"), self.campo_mediana)
        self.paineis["mediana"] = p

        # --- Corrigir fundo ---
        p = Painel("Corrigir iluminação do fundo",
                   "Remove manchas de luz (rolling ball). O raio deve ser maior que o maior objeto.")
        self.campo_raio = QtWidgets.QSpinBox()
        self.campo_raio.setRange(1, 500)
        self.campo_raio.setValue(40)
        self.campo_raio.setSuffix(" px")
        self.campo_raio.setKeyboardTracking(False)       # só recalcula ao terminar de digitar
        self.campo_raio.valueChanged.connect(self.ao_mudar_raio)
        p.add(QtWidgets.QLabel("Raio da bola"), self.campo_raio)
        self.paineis["fundo"] = p

        # --- Contraste ---
        p = Painel("Ajustar contraste", "Multiplica o brilho de cada pixel pelo fator.")
        self.barra = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.barra.setRange(0, 300)
        self.barra.setValue(100)
        self.barra.valueChanged.connect(self.ao_mudar_barra)
        self.rotulo = QtWidgets.QLabel("Fator: 1,00")
        p.add(self.rotulo, self.barra)
        self.paineis["contraste"] = p

        # --- Separar do fundo ---
        p = Painel("Separar do fundo", "Escolhe sozinho o tom que divide objeto e fundo (limiarização).")
        self.escolha_metodo = QtWidgets.QComboBox()
        self.escolha_metodo.addItems(Limiarizar.METODOS)
        self.escolha_metodo.currentTextChanged.connect(self.ao_mudar_metodo)
        self.caixa_claros = QtWidgets.QCheckBox("Objetos mais claros que o fundo")
        self.caixa_claros.setChecked(True)
        self.caixa_claros.toggled.connect(self.ao_mudar_polaridade)
        self.rotulo_limiar = QtWidgets.QLabel("Limiar: —")
        p.add(self.escolha_metodo, self.caixa_claros, self.rotulo_limiar)
        self.paineis["limiar"] = p

        # --- Watershed ---
        p = Painel("Separar objetos encostados",
                   "Corta objetos que se tocam com uma linha fina (watershed), como o Binary › Watershed do Fiji.")
        self.campo_tolerancia = QtWidgets.QDoubleSpinBox()
        self.campo_tolerancia.setRange(0.1, 20.0)
        self.campo_tolerancia.setSingleStep(0.1)
        self.campo_tolerancia.setDecimals(1)
        self.campo_tolerancia.setValue(0.7)
        self.campo_tolerancia.setSuffix(" px")
        self.campo_tolerancia.setKeyboardTracking(False)
        self.campo_tolerancia.valueChanged.connect(self.ao_mudar_tolerancia)
        self.caixa_buracos = QtWidgets.QCheckBox("Preencher buracos antes de cortar")
        self.caixa_buracos.toggled.connect(self.ao_mudar_buracos)
        self.rotulo_cortes = QtWidgets.QLabel("Manchas: —")
        p.add(QtWidgets.QLabel("Tolerância (aumente se cortar demais)"), self.campo_tolerancia,
              self.caixa_buracos, self.rotulo_cortes)
        self.paineis["watershed"] = p

        # --- Tamanho de grão ---
        p = Painel("Tamanho de grão (intercepto)",
                   "Linhas de teste cruzam a imagem; cada cruzamento com um contorno é contado (ASTM E112).")
        self.campo_linhas = QtWidgets.QSpinBox()
        self.campo_linhas.setRange(3, 50)
        self.campo_linhas.setValue(10)
        self.campo_linhas.setKeyboardTracking(False)
        self.campo_linhas.valueChanged.connect(lambda _: self.renderizar())
        self.rotulo_grao = QtWidgets.QLabel("—")
        self.rotulo_grao.setWordWrap(True)
        self.rotulo_G = QtWidgets.QLabel("G: —")
        self.rotulo_G.setObjectName("destaque")
        p.add(QtWidgets.QLabel("Linhas de teste em cada direção"), self.campo_linhas, self.rotulo_grao, self.rotulo_G)
        self.paineis["grao"] = p

        # --- Contar objetos ---
        p = Painel("Contar objetos", "Cada grupo de pixels brancos encostados vira um objeto.")
        self.campo_area = QtWidgets.QSpinBox()
        self.campo_area.setRange(0, 1_000_000)
        self.campo_area.setSingleStep(50)
        self.campo_area.setSuffix(" px²")
        self.campo_area.valueChanged.connect(self.ao_mudar_area)
        self.caixa_borda = QtWidgets.QCheckBox("Excluir objetos na borda")
        self.caixa_borda.toggled.connect(self.ao_mudar_borda)
        self.rotulo_contagem = QtWidgets.QLabel("Objetos: —")
        self.rotulo_contagem.setObjectName("destaque")
        p.add(QtWidgets.QLabel("Ignorar objetos menores que"), self.campo_area, self.caixa_borda,
              self.rotulo_contagem)
        self.paineis["contar"] = p

        self.intro_tutor = QtWidgets.QLabel("")
        self.intro_tutor.setObjectName("introTutor")
        self.intro_tutor.setWordWrap(True)
        self.intro_tutor.hide()
        self.layout_lateral.addWidget(self.intro_tutor)
        for chave in ("escala", "medir", "mediana", "fundo", "contraste", "limiar", "watershed", "grao", "contar"):
            self.layout_lateral.addWidget(self.paineis[chave])
        self.layout_lateral.addStretch()
        return lateral

    ROTEIRO, ROTEIROS = ROTEIRO, ROTEIROS    # dados em atol/tutor/roteiros.py

    def criar_roteiro(self):
        """Uma linha por passo (número + chavinha + "próximo"), logo acima do painel do passo."""
        self.linhas_tutor, self.chaves_tutor, self.tags_tutor = {}, {}, {}
        self.numeros_tutor, self.dicas_tutor = {}, {}
        self.roteiro_ativo = None
        nomes = {k: t for itens in self.TEMAS.values() for k, t in itens}
        for n, chave in enumerate(self.ROTEIRO, start=1):
            linha = QtWidgets.QFrame()
            linha.setObjectName("passoTutor")
            hl = QtWidgets.QHBoxLayout(linha)
            hl.setContentsMargins(12, 8, 12, 8)
            hl.setSpacing(8)
            numero = QtWidgets.QLabel(str(n))
            numero.setObjectName("numeroTutor")
            numero.setFixedSize(20, 20)
            numero.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            c = Chave(nomes[chave], cor_texto=ESPUMA)
            c.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Fixed)
            c.toggled.connect(lambda ligado, k=chave: self.chaves[k].setChecked(ligado))
            c.pairou.connect(lambda dentro, k=chave, w=c: self.cartao_ajuda.pairar(k, w, dentro))
            c.rolou.connect(self.cartao_ajuda.rolar)
            tag = QtWidgets.QLabel("←")
            tag.setObjectName("tagTutor")
            tag.setToolTip("Próximo passo sugerido")
            dica = QtWidgets.QLabel("")
            dica.setObjectName("dicaTutor")
            dica.setWordWrap(True)
            coluna = QtWidgets.QVBoxLayout()
            coluna.setSpacing(2)
            coluna.addWidget(c)
            coluna.addWidget(dica)
            hl.addWidget(numero, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
            hl.addLayout(coluna, stretch=1)
            hl.addWidget(tag, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
            # entra logo antes do painel do passo (ou no fim, para quem não tem painel)
            if chave in self.paineis:
                pos = self.layout_lateral.indexOf(self.paineis[chave])
            else:
                pos = self.layout_lateral.count() - 1          # antes do addStretch
            self.layout_lateral.insertWidget(pos, linha)
            linha.hide()
            self.linhas_tutor[chave], self.chaves_tutor[chave], self.tags_tutor[chave] = linha, c, tag
            self.numeros_tutor[chave], self.dicas_tutor[chave] = numero, dica
        for c in self.chaves_tutor.values():
            c.ancora_ajuda = self.lateral          # cartão de ajuda abre à direita da lateral

        # menu do Tutor: uma opção por roteiro, como os menus dos temas
        menu = MenuTema(self, self.botao_tutor, self.cartao_ajuda)
        menu.manter_marcado = lambda: self.roteiro_ativo is not None
        titulo = QtWidgets.QLabel("O QUE VOCÊ QUER ANALISAR?")
        titulo.setObjectName("menuTitulo")
        menu.add(titulo)
        for nome, receita in self.ROTEIROS.items():
            b = QtWidgets.QPushButton(f"{nome}\n{receita['descricao']}")
            b.setObjectName("opcaoRoteiro")
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, n=nome: (menu.fechar(), self.escolher_roteiro(n)))
            b.setEnabled(not receita.get("indisponivel", False))
            menu.add(b)
        self.botao_sair_tutor = QtWidgets.QPushButton("Sair do Tutor")
        self.botao_sair_tutor.setObjectName("sairTutor")
        self.botao_sair_tutor.clicked.connect(lambda: (self.escolher_roteiro(None), menu.fechar()))
        menu.add(self.botao_sair_tutor)
        self.menus["Tutor"] = menu

    def escolher_roteiro(self, nome):
        """Mostra na lateral só os passos do roteiro escolhido (None = sai do Tutor)."""
        self.roteiro_ativo = nome
        ligado = nome is not None
        self.modo_tutor = ligado
        passos = self.ROTEIROS[nome]["passos"] if ligado else {}
        self.botao_tutor.setText(f"Tutor · {nome}" if ligado else "Tutor")
        self.botao_tutor.setChecked(ligado)
        self.botao_sair_tutor.setVisible(ligado)
        self.intro_tutor.setText(f"<b style='color:#EFF5F4; font-size:14px'>{nome}</b><br>"
                                 "Ligue os passos de cima para baixo. "
                                 "Pode pular os que a sua imagem não precisa." if ligado else "")
        self.botao_tutor.setMinimumWidth(self.botao_tutor.fontMetrics().horizontalAdvance(
            self.botao_tutor.text()) + 44)
        self.intro_tutor.setVisible(ligado)
        n = 0
        for k in self.ROTEIRO:
            no_roteiro = k in passos
            self.linhas_tutor[k].setVisible(no_roteiro)
            if no_roteiro:
                n += 1
                self.numeros_tutor[k].setText(str(n))     # renumera só os passos do roteiro
                self.dicas_tutor[k].setText(passos[k])
                self.dicas_tutor[k].setVisible(bool(passos[k]))
        for painel in self.paineis.values():
            painel.titulo.setVisible(not ligado)     # o nome já está na linha do roteiro
        self.atualizar_lateral()

    def atualizar_tutor(self):
        """Espelha as chaves e marca o próximo passo: o primeiro desligado depois do último ligado."""
        visiveis = list(self.ROTEIROS[self.roteiro_ativo]["passos"]) if self.roteiro_ativo else []
        visiveis = [k for k in self.ROTEIRO if k in visiveis]
        ligados = [i for i, k in enumerate(visiveis) if self.chaves[k].isChecked()]
        proximo = visiveis[max(ligados) + 1] if ligados and max(ligados) + 1 < len(visiveis) else \
            (visiveis[0] if visiveis and not ligados else None)
        for k in self.ROTEIRO:
            c = self.chaves_tutor[k]
            c.blockSignals(True)
            c.setChecked(self.chaves[k].isChecked())
            c.blockSignals(False)
            c.update()
            eh_proximo = k == proximo
            self.tags_tutor[k].setVisible(eh_proximo)
            linha = self.linhas_tutor[k]
            linha.setProperty("proximo", eh_proximo)
            for w in [linha] + linha.findChildren(QtWidgets.QLabel):   # filhos também, para o número mudar de cor
                w.style().unpolish(w)
                w.style().polish(w)

    def atualizar_lateral(self):
        algum = False
        roteiro = self.ROTEIROS[self.roteiro_ativo]["passos"] if getattr(self, "roteiro_ativo", None) else None
        for chave, painel in self.paineis.items():
            ligado = self.chaves[chave].isChecked() and (roteiro is None or chave in roteiro)
            painel.setVisible(ligado)
            algum = algum or ligado
        self.vazio.setVisible(not algum and not getattr(self, "modo_tutor", False))
        if hasattr(self, "chaves_tutor"):
            self.atualizar_tutor()

    # =========================================================
    # 3. Centro: visor e barra de zoom
    # =========================================================
    def criar_centro(self):
        self.visor = Visor()
        self.visor.setObjectName("visor")
        self.rolagem = QtWidgets.QScrollArea()
        self.rolagem.setObjectName("rolagem")
        self.rolagem.setWidget(self.visor)
        self.rolagem.setWidgetResizable(True)           # o visor ocupa pelo menos a área visível
        self.rolagem.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rolagem.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        barra_zoom = QtWidgets.QFrame()
        barra_zoom.setObjectName("barraZoom")
        self.botao_menos = QtWidgets.QPushButton("−")
        self.botao_mais = QtWidgets.QPushButton("+")
        self.botao_100 = QtWidgets.QPushButton("100%")
        self.botao_ajustar = QtWidgets.QPushButton("Ajustar")
        self.rotulo_zoom = QtWidgets.QLabel("100%")
        dica = QtWidgets.QLabel("Ctrl + roda do mouse: zoom · arrastar: mover")
        dica.setObjectName("dica")
        lz = QtWidgets.QHBoxLayout(barra_zoom)
        lz.setContentsMargins(12, 6, 12, 6)
        lz.addWidget(dica)
        lz.addStretch()
        for w in (self.botao_menos, self.rotulo_zoom, self.botao_mais, self.botao_100, self.botao_ajustar):
            lz.addWidget(w)

        self.visor.linhaDesenhada.connect(self.ao_desenhar_linha)
        self.visor.zoomMudou.connect(lambda z: self.rotulo_zoom.setText(f"{z * 100:.0f}%"))
        self.botao_mais.clicked.connect(lambda: self.visor.definir_zoom(self.visor.zoom * 1.25))
        self.botao_menos.clicked.connect(lambda: self.visor.definir_zoom(self.visor.zoom / 1.25))
        self.botao_100.clicked.connect(lambda: self.visor.definir_zoom(1.0))
        self.botao_ajustar.clicked.connect(self.visor.ajustar_a_janela)

        coluna = QtWidgets.QVBoxLayout()
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(0)
        coluna.addWidget(self.rolagem, stretch=1)
        coluna.addWidget(barra_zoom)
        return coluna

    # =========================================================
    # 4. Chaves: ligar/desligar ferramentas e dependências
    # =========================================================
    def ao_alternar(self, chave: str, ligado: bool):
        # dependências: ligar "contar" liga "separar"; desligar "separar" desliga quem precisa dele
        if ligado and chave in self.PRECISA and not self.chaves[self.PRECISA[chave]].isChecked():
            precisa = self.PRECISA[chave]
            self.avisar(f"\"{self.chaves[chave].text()}\" precisa de "
                        f"\"{self.chaves[precisa].text()}\": liguei para você.")
            self.chaves[precisa].setChecked(True)
        if not ligado:
            for dependente, requisito in self.PRECISA.items():
                if requisito == chave and self.chaves[dependente].isChecked():
                    self.chaves[dependente].setChecked(False)

        if chave == "mediana":
            self.mediana.ativo = ligado
        elif chave == "fundo":
            self.fundo.ativo = ligado
        elif chave == "contraste":
            self.contraste.ativo = ligado
        elif chave == "limiar":
            self.limiar.ativo = ligado
        elif chave == "watershed":
            self.separador.ativo = ligado
        elif chave == "grao":
            pass                                   # medida: calculada no renderizar
        elif chave == "contar":
            self.contador.ativo = ligado
        elif chave == "medir":
            if not ligado and self.visor.modo_calibrar and self.visor.proposito == "medir":
                self.visor.cancelar()
        elif chave == "escala":
            self.calibracao.ativa = ligado
            if not ligado and self.visor.modo_calibrar:
                self.visor.cancelar()
        elif chave == "tabela":
            self.alternar_janela_resultados(ligado)

        self.atualizar_lateral()
        self.renderizar()

    def alternar_janela_resultados(self, ligado: bool):
        if ligado:
            if self.janela_resultados is None:
                self.janela_resultados = JanelaResultados(self)
                self.janela_resultados.fechada.connect(lambda: self.chaves["tabela"].setChecked(False))
                self.janela_resultados.linhaEscolhida.connect(self.ao_selecionar_linha)
            # posiciona ao lado direito da janela principal, na primeira vez
            if not self.janela_resultados.isVisible():
                g = self.frameGeometry()
                self.janela_resultados.move(g.right() - self.janela_resultados.width() - 24, g.top() + 120)
            self.janela_resultados.show()
            self.janela_resultados.raise_()
        elif self.janela_resultados is not None and self.janela_resultados.isVisible():
            self.janela_resultados.blockSignals(True)
            self.janela_resultados.close()
            self.janela_resultados.blockSignals(False)
            self.visor.contornos_destaque = []
            self.visor.update()

    def avisar(self, texto: str):
        self.aviso.setText(texto)
        self.relogio_aviso.start(6000)

    # =========================================================
    # 5. Controles: o que cada campo dos painéis faz
    # =========================================================
    @QtCore.Slot(int)
    def ao_mudar_barra(self, valor: int):
        self.contraste.fator = valor / 100
        self.rotulo.setText(f"Fator: {self.contraste.fator:.2f}".replace(".", ","))
        self.renderizar()

    @QtCore.Slot(float)
    def ao_mudar_tolerancia(self, h: float):
        self.separador.tolerancia = h
        self.renderizar()

    @QtCore.Slot(bool)
    def ao_mudar_buracos(self, preencher: bool):
        self.separador.preencher_buracos = preencher
        self.renderizar()

    @QtCore.Slot(int)
    def ao_mudar_mediana(self, raio: int):
        self.mediana.raio = raio
        self.renderizar()

    @QtCore.Slot(int)
    def ao_mudar_raio(self, raio: int):
        self.fundo.raio = raio
        self.renderizar()

    @QtCore.Slot(int)
    def ao_mudar_area(self, area: int):
        self.contador.area_minima = area
        self.renderizar()

    @QtCore.Slot(bool)
    def ao_mudar_borda(self, excluir: bool):
        self.contador.excluir_borda = excluir
        self.renderizar()

    @QtCore.Slot(str)
    def ao_mudar_metodo(self, metodo: str):
        self.limiar.metodo = metodo
        self.renderizar()

    @QtCore.Slot(bool)
    def ao_mudar_polaridade(self, claros: bool):
        self.limiar.objetos_claros = claros
        self.fundo.objetos_claros = claros
        self.renderizar()

    @QtCore.Slot()
    def ao_clicar_escala(self):
        self.visor.iniciar_calibracao()
        self.rotulo_escala.setText("Clique nas duas pontas de algo com tamanho conhecido (Esc cancela).")

    @QtCore.Slot()
    def ao_clicar_medir(self):
        self.visor.iniciar_calibracao("medir")
        self.avisar("Medindo: clique nas duas pontas. Esc termina.")

    def _linha_escolhida(self):
        linhas = self.tabela_medir.selectionModel().selectedRows()
        return linhas[0].row() if linhas else None

    def _texto_apagar(self):
        self.botao_apagar_uma.setText("Apagar a selecionada" if self._linha_escolhida() is not None
                                      else "Apagar a última")

    @QtCore.Slot()
    def ao_apagar_uma(self):
        """Apaga a medida selecionada na tabela; sem seleção, a última (desfazer o erro mais comum)."""
        if not self.linhas_medidas:
            return
        i = self._linha_escolhida()
        self.linhas_medidas.pop(len(self.linhas_medidas) - 1 if i is None else i)
        self.tabela_medir.clearSelection()
        self.atualizar_medidas()

    @QtCore.Slot()
    def ao_apagar_medidas(self):
        self.linhas_medidas = []
        self.atualizar_medidas()

    def atualizar_medidas(self):
        """Recalcula comprimento e ângulo de cada linha com a escala atual e redesenha."""
        u = self.calibracao.unidade
        self.tabela_medir.setHorizontalHeaderLabels(["#", f"Comprimento ({u})", "Ângulo (°)"])
        self.tabela_medir.setRowCount(len(self.linhas_medidas))
        camada, angulos = [], []
        for i, (x1, y1, x2, y2) in enumerate(self.linhas_medidas):
            d = self.calibracao.comprimento(comprimento_px(x1, y1, x2, y2))
            a = angulo_linha(x1, y1, x2, y2)
            angulos.append(a)
            for j, texto in enumerate((str(i + 1), f"{d:.2f}".replace(".", ","), f"{a:.1f}".replace(".", ","))):
                item = QtWidgets.QTableWidgetItem(texto)
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.tabela_medir.setItem(i, j, item)
            camada.append((x1, y1, x2, y2, f"{i + 1}: {d:.1f} {u}".replace(".", ",")))
        self.tabela_medir.resizeColumnsToContents()
        if len(angulos) >= 2:
            entre = angulo_entre(angulos[-2], angulos[-1])
            self.rotulo_entre.setText(f"Ângulo entre as linhas {len(angulos) - 1} e {len(angulos)}: "
                                      + f"{entre:.1f}°".replace(".", ","))
        else:
            self.rotulo_entre.setText("Desenhe 2 linhas para ver o ângulo entre elas." if angulos else "")
        self.atualizar_vickers()
        self.visor.medicoes = camada if self.chaves["medir"].isChecked() else []
        self.botao_apagar_uma.setEnabled(bool(self.linhas_medidas))
        self.botao_apagar_medidas.setEnabled(bool(self.linhas_medidas))
        self._texto_apagar()
        self.visor.update()

    def atualizar_vickers(self):
        """HV com as duas últimas medidas como d₁ e d₂ (precisa da escala em comprimento real)."""
        if len(self.linhas_medidas) < 2:
            self.rotulo_vickers.setText("HV: meça as duas diagonais da marca")
            self.aviso_vickers.setText("")
            return
        u = self.calibracao.unidade
        if not (self.calibracao.calibrada and u in PARA_MM):
            self.rotulo_vickers.setText("HV: calibre a escala primeiro")
            self.aviso_vickers.setText("")
            return
        d1, d2 = (self.calibracao.comprimento(comprimento_px(*l)) * PARA_MM[u] for l in self.linhas_medidas[-2:])
        F = self.escolha_carga.currentData()
        hv = dureza_vickers(F, d1, d2)
        self.rotulo_vickers.setText(f"{hv:.0f} HV {F:g}".replace(".", ",")
                                    + f"   (d = {(d1 + d2) / 2 * 1000:.1f} µm)".replace(".", ","))
        avisos = []
        diferenca = abs(d1 - d2) / ((d1 + d2) / 2)
        if diferenca > 0.05:                      # marcas tortas: superfície inclinada ou mal preparada
            avisos.append(f"As diagonais diferem {diferenca * 100:.0f}%: confira se a superfície "
                          "está plana e perpendicular à ponta.")
        a = angulo_entre(angulo_linha(*self.linhas_medidas[-2]), angulo_linha(*self.linhas_medidas[-1]))
        if a < 80:
            avisos.append(f"As duas linhas fazem {a:.0f}° entre si; as diagonais deveriam ser perpendiculares (90°).")
        self.aviso_vickers.setText("\n".join(avisos).replace(".", ",", 0))

    @QtCore.Slot(float, float, float, float)
    def ao_desenhar_linha(self, x1, y1, x2, y2):
        if self.visor.proposito == "medir":
            if comprimento_px(x1, y1, x2, y2) >= 1:
                self.linhas_medidas.append((x1, y1, x2, y2))
                self.atualizar_medidas()
            self.visor.iniciar_calibracao("medir")          # continua medindo até o Esc
            return
        d_px = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5       # Pitágoras
        if d_px < 1:
            self.rotulo_escala.setText("Linha curta demais. " + self.calibracao.texto())
            return
        dialogo = DialogoEscala(d_px, self)
        if dialogo.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.calibracao.definir(d_px, dialogo.campo_valor.value(), dialogo.campo_unidade.currentText())
        self.rotulo_escala.setText(self.calibracao.texto())
        self.renderizar()

    @QtCore.Slot(int)
    def ao_selecionar_linha(self, indice: int):
        if indice < 0 or indice >= len(self.medidas):
            self.visor.contornos_destaque = []
            self.visor.update()
            return
        m = self.medidas[indice]
        mascara = ndi.binary_fill_holes(self.contador.rotulos == m["rotulo"]).astype(float)
        contornos = measure.find_contours(np.pad(mascara, 1), 0.5)
        # find_contours trabalha na imagem com 1 pixel de borda: desconta esse 1; fica só o de fora
        self.visor.contornos_destaque = [max(contornos, key=len) - 1] if contornos else []
        alvo = self.visor.imagem_para_tela(m["_cx"], m["_cy"])         # leva a rolagem até o objeto
        self.rolagem.ensureVisible(round(alvo.x()), round(alvo.y()), 80, 80)
        self.visor.update()

    @QtCore.Slot()
    def ao_exportar(self):
        pai = self.janela_resultados or self
        caminho, _ = QtWidgets.QFileDialog.getSaveFileName(
            pai, "Exportar resultados", "resultados_atol.xlsx", "Planilha do Excel (*.xlsx)")
        if not caminho:
            return
        try:
            exportar_excel(caminho, self.medidas, self.calibracao, self.nome_arquivo.text(),
                           self.limiar.fracao_area if self.limiar.ativo else None)
        except ImportError:
            QtWidgets.QMessageBox.warning(pai, "Falta um pacote",
                "Para exportar para Excel, instale o openpyxl:\n\npip install openpyxl")
            return
        except OSError as erro:
            QtWidgets.QMessageBox.warning(pai, "Não consegui salvar",
                f"{caminho}\n\n{erro}\n\nSe a planilha estiver aberta no Excel, feche e tente de novo.")
            return
        self.avisar("Resultados exportados.")

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        if self.visor.ajustar:
            QtCore.QTimer.singleShot(0, self.visor.ajustar_a_janela)

    def keyPressEvent(self, evento):
        if evento.key() == QtCore.Qt.Key.Key_Escape and self.visor.modo_calibrar:
            medindo = self.visor.proposito == "medir"
            self.visor.cancelar()
            if medindo:
                self.avisar("Medição terminada.")
            else:
                self.rotulo_escala.setText(self.calibracao.texto())
        else:
            super().keyPressEvent(evento)

    @QtCore.Slot()
    def ao_clicar_abrir(self):
        caminho, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Abrir imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif);;Todos (*)")
        if caminho:                     # vazio = usuário cancelou
            self.abrir(caminho)

    def abrir(self, caminho: str):
        """Única porta de entrada de imagens (o arrastar e soltar vai usar esta)."""
        try:
            self.original = carregar_imagem(caminho)
        except Exception as erro:
            QtWidgets.QMessageBox.warning(self, "Não consegui abrir", f"{caminho}\n\n{erro}")
            return
        self.nome_arquivo.setText(caminho.replace("\\", "/").split("/")[-1])
        self.calibracao = Calibracao()          # imagem nova: escala nova
        self.calibracao.ativa = self.chaves["escala"].isChecked()
        self.visor.linha = None
        self.visor.ajustar = True
        self.rotulo_escala.setText(self.calibracao.texto())
        self.renderizar()

    # =========================================================
    # 6. Desenho: recalcular a linha do tempo e atualizar a tela
    # =========================================================
    def renderizar(self):
        resultado = aplicar_linha_do_tempo(self.original, self.passos)
        self.visor.mostrar(numpy_para_pixmap(resultado))
        if self.limiar.ativo and self.limiar.ultimo_T is not None:
            self.rotulo_limiar.setText(f"Limiar: {self.limiar.ultimo_T:.1f}".replace(".", ","))
        else:
            self.rotulo_limiar.setText("Limiar: —")

        if self.separador.ativo and self.separador.depois is not None:
            self.rotulo_cortes.setText(f"Manchas: {self.separador.antes} → objetos: {self.separador.depois}")
        else:
            self.rotulo_cortes.setText("Manchas: —")

        self.atualizar_grao()
        if hasattr(self, "linhas_medidas"):
            self.atualizar_medidas()

        tem_objetos = self.contador.ativo and self.contador.rotulos is not None and self.contador.contagem
        self.medidas = medir_objetos(self.contador.rotulos, self.calibracao) if tem_objetos else []
        if self.contador.ativo and self.contador.contagem is not None:
            self.rotulo_contagem.setText(f"Objetos: {self.contador.contagem}")
        else:
            self.rotulo_contagem.setText("Objetos: —")
        if self.janela_resultados is not None:
            fracao = self.limiar.fracao_area if self.limiar.ativo else None
            self.janela_resultados.mostrar_medidas(self.medidas, self.calibracao.unidade, fracao)
        self.visor.contornos_destaque = []
        self.atualizar_etiquetas()

    def atualizar_grao(self):
        """Tamanho de grão pelo intercepto, sobre a máscara do "Separar do fundo" (grão = branco)."""
        ligado = self.chaves["grao"].isChecked() and self.limiar.ativo and self.limiar.ultima_mascara is not None
        if not ligado:
            self.visor.linhas_teste, self.visor.pontos_teste = [], []
            self.rotulo_grao.setText("—")
            self.rotulo_G.setText("G: —")
            return
        r = medir_intercepto(self.limiar.ultima_mascara, self.campo_linhas.value())
        self.visor.linhas_teste, self.visor.pontos_teste = r["linhas"], r["pontos"]
        if r["l"] is None:
            self.rotulo_grao.setText("Nenhum contorno cruzado. Confira se os grãos estão brancos e os contornos pretos.")
            self.rotulo_G.setText("G: —")
            return
        u = self.calibracao.unidade
        c = self.calibracao.comprimento
        fmt = lambda v: "—" if v is None else f"{c(v):.2f} {u}".replace(".", ",")
        texto = (f"Interseções: {r['N_h'] + r['N_v']}\n"
                 f"Intercepto horizontal: {fmt(r['l_h'])}\n"
                 f"Intercepto vertical: {fmt(r['l_v'])}\n"
                 f"Intercepto médio ℓ̄: {fmt(r['l'])}")
        if r["l_h"] and r["l_v"]:
            texto += "\nAlongamento (horiz./vert.): " + f"{r['l_h'] / r['l_v']:.2f}".replace(".", ",")
        self.rotulo_grao.setText(texto)
        if self.calibracao.calibrada and u in PARA_MM:
            G = numero_astm(c(r["l"]) * PARA_MM[u])
            self.rotulo_G.setText(f"G (ASTM E112): {G:.1f}".replace(".", ","))
        else:
            self.rotulo_G.setText("G: calibre a escala para calcular")

    def atualizar_etiquetas(self):
        """Camada de visualização: diâmetro equivalente de cada objeto, no centro dele."""
        if not (self.chaves["diametro"].isChecked() and self.medidas):
            self.visor.etiquetas, self.visor.rotulos = {}, None
            self.visor.update()
            return
        u = self.calibracao.unidade
        self.visor.etiquetas = {m["rotulo"]: (m["_cx"] - 0.5, m["_cy"] - 0.5,
                                              f"{m['diametro']:.1f} {u}".replace(".", ","))
                                for m in self.medidas}
        self.visor.rotulos = self.contador.rotulos
        self.visor.update()

# ---------------------------------------------------------
# Em palavras simples (janela):
#   O caminho de um clique: o usuário liga uma chavinha no menu ->
#   ao_alternar liga também o que é pré-requisito (PRECISA) e marca o
#   passo como ativo -> renderizar roda a linha do tempo desde a imagem
#   original -> o visor, o painel, as medidas e a janela de Resultados
#   são atualizados. Os campos dos painéis seguem o mesmo caminho: mudam
#   um parâmetro do passo e chamam renderizar. O Tutor não tem lógica
#   própria: ele só mostra, na lateral, as chaves de um roteiro na ordem.
# ---------------------------------------------------------
