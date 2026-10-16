"""Saída de dados: Excel e gráficos no padrão de artigo."""
from .excel import exportar_excel
from .graficos import ESTILO_GRAFICO, figura_histograma

__all__ = ["exportar_excel", "ESTILO_GRAFICO", "figura_histograma"]
