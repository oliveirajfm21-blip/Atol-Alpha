# Arquitetura do Atol

## A regra principal: as dependências só descem

```
interface  ──►  tutor, saida  ──►  nucleo
 (PySide6)      (dados, Excel,      (NumPy, SciPy,
                 matplotlib)         scikit-image)
```

- `nucleo` **não importa nada** do Atol nem de Qt. Pode ser testado sem abrir janela e reaproveitado
  numa versão web, num script de lote ou num add-on.
- `saida` e `tutor` só conhecem o `nucleo`.
- `interface` conhece todos, e ninguém conhece a `interface`.

Consequência prática: trocar a interface inteira (por exemplo, por uma versão web) reaproveita
`nucleo`, `saida`, `tutor` e as imagens da `ajuda` sem mudar uma linha.

## Módulos

| Pasta / arquivo | Responsabilidade |
|---|---|
| `main.py` | Cria o `QApplication` e abre a `JanelaAtol`. Nada mais. |
| `atol/nucleo/passos.py` | Classe-base `Passo` e os passos da linha do tempo: `FiltroMediana`, `CorrigirFundo`, `AjustarContraste`, `Limiarizar`, `SepararEncostados`, `ContarObjetos`. |
| `atol/nucleo/medidas.py` | Medidas sobre resultados: `medir_objetos` (área, perímetro traçado do ImageJ, diâmetro, circularidade), `medir_intercepto` e `numero_astm` (grão), `angulo_linha`, `angulo_entre`, `dureza_vickers`, `classes_sturges`. |
| `atol/nucleo/imagem.py` | `carregar_imagem` (qualquer formato → uint8) e `aplicar_linha_do_tempo`. |
| `atol/nucleo/calibracao.py` | `Calibracao`: escala px/unidade; converte comprimentos (L/s) e áreas (A/s²). |
| `atol/saida/excel.py` | `exportar_excel`: abas Objetos e Resumo, tabela no estilo de artigo. |
| `atol/saida/graficos.py` | `figura_histograma` no estilo SciencePlots (`science` + `no-latex`). |
| `atol/tutor/roteiros.py` | `TEMAS` (menus), `PRECISA` (dependências), `ROTEIRO` (ordem) e `ROTEIROS` (análises guiadas). Só dados. |
| `atol/interface/janela.py` | `JanelaAtol`: barra de temas, menus, Tutor, lateral com painéis, ligação chave → passo, `renderizar`. |
| `atol/interface/visor.py` | `Visor`: mostra a imagem, zoom, arrastar, cliques de linha (calibrar/medir) e camadas desenhadas por cima. `DialogoEscala`. |
| `atol/interface/resultados.py` | `JanelaResultados` (cartões, tabela) e `Histograma` (matplotlib embutido). |
| `atol/interface/componentes.py` | Peças reutilizáveis: `Chave`, `Painel`, `MenuTema`, `CartaoAjuda`, `numpy_para_pixmap`. |
| `atol/interface/estilo.py` | Paleta, símbolo SVG e a folha de estilo (QSS). |
| `atol/ajuda/` | `AJUDA` (HTML dos cartões, uma entrada por chave), `imagens/` e `gerar.py`. |

## Fluxo de dados

```
imagem original (nunca é alterada)
   │
   ▼  aplicar_linha_do_tempo: só os passos com ativo = True, nesta ordem
Mediana → Fundo → Contraste → Separar do fundo → Separar encostados → Contar
   │
   ├──► Visor (o que aparece na tela)
   ├──► medidas: medir_objetos, intercepto, fração de área (a partir da máscara do limiar)
   └──► Resultados, Excel, gráfico
```

Três ideias que sustentam isso:

1. **A linha do tempo sempre recalcula a partir da original.** Desligar um passo é só pular ele;
   nada se perde (por exemplo, tons que saturaram no contraste).
2. **A calibração não é um passo.** Ela não muda pixels, só como as medidas são lidas.
   Mudar a escala recalcula todas as medidas.
3. **Camadas de visualização não mudam pixels nem medidas.** Etiquetas de diâmetro, contorno
   destacado, linhas de medida e linhas de teste do grão são desenhadas por cima, no `Visor`.

## Como a interface liga uma chave a um passo

1. `TEMAS` (em `tutor/roteiros.py`) define a chave e o texto que aparece no menu.
2. `JanelaAtol.criar_menus` cria uma `Chave` por item; ligar chama `ao_alternar(chave, ligado)`.
3. `ao_alternar` aplica `PRECISA` (liga o que é pré-requisito, desliga os dependentes), muda
   `passo.ativo` e chama `renderizar`.
4. `renderizar` roda a linha do tempo, atualiza visor, medidas, tabela, grão e medições.
5. O painel da lateral (`self.paineis[chave]`) aparece só quando a chave está ligada.

## Desempenho

- `FiltroMediana` e `CorrigirFundo` guardam o último resultado (cache por hash da imagem + parâmetros),
  porque são os passos lentos. O rolling ball leva ~1 s na primeira vez e é instantâneo depois.
- Os demais passos levam menos de 0,2 s numa imagem de 384×303 px.
