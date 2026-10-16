# Validação do Atol contra o ImageJ

**Referência:** ImageJ 1.54p (o mesmo motor do Fiji instalado), rodado sem janela pelo `Validar.java`.
**Imagem:** `coins.tif` (moedas do scikit-image, 384 × 303, 8 bits).
**Fluxo igual nos dois:** limiar automático (ImageJ "Default" × Atol IsoData), objetos claros, Analyze Particles com tamanho 0–∞, sem excluir borda, sem correção de fundo.

| Medida | ImageJ | Atol | Concordância |
|---|---|---|---|
| Limiar | pixels ≥ 108 | pixels > 107,02 | mesmos pixels |
| Contagem | 96 | 96 | idêntica |
| Centroide | — | — | diferença máxima 0,001 px |
| Área | — | — | idêntica nos 96 objetos |
| Perímetro (objetos ≥ 200 px²) | — | — | diferença média −0,02% (máx. 0,40%) |
| Circularidade (objetos ≥ 200 px²) | — | — | diferença média +0,03% |

**Perímetro:** na primeira rodada, com o estimador do scikit-image, a diferença chegava a ±5% nas moedas e a 100% nos objetos de 1–2 pixels (o scikit-image dá perímetro 0 para eles). O Atol passou a usar o mesmo algoritmo do ImageJ (contorno traçado pelas bordas dos pixels, descontando 2 − √2 por canto). Depois disso, 93 de 96 objetos têm perímetro idêntico; os outros 3 diferem em exatamente um canto (0,586 px), por causa do ponto onde o traçado começa.

## Blobs (amostra oficial do Fiji)

**Imagem:** `blobs.tif` (256 × 254, 8 bits, tabela de cores invertida: as manchas têm valor alto e aparecem escuras no Fiji). No Atol: "Objetos mais claros que o fundo" marcado, porque o Atol lê os valores dos pixels, não a tabela de cores.

| Medida | ImageJ (Default) | Atol (IsoData) | Concordância |
|---|---|---|---|
| Limiar | pixels ≥ 126 | pixels > 125,30 | mesmos pixels |
| Contagem | 64 | 64 | idêntica |
| Área média | 347,55 px² | 347,55 px² | idêntica (64 de 64 objetos iguais) |
| Centroide | — | — | diferença máxima 0,001 px |
| Perímetro | — | — | 49 de 64 idênticos; os demais diferem em um canto (0,586 px); média −0,16% |
| Circularidade | — | — | diferença média +0,33% (máx. 0,023) |

Com Otsu, o Atol escolhe limiar 120 e também encontra 64 objetos.

**Pendente:** repetir com a correção de fundo ligada (o "Subtract Background" do ImageJ reduz a imagem antes de rolar a bola, então diferenças pequenas são esperadas).

## Watershed (13/10/2026)

Mesma máscara binária (saída do "Separar do fundo" do Atol, IsoData) entregue aos dois programas.
ImageJ 1.54p: `EDM.toWatershed` (= Process › Binary › Watershed), script `WS.java`.
Atol: `SepararEncostados` (transformada de distância + h-máximos + watershed), tolerância h = 0,7.

| Imagem | Manchas antes | ImageJ | Atol | Manchas cortadas de forma diferente |
|---|---|---|---|---|
| Blobs | 64 | 68 | 68 | 0 de 64 |
| coins | 96 | 189 | 189 | 13 de 96 |

- Blobs: os mesmos 4 cortes nos mesmos objetos.
- coins: a máscara tem muitos buracos dentro das moedas, e os dois programas supersegmentam igualmente (189 pedaços); as diferenças ficam nessas regiões ruidosas. Com "Preencher buracos" o Atol dá 104.
- h = 0,7 foi escolhido por varredura (0,5 a 0,9) porque reproduz o ImageJ, que usa tolerância nominal 0,5 com correção de altura dos picos do EDM.
- Arquivos: `mask_*.tif` (entrada), `ws_imagej_*.tif` (saída do ImageJ), `WS.java`.

## Tamanho de grão — intercepto (13/10/2026)

O ImageJ não tem um comando pronto de intercepto, então a validação foi contra valores conhecidos:

| Teste | Esperado | Atol |
|---|---|---|
| Listras com período 20 px (contorno de 1 px) | ℓ̄ = 20 px | 20,0 px |
| Listras com período 13 px (contorno de 2 px) | ℓ̄ = 13 px | 13,0 px |
| Fórmula G (tabela ASTM E112): ℓ̄ = 0,320 / 0,020 / 0,010 mm | G = 0 / 8 / 10 | 0,0 / 8,0 / 10,0 |
| Voronoi esticado 3× (desenho limpo) | razão ≈ 3 | 2,94 |
| `graos_laminados_sinteticos.tif` (ruído + luz desigual), verdade no desenho limpo: ℓ̄h = 62,9 px, ℓ̄v = 25,5 px, razão 2,47 | — | sem correção de fundo: 48,6 / 29,5 / 1,65 (erra); com mediana r = 2 + fundo r = 30–80: 62,8–64,8 / 26,8–27,3 / 2,34–2,38 |

- Conclusão: a correção de fundo é obrigatória nesse tipo de imagem; com ela o erro fica em ~3–7%.
- Cada linha vale só entre o 1º e o último contorno cruzado, para que os grãos cortados pela borda não distorçam ℓ̄.
