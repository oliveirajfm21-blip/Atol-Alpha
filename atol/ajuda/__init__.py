"""Textos dos cartões de ajuda do Atol.

Cada cartão: nome da técnica, o que ela faz, o que acontece por trás (passos,
fórmulas e figuras da pasta "ajuda") e a referência. As fórmulas e figuras são
PNG gerados por gerar.py (python -m atol.ajuda.gerar).
"""


import struct
from pathlib import Path

PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens"   # PNG gerados por gerar.py
_PASTA = PASTA_IMAGENS


def _largura_png(arquivo: Path) -> int:
    """Lê a largura direto do cabeçalho do PNG (bytes 16 a 20)."""
    try:
        with open(arquivo, "rb") as f:
            return struct.unpack(">I", f.read(24)[16:20])[0]
    except OSError:
        return 300


def _formula(nome: str, legenda: str) -> str:
    largura = min(round(_largura_png(_PASTA / f"f_{nome}.png") * 0.72), 340)   # cabe no cartão
    return (f'<p align="center"><img src="f_{nome}.png" width="{largura}"></p>'
            f'<p class="legenda">{legenda}</p>')


def _figura(nome: str, legenda: str) -> str:
    return (f'<p align="center"><img src="g_{nome}.png" width="340"></p>'
            f'<p class="legenda">{legenda}</p>')


CSS = """
h2 { color: #0B3340; font-size: 16px; margin: 0; }
p.tecnica { color: #C2364A; font-size: 11px; font-weight: bold; margin-top: 2px; }
p { color: #0B3340; font-size: 12px; line-height: 140%; }
h4 { color: #4D6670; font-size: 11px; margin-top: 12px; margin-bottom: 2px; }
p.legenda { color: #4D6670; font-size: 11px; font-style: italic; }
p.fonte { color: #4D6670; font-size: 10px; }
"""

