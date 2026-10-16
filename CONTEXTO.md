# Atol — contexto para a próxima sessão

Cole este arquivo no início de uma conversa nova para continuar sem gastar tempo explicando.

## Projeto
Programa de análise de imagens científicas para iniciantes, inspirado no Fiji/ImageJ, para o Prof. Dr. Gilberto Prandi (lab. de mecânica, Unicamp). Prazo: 05/11/2026. Python + PySide6 + NumPy + scikit-image. Autor: João Filipe M. de Oliveira.
Modo de trabalho: interface por vibe coding (IA escreve, eu rodo e explico de volta); núcleo científico em modo professor. Fórmulas em LaTeX com legenda. Corrigir minha ortografia no início das respostas.

## Arquivos (pasta Atol) — estrutura desde 14/10 (v0.9)
- main.py: só abre o Atol (python main.py).
- atol/nucleo/: processamento científico, sem Qt — passos.py (mediana, fundo, contraste, limiar, watershed, contar), medidas.py (objetos, perímetro, intercepto/G, ângulos, Vickers, Sturges), imagem.py (abrir, linha do tempo), calibracao.py.
- atol/saida/: excel.py e graficos.py (SciencePlots).
- atol/tutor/roteiros.py: TEMAS, PRECISA, ROTEIRO, ROTEIROS (dados).
- atol/interface/: janela.py (JanelaAtol), visor.py, resultados.py, componentes.py, estilo.py.
- atol/ajuda/: textos dos cartões (__init__.py), imagens/ e gerar.py (python -m atol.ajuda.gerar).
- tests/test_atol.py: 19 testes com os números validados (rodar: pytest). Regra: rodar pytest antes e depois de qualquer mudança.
- _antigo/: o main.py único de antes (backup).
- README.md e docs/ (ARQUITETURA, FERRAMENTAS, COMO_ADICIONAR, DECISOES): documentação técnica, feita 14/10. Atualizar junto com o código.
- Identidade visual: paleta oceano #0B3340, lagoa #1FA89C, coral #F2606F, espuma #EFF5F4; visor cinza #808080.

## O que já funciona
- Linha do tempo de Passos (cada um com ativo): FiltroMediana (disco de raio r, cor por canal, com cache) → CorrigirFundo (rolling ball, raio 40, com cache) → AjustarContraste → Limiarizar (IsoData à mão / Otsu) → SepararEncostados (watershed: distância + h-máximos, h = 0,7; opção preencher buracos) → ContarObjetos (vizinhança-8, área mínima, excluir borda).
- Calibracao (fora da linha do tempo): L/s e A/s²; chave desligada mede em px e guarda a escala.
- Visor com zoom (Ctrl+roda, botões, arrastar), conversão tela↔imagem x_img = (x_tela − o)/z.
- Barra superior por tema (Imagem, Ajustar, Analisar, Resultados): clicar abre um menu suspenso com as chavinhas uma embaixo da outra, que some quando o mouse sai; painéis à esquerda só das chaves ligadas; dependências automáticas (contar liga separar).
- Diâmetro equivalente na imagem; janela de Resultados (cartão média ± desvio do diâmetro, tabela, clique destaca objeto, exportar Excel com abas Objetos e Resumo).
- Perímetro só da borda externa (estimador corrigido, não a "escada"); circularidade 4πA/P² limitada a 1.
- Cartões de ajuda ao passar o mouse nas chaves (técnica, fórmulas, figuras, rola com a roda).

## Validação (feita)
- Atol × ImageJ 1.54p (motor do Fiji) nas imagens coins e Blobs: mesmo limiar, mesma contagem (Blobs: 64), áreas idênticas, perímetro igual ao do ImageJ (mesmo algoritmo de contorno traçado). Detalhes em validacao/RELATORIO.md; script em validacao/Validar.java.
- Watershed × ImageJ (Binary › Watershed) na mesma máscara: Blobs 68 = 68, mesmos cortes; coins 189 = 189 (13 de 96 manchas cortadas diferente, regiões com buracos). Script validacao/WS.java.

## Estado: ALFA 1 público (0.9.0a1) desde 15/10 — no GitHub; CONTEXTO.md fica fora do Git (.gitignore)
Daqui em diante: correções, testes com imagens reais do laboratório e os itens de preparação do estudo. Add-ons e modo ao vivo ficam para depois de 05/11.

## Próximos passos (em ordem)
Regra: núcleo = o que qualquer área usa; complemento = o que serve a uma área específica.

