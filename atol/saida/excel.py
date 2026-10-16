"""
Exportar para Excel
===================

Gera uma planilha com duas abas:
    Objetos: uma linha por objeto (área, perímetro, diâmetro, circularidade, X, Y)
    Resumo:  imagem, escala, contagem, médias e fração de área

O Resumo usa fórmulas do Excel (=AVERAGE, =STDEV), para quem abrir conferir as contas.
"""


def exportar_excel(caminho: str, medidas: list, calibracao, origem: str, fracao=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    u = calibracao.unidade
    livro = Workbook()
    folha = livro.active
    folha.title = "Objetos"
    cab = ["Objeto", f"Área ({u}²)", f"Perímetro ({u})", f"Diâmetro equivalente ({u})",
           "Circularidade", f"X ({u})", f"Y ({u})"]
    folha.append(cab)
    from openpyxl.styles import Border, Side
    grossa, fina = Side(style="medium"), Side(style="thin")
    for c in folha[1]:                         # estilo de artigo: linha grossa em cima, fina embaixo do cabeçalho
        c.font = Font(bold=True)
        c.border = Border(top=grossa, bottom=fina)
    for m in medidas:
        folha.append([m["rotulo"], m["area"], m["perimetro"], m["diametro"],
                      m["circularidade"], m["x"], m["y"]])
    if medidas:                                # linha grossa embaixo da última linha
        for c in folha[len(medidas) + 1]:
            c.border = Border(bottom=grossa)
    for coluna in "BCDFG":
        for celula in folha[coluna][1:]:
            celula.number_format = "0.000"
    folha["E1"].number_format = "General"
    n = len(medidas) + 1
    resumo = livro.create_sheet("Resumo")
    resumo.append(["Imagem", origem])
    resumo.append(["Escala", calibracao.texto().replace("Escala: ", "")])
    resumo.append(["Objetos", f"=COUNT(Objetos!A2:A{n})"])
    resumo.append([f"Diâmetro médio ({u})", f"=AVERAGE(Objetos!D2:D{n})"])
    resumo.append([f"Desvio padrão do diâmetro ({u})", f"=STDEV(Objetos!D2:D{n})"])
    resumo.append([f"Área média ({u}²)", f"=AVERAGE(Objetos!B2:B{n})"])
    if fracao is not None:
        resumo.append(["Fração de área (%)", round(fracao, 3)])
    for linha in resumo.iter_rows(min_row=4, max_row=6, min_col=2, max_col=2):
        linha[0].number_format = "0.000"
    resumo.column_dimensions["A"].width = 32
    folha.column_dimensions["D"].width = 26
    livro.save(caminho)

# ---------------------------------------------------------
# Em palavras simples (1):
#   A tabela segue o estilo de artigo científico: sem grade, só uma linha
#   grossa em cima, uma fina embaixo do cabeçalho e uma grossa no fim. O
#   resumo não traz números "colados": ele calcula média e desvio com
#   fórmulas do próprio Excel, então qualquer pessoa pode conferir.
# ---------------------------------------------------------