AJUDA = {

"escala": f"""
<h2>Calibrar escala</h2>
<p class="tecnica">CALIBRAÇÃO ESPACIAL · "SET SCALE" NO FIJI</p>
<p>Ensina ao Atol quanto vale um pixel no mundo real, para as medidas saírem em mm, µm ou cm.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>1. Você clica nas duas pontas de algo com tamanho conhecido. O comprimento da linha sai de Pitágoras:</p>
{_formula("escala_pitagoras", "(x₁, y₁) e (x₂, y₂) são os dois cliques, em pixels da imagem.")}
<p>2. Você digita o tamanho real, e o Atol calcula a escala:</p>
{_formula("escala_s", "s é a escala em pixels por unidade (por exemplo, px/mm).")}
<p>3. Comprimentos são divididos por s, e áreas por s², porque área é comprimento × comprimento (a razão de semelhança k ao quadrado):</p>
{_formula("escala_conv", "L é qualquer comprimento (perímetro, diâmetro, posição); A é a área.")}
<p>A circularidade não muda com a escala: o s² aparece em cima e embaixo e se cancela.</p>
<h4>PRECISÃO</h4>
<p>Um clique erra cerca de 1/z pixel, onde z é o zoom. O erro relativo da escala fica aproximadamente:</p>
{_formula("escala_erro", "Δs/s é o erro relativo da escala; z é o zoom; d_px é o comprimento da linha.")}
<p>Por isso: use uma referência longa e dê zoom antes de clicar nas pontas.</p>
<p class="fonte">Desligar a chave volta a medir em pixels, mas guarda a escala.</p>
""",

"medir": f"""
<h2>Medir distância e ângulo</h2>
<p class="tecnica">FERRAMENTA DE LINHA · "STRAIGHT LINE" + "MEASURE" NO FIJI</p>
<p>Mede comprimentos (diagonal de uma indentação, espessura de revestimento, trinca) e ângulos.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p><b>Comprimento</b>: Pitágoras nos dois cliques, dividido pela escala:</p>
{_formula("medir_d", "(x₁, y₁) e (x₂, y₂) são os cliques em pixels; s é a escala em px por unidade.")}
<p><b>Ângulo com a horizontal</b>: a tangente do ângulo é Δy/Δx, mas dividir quebraria numa linha vertical (Δx = 0). Por isso o Atol usa o atan2, que recebe Δy e Δx separados e sabe o quadrante:</p>
{_formula("medir_ang", "Δx = x₂ − x₁ e Δy = y₂ − y₁. O sinal de menos existe porque o eixo y da imagem cresce para baixo.")}
<p>O resultado vai de −180° a 180°, crescendo no sentido anti-horário, como na matemática da escola.</p>
<p><b>Ângulo entre duas linhas</b>: a diferença entre os dois ângulos, reduzida ao menor ângulo (0° a 90°).</p>
<h4>DUREZA VICKERS</h4>
<p>Meça as duas diagonais da marca da pirâmide de diamante. As duas últimas linhas viram d₁ e d₂:</p>
{_formula("hv", "F é a carga em kgf; d é a média das diagonais em mm; 136° é o ângulo entre as faces opostas da pirâmide.")}
<p>Marca maior = metal mais mole. Como d aparece ao quadrado, o erro na diagonal dobra na dureza:</p>
{_formula("hv_erro", "Errar 5% na diagonal dá cerca de 10% de erro em HV: dê zoom antes de clicar.")}
<p class="fonte">Os valores são recalculados quando a escala muda. Um clique erra cerca de 1/z pixel (z = zoom): dê zoom antes de medir.</p>
""",

"fundo": f"""
<h2>Corrigir iluminação do fundo</h2>
<p class="tecnica">SUBTRAÇÃO DE FUNDO POR ROLLING BALL · STERNBERG (1983)</p>
<p>Remove variações lentas de luz, como um canto mais claro, sem apagar os objetos.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>Imagine a imagem como um relevo: pixel claro é morro, pixel escuro é vale. Uma bola de raio r rola por baixo desse relevo. Como ela é maior que os objetos, não entra neles e só acompanha a variação lenta da luz. O caminho do topo da bola é o fundo estimado F, que é subtraído:</p>
{_formula("fundo_sub", "I é a imagem original, F o fundo estimado e I_corr a imagem com o fundo plano.")}
<p>Matematicamente, F é uma abertura morfológica em tons de cinza com uma bola b de raio r (erosão ⊖ seguida de dilatação ⊕). Subtrair a abertura da imagem é a transformada top-hat.</p>
{_formula("fundo_abertura", "b_r é o elemento estruturante: uma bola de raio r.")}
{_figura("fundo", "Uma linha de pixels: a bola pequena entra nas moedas e as apaga (esquerda); a grande só acompanha o fundo (direita).")}
<h4>COMO ESCOLHER O RAIO</h4>
{_formula("fundo_raio", "r abaixo do maior objeto come o miolo dele; acima da mancha de luz, não a remove.")}
<p>Para objetos escuros sobre fundo claro, o Atol inverte a imagem, corrige e desinverte (como o "Light background" do Fiji).</p>
<p class="fonte">Sternberg, S. R. Biomedical Image Processing. IEEE Computer, 16(1), 1983. No Fiji: Process › Subtract Background.</p>
""",

"mediana": f"""
<h2>Remover ruído (mediana)</h2>
<p class="tecnica">FILTRO DE MEDIANA · "PROCESS › FILTERS › MEDIAN" NO FIJI</p>
<p>Tira pontinhos isolados (ruído "sal e pimenta", poeira, pixels mortos) sem borrar as bordas dos objetos.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>Para cada pixel, o Atol pega os vizinhos dentro de um disco de raio r, coloca os brilhos em ordem e fica com o do meio:</p>
{_formula("mediana", "W_r é a janela (disco de raio r) em volta do pixel (x, y); I é o brilho de cada vizinho.")}
<p>A média deixa todo pixel "votar" com o seu valor, então um 255 isolado puxa o resultado e o ruído se espalha. Na mediana, o 255 só vai para o fim da fila e nunca entra na conta.</p>
{_figura("mediana", "Uma borda com um pixel de ruído: a média borra a borda e espalha o ruído; a mediana remove o ruído e mantém a borda.")}
<p>A mediana sempre devolve um valor que já existia na janela, por isso não inventa tons intermediários na borda. Isso importa porque o próximo passo, "Separar do fundo", corta exatamente na borda.</p>
<h4>COMO ESCOLHER O RAIO</h4>
{_formula("mediana_raio", "r deve ser maior que o ruído e menor que o menor objeto que você quer manter.")}
<p>Um objeto que ocupa menos da metade da janela perde a votação e some. Comece com r = 1 ou 2.</p>
<p class="fonte">Em imagens coloridas, cada canal (R, G, B) é filtrado separadamente.</p>
""",

"contraste": f"""
<h2>Ajustar contraste</h2>
<p class="tecnica">AJUSTE LINEAR DE GANHO</p>
<p>Multiplica o brilho de todos os pixels por um fator f. Acima de 1 clareia e afasta os tons; abaixo de 1 escurece.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
{_formula("contraste", "I é o brilho original (0 a 255), f o fator da barra e I' o brilho novo, travado entre 0 e 255.")}
<p>A conta é feita em número decimal (float) e só depois volta para 8 bits. Em 8 bits, 200 × 2 = 400 não cabe e "dá a volta" para 144; por isso o Atol trava em 255 em vez de deixar dar a volta.</p>
{_figura("contraste", "Entrada × saída para três fatores. Com f = 2, tudo acima de 127 vira 255 e se perde.")}
<p>Tons que saturam em 255 não podem ser recuperados. Por isso a linha do tempo sempre recalcula a partir da imagem original.</p>
""",

"limiar": f"""
<h2>Separar do fundo</h2>
<p class="tecnica">LIMIARIZAÇÃO AUTOMÁTICA · ISODATA (RIDLER E CALVARD, 1978) E OTSU (1979)</p>
<p>Decide, pixel a pixel, o que é objeto e o que é fundo, comparando o brilho com uma "nota de corte" T.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
{_formula("limiar_b", "B é a imagem binária: 1 = objeto, 0 = fundo.")}
<p>O difícil é escolher T sozinho. O histograma costuma ter dois morros (fundo e objetos), e T deve cair no vale entre eles.</p>
{_figura("limiar", "Histograma da imagem das moedas e os limiares escolhidos pelos dois métodos.")}
<p><b>IsoData</b>: começa com T = média da imagem, separa os dois grupos e coloca T no meio das duas médias. Repete até T parar de mudar.</p>
{_formula("limiar_iso", "μ_fundo e μ_objeto são as médias de brilho dos pixels abaixo e acima de T_k.")}
<p><b>Otsu</b>: testa todos os T e escolhe o que deixa os dois grupos mais separados (maior variância entre classes).</p>
{_formula("limiar_otsu", "ω₀ e ω₁ são as frações de pixels de cada grupo; μ₀ e μ₁ as médias.")}
<p class="fonte">O método "Default" do ImageJ é uma variação do IsoData; o limiar pode diferir em 1 ou 2 unidades.</p>
""",

"watershed": f"""
<h2>Separar objetos encostados</h2>
<p class="tecnica">WATERSHED NA TRANSFORMADA DE DISTÂNCIA · "PROCESS › BINARY › WATERSHED" NO FIJI</p>
<p>Corta com uma linha fina objetos redondos que se tocam, para que sejam contados e medidos separados.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>1. Para cada pixel branco, o Atol mede a distância até o fundo mais próximo:</p>
{_formula("ws_dist", "p é um pixel do objeto, q percorre os pixels de fundo e ‖p − q‖ é a distância entre eles.")}
<p>O centro de cada objeto vira um morro (máximo de D). O "pescoço" onde dois objetos se tocam vira uma sela, mais baixa.</p>
{_figura("watershed", "Perfil de D ao longo de duas moedas encostadas: dois morros, uma sela e a linha de corte nela.")}
<p>2. Cada morro vira uma semente. Com o relevo de cabeça para baixo (−D), a água sobe a partir das sementes. Onde a água de duas bacias se encontra, levanta-se uma barragem de 1 pixel: essa é a linha de corte.</p>
<p>3. Bordas serrilhadas criam morrinhos falsos, que cortariam um objeto só em dois (supersegmentação). Por isso só valem os picos que se destacam da sela pelo menos h:</p>
{_formula("ws_h", "D_pico é a altura do morro, D_sela a da sela até o vizinho e h a tolerância.")}
<h4>DICAS</h4>
<p>Funciona bem para objetos arredondados. Se uma peça só for cortada, aumente a tolerância. Objetos com buracos por dentro (como as moedas) se cortam demais: marque "Preencher buracos".</p>
<p class="fonte">Com tolerância 0,7, o Atol faz os mesmos cortes que o ImageJ 1.54p nas Blobs (68 objetos).</p>
""",

"grao": f"""
<h2>Tamanho de grão (intercepto)</h2>
<p class="tecnica">MÉTODO DO INTERCEPTO LINEAR DE HEYN · ASTM E112</p>
<p>Mede o tamanho médio dos grãos de um metal. Grão menor costuma significar metal mais resistente (relação de Hall-Petch).</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>1. O Atol traça linhas de teste horizontais e verticais (verde) sobre a imagem já separada: grão branco, contorno preto.</p>
<p>2. Anda pixel a pixel por cada linha e marca (coral) cada vez que ela atravessa um contorno.</p>
<p>3. O intercepto médio é o comprimento de linha dividido pelo número de grãos atravessados:</p>
{_formula("grao_l", "L é o comprimento das linhas entre o 1º e o último contorno cruzado; P é o número de grãos inteiros atravessados.")}
<p>4. A norma converte o intercepto (em mm) no número de tamanho de grão G. G maior = grão menor:</p>
{_formula("grao_G", "ℓ̄ é o intercepto médio em mm. G = 0 corresponde a ℓ̄ ≈ 0,32 mm e G = 8 a ℓ̄ ≈ 0,020 mm.")}
{_figura("grao", "Grãos sintéticos: linhas de teste (verde) e cruzamentos com os contornos (coral).")}
<h4>LAMINAÇÃO: GRÃOS ALONGADOS</h4>
<p>Num material laminado, os grãos se esticam na direção de laminação. Compare o intercepto nas duas direções:</p>
{_formula("grao_aniso", "Perto de 1: grãos equiaxiais. Maior que 1: alongados na horizontal da imagem.")}
<p>Por que funciona mesmo com contornos falhados? Um furo no contorno só atrapalha as poucas linhas que passam exatamente por ele. Já o "Contar objetos" juntaria os dois grãos inteiros.</p>
<p class="fonte">Precisa da escala calibrada para calcular G. Para a medida valer, use linhas suficientes para cruzar pelo menos uns 50 grãos.</p>
""",

"contar": f"""
<h2>Contar objetos</h2>
<p class="tecnica">ROTULAÇÃO DE COMPONENTES CONEXOS</p>
<p>Agrupa os pixels brancos que se encostam e dá um número a cada grupo. Cada grupo é um objeto.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>Funciona como o balde de tinta do Paint: acha um pixel branco ainda sem cor, pinta ele e todos os vizinhos brancos com um número novo e repete até não sobrar pixel branco sem número.</p>
{_figura("contar", "Quem conta como vizinho do pixel central (escuro). O Atol usa vizinhança-8, como o Fiji.")}
<p>Vizinhança-4 tende a contar a mais (quebra objetos finos na diagonal); vizinhança-8 tende a contar a menos (junta objetos que quase se tocam).</p>
<h4>FILTROS</h4>
<p><b>Área mínima</b> descarta pontinhos de ruído (como o campo "Size" do Analyze Particles). <b>Excluir borda</b> descarta objetos cortados pela borda da imagem, que não podem ser medidos inteiros.</p>
<p class="fonte">Objetos encostados viram um só. Para separá-los, ligue antes "Separar objetos encostados" (Watershed).</p>
""",

"diametro": f"""
<h2>Mostrar diâmetro na imagem</h2>
<p class="tecnica">DIÂMETRO EQUIVALENTE (DIÂMETRO DO CÍRCULO DE MESMA ÁREA)</p>
<p>Escreve o tamanho de cada objeto no centro dele. Só muda o que você vê: nenhum pixel e nenhuma medida.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p>Objetos reais não são círculos perfeitos, então o Atol usa o diâmetro do círculo que teria a mesma área:</p>
{_formula("diametro", "A é a área do objeto; d sai em pixels e é dividido pela escala s, por ser um comprimento.")}
<p>O centro é o centroide: a média das posições de todos os pixels do objeto.</p>
<p class="fonte">Com mais de 60 objetos, aparece só o do objeto sob o mouse, para a tela não virar uma sopa de números.</p>
""",

"tabela": f"""
<h2>Tabela de resultados</h2>
<p class="tecnica">MEDIDAS POR OBJETO · COMO O "ANALYZE PARTICLES" DO FIJI</p>
<p>Abre uma janela com uma linha por objeto. Clique numa linha para ver o objeto destacado na imagem.</p>
<h4>O QUE ACONTECE POR TRÁS</h4>
<p><b>Área</b>: número de pixels do objeto (sem os buracos internos), dividido por s².</p>
<p><b>Perímetro</b>: só a borda de fora, com o mesmo algoritmo do ImageJ: o contorno é traçado pelas bordas dos pixels e cada canto desconta (2 − √2), para não somar a "escada" de arestas.</p>
{_formula("tabela_escada", "Em média, a escada de arestas sai 27% maior que o perímetro de um círculo.")}
<p><b>Circularidade</b>: 1 é um círculo perfeito; perto de 0, uma forma alongada ou recortada. Limitada a 1, como no ImageJ.</p>
{_formula("tabela_circ", "A é a área e P o perímetro. Não tem unidade e não muda com a escala.")}
<p><b>Tamanho médio</b>: média ± desvio padrão do diâmetro equivalente.</p>
{_formula("tabela_desvio", "d_i é o diâmetro de cada objeto, d̄ a média e n o número de objetos (n − 1: amostra).")}
<p><b>Histograma</b>: quantos objetos caem em cada faixa de diâmetro. O número de faixas (classes) segue a regra de Sturges:</p>
{_formula("tabela_sturges", "k é o número de classes e n o número de objetos; ⌈ ⌉ arredonda para cima.")}
<p><b>Fração de área</b>: a porcentagem da imagem coberta por objeto (porosidade, fração de uma fase, área corroída). Conta todo pixel de objeto, inclusive de objetos na borda, porque cortar a imagem não muda quanto material há em cada pixel.</p>
{_formula("tabela_fracao", "A_objetos é a soma das áreas de objeto e A_total a área da imagem. Não depende da escala.")}
<p>Pelo princípio de Delesse (1847), num corte qualquer do material a fração de área estima a fração de volume: A_A = V_V.</p>
<p class="fonte">"Exportar para Excel" gera as abas Objetos e Resumo; o Resumo usa fórmulas do Excel para você conferir.</p>
""",
}
