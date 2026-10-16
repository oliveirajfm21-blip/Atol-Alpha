"""
Roteiros do Tutor
=================

Dados (não código) que organizam a interface:
    1. TEMAS e PRECISA: menus da barra de cima e dependências entre ferramentas
    2. ROTEIRO e ROTEIROS: ordem dos passos e as análises guiadas do Tutor

Por serem só dados, um pacote futuro (Atol Material, Atol Life) pode trazer os próprios roteiros.
"""

# =========================================================
# 1. Menus e dependências
# =========================================================
TEMAS = {
    "Imagem": [("escala", "Calibrar escala"), ("medir", "Medir distância e ângulo")],
    "Ajustar": [("mediana", "Remover ruído (mediana)"), ("fundo", "Corrigir iluminação do fundo"), ("contraste", "Ajustar contraste")],
    "Analisar": [("limiar", "Separar do fundo"), ("watershed", "Separar objetos encostados"), ("grao", "Tamanho de grão (intercepto)"), ("contar", "Contar objetos")],
    "Resultados": [("diametro", "Mostrar diâmetro na imagem"), ("tabela", "Tabela de resultados")],
}
# quem precisa de quem (ligar o de cima liga também o de baixo)
PRECISA = {"grao": "limiar", "watershed": "limiar", "contar": "limiar", "diametro": "contar", "tabela": "contar"}

# ---------------------------------------------------------
# Em palavras simples (1):
#   Cada ferramenta tem uma chave curta ("limiar", "contar"...) usada em
#   todo o programa. TEMAS diz em qual menu ela aparece. PRECISA diz quem
#   depende de quem: ligar "Contar" liga "Separar do fundo" sozinho, porque
#   não dá para contar objetos numa imagem que ainda não foi separada.
# ---------------------------------------------------------


# =========================================================
# 2. Roteiros do Tutor
# =========================================================

# ordem do roteiro do Tutor = ordem em que a imagem é processada
ROTEIRO = ["escala", "medir", "mediana", "fundo", "contraste", "limiar", "watershed", "grao", "contar", "diametro", "tabela"]

# Roteiros do Tutor: cada um escolhe quais passos aparecem e dá uma dica por passo.
# Ficam como dados para que, no futuro, cada pacote traga os próprios roteiros.
ROTEIROS = {
    "Porosidade e fração de fases": {
        "descricao": "Quanto da amostra é poro, inclusão ou uma fase (ex.: ferrita × perlita).",
        "passos": {
            "escala": "Use a barra de escala da micrografia.",
            "mediana": "Raio 1 ou 2 tira o ruído e os riscos finos do polimento.",
            "fundo": "Corrige a luz desigual do microscópio.",
            "contraste": "Só se a fase de interesse estiver apagada.",
            "limiar": "Escolha a fase de interesse: poros e inclusões costumam ser escuros.",
            "tabela": "O número principal é a fração de área (ASTM E562 faz o mesmo por contagem de pontos).",
        },
    },
    "Tamanho e forma de partículas": {
        "descricao": "Inclusões, pós, precipitados ou alvéolos (dimples) de fratura.",
        "passos": {
            "escala": "Use a barra de escala (µm).",
            "mediana": "Raio 1 ou 2 tira o ruído.",
            "fundo": "Corrige a luz desigual.",
            "contraste": "Só se as partículas estiverem apagadas.",
            "limiar": "Confira se as partículas ficaram brancas por inteiro.",
            "watershed": "Partículas encostadas viram uma só sem este passo.",
            "contar": "Ignore pontinhos de ruído e exclua as cortadas pela borda.",
            "diametro": "",
            "tabela": "Veja o histograma de tamanhos e a circularidade.",
        },
    },
    "Tamanho de grão (ASTM E112)": {
        "descricao": "Tamanho médio do grão de um metal pelo método do intercepto.",
        "passos": {
            "escala": "Obrigatório: o número G da norma precisa do tamanho em mm.",
            "mediana": "Raio 1 ou 2 tira o ruído sem apagar os contornos finos.",
            "fundo": "Raio maior que o maior grão.",
            "contraste": "Só se os contornos estiverem fracos.",
            "limiar": "Os grãos devem ficar brancos e os contornos pretos.",
            "grao": "Laminado? Compare o intercepto horizontal e o vertical.",
        },
    },
    "Dureza Vickers": {
        "descricao": "Medir as diagonais da marca do ensaio e calcular HV.",
        "passos": {
            "escala": "Obrigatório: calibre com a barra de escala do microscópio.",
            "medir": "Dê zoom e meça as duas diagonais da marca, uma de cada vez. "
                     "Escolha a carga usada no ensaio.",
        },
    },
    "Contagem de células": {
        "descricao": "Contar e medir células numa imagem de microscópio.",
        "passos": {
            "escala": "Use a barra de escala do microscópio (µm).",
            "mediana": "Raio 1 ou 2 tira o ruído da câmera.",
            "fundo": "A luz do microscópio quase nunca é uniforme.",
            "limiar": "Desmarque \"objetos claros\" se as células forem mais escuras que o fundo.",
            "watershed": "Células costumam se encostar.",
            "contar": "Ignore detritos pequenos e exclua as cortadas pela borda.",
            "diametro": "",
            "tabela": "",
        },
    },
}

# ---------------------------------------------------------
# Em palavras simples (2):
#   Um roteiro é uma receita para um objetivo: medir porosidade, tamanho
#   de grão, dureza... O Tutor mostra na lateral só os passos daquela
#   receita, na ordem, com uma dica em cada um, e destaca o próximo. A
#   ordem é sugerida, não obrigatória: pular passos é normal (uma imagem
#   sem ruído não precisa de mediana).
# ---------------------------------------------------------
