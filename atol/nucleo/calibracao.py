"""
Calibração
==========

Escala da imagem: quantos pixels valem uma unidade real (mm, µm...).

    s = d_px / d_real          L_real = L_px / s          A_real = A_px / s²
"""


class Calibracao:
    """Escala da imagem. Não é um Passo: não muda nenhum pixel, só como as medidas são lidas."""

    def __init__(self):
        self.px_por_unidade = None     # s, em pixels por unidade; None = não calibrada
        self._unidade = "px"
        self.ativa = True              # desligada: mede em px, mas guarda a escala

    @property
    def calibrada(self) -> bool:
        return self.px_por_unidade is not None and self.ativa

    @property
    def unidade(self) -> str:
        return self._unidade if self.calibrada else "px"

    def definir(self, d_px: float, d_real: float, unidade: str):
        self.px_por_unidade = d_px / d_real          # s = d_px / d_real
        self._unidade = unidade

    def comprimento(self, valor_px: float) -> float:
        return valor_px / self.px_por_unidade if self.calibrada else valor_px        # L / s

    def area(self, valor_px2: float) -> float:
        return valor_px2 / self.px_por_unidade ** 2 if self.calibrada else valor_px2  # A / s²

    def texto(self) -> str:
        if self.px_por_unidade is None:
            return "Escala: não calibrada (px)"
        return f"Escala: {self.px_por_unidade:.3f} px/{self._unidade}".replace(".", ",")

# ---------------------------------------------------------
# Em palavras simples (1):
#   O usuário clica nas duas pontas de algo de tamanho conhecido (uma
#   régua, a barra de escala do microscópio) e digita quanto aquilo mede.
#   Comprimentos são divididos pela escala s, e áreas por s², porque área
#   é comprimento vezes comprimento. A calibração não é um passo: não muda
#   nenhum pixel, só como os números são lidos. Por isso, calibrar depois
#   de medir recalcula todas as medidas.
# ---------------------------------------------------------
