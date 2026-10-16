# Ferramentas

Cada ferramenta tem uma chave (o nome interno usado em `TEMAS`, `PRECISA`, `AJUDA` e nos painéis).
As fórmulas completas, com figuras, estão nos cartões de ajuda (`atol/ajuda/`).

## Imagem

### Calibrar escala — chave `escala`
- Classe: `nucleo.Calibracao` (não é um passo).
- Dois cliques sobre algo de tamanho conhecido: $s = d_{px}/d_{real}$; comprimentos ÷ s, áreas ÷ s².
- Desligar a chave mede em px, mas guarda a escala.

### Medir distância e ângulo — chave `medir`
- Funções: `comprimento_px`, `angulo_linha` (atan2(−Δy, Δx), de −180° a 180°, anti-horário), `angulo_entre` (0° a 90°).
- Mede várias linhas seguidas até apertar Esc; apagar a selecionada, a última ou todas.
- **Dureza Vickers** no mesmo painel: as 2 últimas linhas são as diagonais; `dureza_vickers(F, d1, d2)`,
  $HV = 2F\sin(68°)/d^2 \approx 1{,}8544\,F/d^2$ (F em kgf, d em mm). Avisa se as diagonais diferem > 5%
  ou não são perpendiculares. Erro: $\Delta HV/HV \approx 2\,\Delta d/d$.
- Validação: HV10 com d = 0,293 mm → 216,0 HV (teste `test_vickers`).

## Ajustar

### Remover ruído (mediana) — chave `mediana`
- Classe: `FiltroMediana(raio=2)`. Janela em disco (como o Median do Fiji); colorida: canal por canal.
- Remove ruído sal e pimenta sem mover bordas. Raio: maior que o ruído, menor que o menor objeto
  (objeto com menos da metade da janela some).

### Corrigir iluminação do fundo — chave `fundo`
- Classe: `CorrigirFundo(raio=40, objetos_claros=True)`. Rolling ball de Sternberg (1983):
  $I_{corr} = I - F$, com F = abertura morfológica com bola de raio r.
- Raio: maior que o maior objeto, menor que a mancha de luz. Objetos escuros: inverte, corrige, desinverte.

### Ajustar contraste — chave `contraste`
- Classe: `AjustarContraste(fator=1.0)`. $I' = \min(255, \max(0, f \cdot I))$, calculado em float.

## Analisar

### Separar do fundo — chave `limiar`
- Classe: `Limiarizar(metodo="IsoData", objetos_claros=True)`. IsoData (Ridler e Calvard, 1978) ou Otsu (1979).
- Saída: objeto = 255, fundo = 0, sempre (mesmo com objetos escuros). Guarda `ultimo_T`,
  `fracao_area` e `ultima_mascara` (usada pelo tamanho de grão).
- Validação: mesmo limiar e mesma contagem do ImageJ (coins 96, Blobs 64).

### Separar objetos encostados — chave `watershed`
- Classe: `SepararEncostados(tolerancia=0.7, preencher_buracos=False)`.
- Transformada de distância → h-máximos (proeminência ≥ h) como sementes → watershed em −D →
  linha de corte de 1 px (feita à mão: `watershed_line=True` com vizinhança-8 é ~35 s).
- h = 0,7 reproduz o Binary › Watershed do ImageJ (Blobs: 64 → 68, mesmos cortes).
- Supersegmentação: aumentar a tolerância; buracos internos: "Preencher buracos".

### Tamanho de grão (intercepto) — chave `grao`
- Funções: `medir_intercepto(grao, n_linhas)`, `numero_astm(l_mm)`.
- n linhas horizontais e n verticais; cada linha vale só entre o 1º e o último contorno cruzado.
  $\bar\ell = L/P$; $G = -6{,}6439\log_{10}\bar\ell - 3{,}288$ (ℓ̄ em mm); alongamento = ℓ̄h/ℓ̄v.
- Precisa da escala para G. Exige correção de fundo em imagens com luz desigual.
- Validação: listras (ℓ̄ exato), tabela da ASTM E112, grãos laminados sintéticos (erro 3–7%).

### Contar objetos — chave `contar`
- Classe: `ContarObjetos(area_minima=0, excluir_borda=False)`. Componentes conexos, vizinhança-8.

## Resultados

- **Mostrar diâmetro** (`diametro`): $d = 2\sqrt{A/\pi}$ no centroide; com > 60 objetos, só o sob o mouse.
- **Tabela de resultados** (`tabela`): janela própria com
  - cartão média ± desvio (amostral, n − 1) do diâmetro;
  - cartão fração de área $f_A = A_{obj}/A_{total}$ (inclui objetos na borda; princípio de Delesse);
  - histograma do diâmetro (Sturges, $k = \lceil\log_2 n\rceil + 1$), SciencePlots, botão "Salvar gráfico…"
    (PNG 600 dpi, PDF, SVG; 1 coluna de artigo);
  - tabela por objeto: área, perímetro (traçado do ImageJ), diâmetro, circularidade $4\pi A/P^2$ (≤ 1), X, Y;
  - exportar Excel (abas Objetos e Resumo, com fórmulas).

## Tutor

Menu com roteiros (`tutor/roteiros.py`). Escolhido um, a lateral mostra só os passos dele, numerados,
com uma dica por passo; o próximo sugerido é destacado (a ordem é sugerida, não obrigatória).

| Roteiro | Passos |
|---|---|
| Porosidade e fração de fases | escala, mediana, fundo, contraste, limiar, tabela |
| Tamanho e forma de partículas | escala, mediana, fundo, contraste, limiar, watershed, contar, diâmetro, tabela |
| Tamanho de grão (ASTM E112) | escala, mediana, fundo, contraste, limiar, grão |
| Dureza Vickers | escala, medir |
| Contagem de células | escala, mediana, fundo, limiar, watershed, contar, diâmetro, tabela |