Prioridade 1 — fechar o escopo (até 05/11)
1. ✔ Filtro de mediana (feito 13/10).
2. ✔ Watershed (feito e validado 13/10).
3. ✔ Histograma (Sturges) e cartão de fração de área nos Resultados (feito 13/10; fração vai também para o Resumo do Excel).
4. ✔ Medir distância e ângulo (feito 14/10: tema Imagem; atan2; ângulo entre as 2 últimas linhas; recalcula com a escala); apagar a selecionada/última. Dureza Vickers no mesmo painel (2 últimas linhas = diagonais, cargas HV0,1–HV30, avisos de diagonais desiguais/não perpendiculares) + roteiro "Dureza Vickers" no Tutor.)
- 14/10: gráficos com SciencePlots (estilo science + no-latex), botão "Salvar gráfico…" (PNG 600 dpi/PDF/SVG, 1 coluna de artigo); tabelas no estilo de artigo (3 linhas, sem grade), também no Excel; requirements.txt criado.
5. Sistema de complementos e pacotes:
   - complemento = arquivo .py que herda de Passo e declara parâmetros; o Atol monta o painel e o cartão de ajuda sozinho;
   - pacote = pasta ou .zip com pacote.json (nome, versão, autor, área, versão mínima do Atol) + complementos; cada pacote instalado vira um tema novo na barra superior; botão "Instalar pacote…";
   - primeiro pacote: Materiais (tamanho de grão pelo método do intercepto, ASTM E112; comprimento de trincas por esqueletização). Pacote de Biologia (separar canais, contagem por fluorescência, colocalização) fica como ideia futura ou para alguém da área;
   - avisar que pacotes são código: instalar só de fonte confiável.

Prioridade 2 — preparar o estudo com alunos
6. Registro automático de tempo e passos.
7. Revisar os textos dos cartões de ajuda (fundo e limiarização).
8. Tutor — v1 feito 13/10: botão Tutor (começa desligado) abre um menu de roteiros pelos 3 objetivos principais da eng. mecânica com o Fiji (Porosidade e fração de fases; Tamanho e forma de partículas; Tamanho de grão ASTM E112 — feito 13/10: intercepto horizontal e vertical, G, alongamento; por ora no núcleo, depois vai para o pacote Materiais) + Contagem de células; confirmar com o professor quais o laboratório mais usa; escolhido um, a lateral mostra só os passos dele, numerados, com uma dica por passo; ordem sugerida (destaca o próximo, não trava). Roteiros ficam em JanelaAtol.ROTEIROS (dados), para os pacotes trazerem os seus depois. Falta a v2, avisos inteligentes: avisar quando a imagem tiver tabela de cores invertida (caso da Blobs); avisar quando o Watershed cortar muitos pedaços por mancha (sugerir "Preencher buracos").
9. Executável (PyInstaller, ícone do Atol) — depois do dia 11, com as funções congeladas.
10. Teste com alunos (SUS, tempo, acertos; metade começa pelo Fiji, metade pelo Atol). Depois, abstract em inglês e escolha da revista com o JournalFinder (Elsevier) e o Springer Journal Suggester.

Prioridade 3 — depois da entrega
11. Modo ao vivo com webcam ou microscópio (gráficos em tempo real; botão "Gravar" que guarda medidas e imagens brutas e mostra o resumo do período). Antes, perguntar ao professor se o laboratório acompanha ensaios com câmera.
12. Feret e razão de aspecto.
13. Arrastar e soltar.

## Reorganização do código — ✔ feita 14/10 (ver Arquivos)
Antes de reorganizar: testes automáticos (pytest) com os números validados (Blobs 64, Watershed 68/189, listras ℓ̄ = 20, G da tabela ASTM). Depois: separar main.py em módulos (núcleo, interface, ajuda), buscando eficiência e um código mais profissional.

## Situação em 14/10
- Prof. Gilberto vai separar imagens particularmente difíceis do laboratório → próxima sessão: testar o beta nelas (cada bug vira um teste).
- Prof. Garraffoni ainda não respondeu (imagens de biologia).
- Comitê de ética: adiado por decisão do João (lembrar: aprovação leva semanas e condiciona o teste com alunos).
- Decidido (14/10): um só código (núcleo comum) + pacotes por área; ao abrir, uma tela inicial pergunta qual edição iniciar: "Atol Material" (mecânica/materiais) ou "Atol Life" (biologia). A edição só escolhe quais pacotes e roteiros do Tutor vêm ligados. Nomes a definir (manter tudo em português ou tudo em inglês). Implementar junto com o sistema de pacotes (depois de 05/11), ou antes só a tela, se for útil para o teste.

## Pendências com o professor
Programa independente em Python atende? Comitê de ética para o teste com alunos (perguntar já: a aprovação pela Plataforma Brasil leva semanas)? Política de uso de IA? Revista ou evento, idioma e tamanho do abstract? O laboratório acompanha ensaios com câmera? Quais análises o laboratório mais usa (tamanho de grão? trincas? outra)?

## Aviso técnico para a IA
Ao gravar arquivos na pasta do usuário, use um nome de arquivo temporário novo a cada envio (a ponte guarda a cópia anterior se o nome se repetir).
