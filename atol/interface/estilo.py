"""
Estilo
======

Identidade visual do Atol: símbolo (lupa com lente de atol), paleta e folha de estilo (QSS).

Paleta: oceano #0B3340 · espuma #EFF5F4 · coral #F2606F · lagoa #1FA89C · visor #808080
"""

SIMBOLO_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g fill="none" stroke-linecap="round">
<line x1="39.4" y1="39.4" x2="56" y2="56" stroke="#EFF5F4" stroke-width="7"/>
<circle cx="26" cy="26" r="16" stroke="#EFF5F4" stroke-width="6" stroke-linecap="butt" stroke-dasharray="40.68 4 22.53 4 25.32 4" stroke-dashoffset="6.38"/>
<circle cx="26" cy="26" r="9.5" stroke="#3CCFC1" stroke-width="2"/></g>
<circle cx="14.69" cy="14.69" r="4.8" fill="#F2606F"/></svg>"""

OCEANO, ESPUMA, CORAL, LAGOA, TINTA_SUAVE, LINHA = "#0B3340", "#EFF5F4", "#F2606F", "#1FA89C", "#4D6670", "#D3E0DE"


ESTILO = """
    #topo { background: #0B3340; }
    #topo QLabel#marca { color: #EFF5F4; font-size: 18px; font-weight: bold; }
    #topo QPushButton#tema { background: transparent; color: #9DB6BA; border: none;
                             padding: 6px 12px; font-size: 14px; font-weight: 600; border-radius: 4px; }
    #topo QPushButton#tema:hover { color: #EFF5F4; }
    #topo QPushButton#tema:checked { color: #EFF5F4; background: #164556; }
    #topo QPushButton#tutor { background: transparent; color: #9DB6BA; border: 1px solid #5F8590;
                              border-radius: 4px; padding: 5px 14px; }
    #topo QPushButton#tutor:hover { color: #EFF5F4; border-color: #9DB6BA; }
    #topo QPushButton#tutor:checked { background: #F2606F; color: #041820; border-color: #F2606F; font-weight: bold; }
    #topo QLabel#aviso { color: #9DB6BA; }
    #menuTema { background: #FFFFFF; border: 1px solid #D3E0DE; border-radius: 8px; }
    #menuTema QLabel#menuTitulo { color: #4D6670; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
    #menuTema QPushButton#opcaoRoteiro { background: #FFFFFF; color: #0B3340; border: 1px solid #D3E0DE;
                                         border-radius: 6px; padding: 8px 12px; text-align: left; min-width: 300px; }
    #menuTema QPushButton#opcaoRoteiro:hover { border-color: #1FA89C; background: #EFF5F4; }
    #menuTema QPushButton#opcaoRoteiro:disabled { color: #9DB6BA; border-style: dashed; }
    #menuTema QPushButton#sairTutor { background: transparent; color: #C2364A; border: none; padding: 4px;
                                      text-align: left; font-weight: bold; }
    #lateral QLabel#dicaTutor { color: #9DB6BA; font-size: 11px; padding-left: 42px; }
    #menuTema QPushButton#acao { background: #F2606F; color: #041820; border: none; border-radius: 4px;
                                 padding: 6px 14px; font-weight: bold; }
    #lateral QLabel#introTutor { color: #9DB6BA; font-size: 12px; padding: 4px 16px 10px 16px; }
    #passoTutor { border-top: 1px solid #164556; }
    #passoTutor[proximo="true"] { background: #164556; border-left: 3px solid #F2606F; }
    #lateral QLabel#numeroTutor { background: #164556; color: #9DB6BA; border-radius: 10px;
                                  font-size: 11px; font-weight: bold; }
    #passoTutor[proximo="true"] QLabel#numeroTutor { background: #F2606F; color: #041820; }
    #lateral QLabel#tagTutor { color: #F2606F; font-size: 16px; font-weight: bold; }
    #rolagemLateral QScrollBar:vertical { background: #0B3340; width: 8px; }
    #rolagemLateral QScrollBar::handle:vertical { background: #164556; border-radius: 4px; min-height: 24px; }
    #rolagemLateral QScrollBar::add-line, #rolagemLateral QScrollBar::sub-line { height: 0; }
    #cartaoAjuda { background: #FFFFFF; border: 1px solid #9DB6BA; border-radius: 8px; }
    #cartaoAjuda QTextBrowser { background: #FFFFFF; }
    #lateral, #rolagemLateral, #conteudoLateral { background: #0B3340; }
    #lateral QLabel, #lateral QCheckBox { color: #EFF5F4; }
    #lateral QLabel#arquivo { color: #9DB6BA; padding: 12px 16px 4px 16px; }
    #lateral QLabel#vazio { color: #9DB6BA; padding: 16px; }
    #painel { border-top: 1px solid #164556; }
    #painel QLabel#painelTitulo { font-size: 15px; font-weight: bold; }
    #painel QLabel#painelExplicacao { color: #9DB6BA; font-size: 12px; }
    #painel QLabel#destaque { font-size: 15px; font-weight: bold; padding-top: 4px; }
    #lateral QPushButton#secundario { background: transparent; color: #EFF5F4;
                                      border: 1px solid #9DB6BA; border-radius: 4px; padding: 6px; }
    #visor   { background: #808080; }
    #rolagem, #rolagem > QWidget > QWidget { background: #808080; }
    #barraZoom { background: #EFF5F4; border-top: 1px solid #D3E0DE; }
    #barraZoom QLabel { color: #0B3340; }
    #barraZoom QLabel#dica { color: #4D6670; }
    #barraZoom QPushButton { background: #FFFFFF; color: #0B3340; border: 1px solid #74898F;
                             border-radius: 4px; padding: 3px 10px; min-width: 24px; }
    #resultados { background: #EFF5F4; }
    #resultados QLabel { color: #0B3340; }
    #cartao { background: #FFFFFF; border: 1px solid #D3E0DE; border-radius: 8px; padding: 8px; }
    #cartaoRotulo { color: #4D6670; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
    #cartaoValor { font-size: 28px; font-weight: bold; }
    #cartaoDetalhe { color: #4D6670; font-size: 12px; }
    QTableWidget#tabelaArtigo { background: #FFFFFF; color: #000000; border: none;
                                border-top: 2px solid #000000; border-bottom: 2px solid #000000;
                                selection-background-color: #F2606F; selection-color: #041820; }
    QTableWidget#tabelaArtigo QHeaderView::section { background: #FFFFFF; color: #000000; border: none;
                                border-bottom: 1px solid #000000; padding: 4px; font-weight: bold; }
    #resultados QPushButton#salvarGrafico { background: transparent; color: #0B3340; border: 1px solid #74898F;
                                            border-radius: 4px; padding: 3px 10px; }
    #resultados QPushButton#exportar { background: #F2606F; color: #041820; border: none;
                                       border-radius: 4px; padding: 8px; font-weight: bold; }
    #resultados QPushButton#exportar:disabled { background: #D3E0DE; color: #74898F; }
"""
