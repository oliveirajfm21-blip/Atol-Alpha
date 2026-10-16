# Decisões do projeto

Registro curto do que foi decidido e por quê, para não rediscutir.

| Data | Decisão | Motivo |
|---|---|---|
| set/2026 | Python puro (PySide6 + scikit-image), sem Fiji por baixo | Controle total da interface para iniciantes; instalação simples. |
| set/2026 | Escopo genérico; biologia fora do núcleo | O laboratório é de mecânica; áreas específicas viram pacotes. |
| set/2026 | Nome "Atol", paleta própria | Identidade visual separada de outros projetos. |
| set/2026 | Linha do tempo sempre recalcula da imagem original | Desligar um passo não perde informação. |
| set/2026 | Calibração é propriedade da imagem, não um passo | Não muda pixels; mudar a escala recalcula as medidas. |
| out/2026 | Perímetro pelo contorno traçado do ImageJ (desconta 2 − √2 por canto) | O perímetro em escada sai ~27% maior; agora bate com o ImageJ. |
| out/2026 | Perímetro e circularidade sobre o objeto com buracos preenchidos | Buracos internos derrubavam a circularidade (0,11). |
| 13/10 | Mediana e Watershed no núcleo (não como add-on) | Toda área usa. |
| 13/10 | Watershed com h = 0,7 | Reproduz os cortes do ImageJ (h nominal 0,5 + correção de altura do EDM). |
| 13/10 | Fração de área inclui objetos na borda | É medida por pixel; excluir criaria viés para menos. |
| 13/10 | Tutor por roteiros (dados), ordem sugerida, começa desligado | Pular passos é normal; roteiros poderão vir de pacotes. |
| 13/10 | Roteiros pelos 3 objetivos da eng. mecânica (fração de fases, partículas, grão) | Usos mais comuns de metalografia com ImageJ; confirmar com o professor. |
| 13/10 | Intercepto: cada linha vale entre o 1º e o último contorno | Evita viés dos grãos cortados pela borda (listras dão ℓ̄ exato). |
| 14/10 | Ângulo com atan2(−Δy, Δx) | Sem divisão por zero, quadrante certo, eixo y da imagem invertido. |
| 14/10 | Gráficos com SciencePlots (`science` + `no-latex`), tabelas sem grade | Pedido do professor: padrão de artigo; no-latex dispensa LaTeX instalado. |
| 14/10 | Testes automáticos antes de reorganizar | Rede de proteção: 19 testes com os números validados. |
| 14/10 | Código em pacote `atol/` com camadas (nucleo, saida, tutor, interface, ajuda) | Trocar uma parte sem mexer nas outras; base para add-ons e executável. |
| — | Executável só depois de congelar as funções | Evita gerar de novo a cada mudança. |
| 14/10 | Add-ons e modo ao vivo depois de 05/11 (o plano fica em COMO_ADICIONAR.md) | Prazo; o essencial é o teste com alunos. |
| 14/10 | Beta interno (0.9.0b1) | Núcleo validado e os 3 objetivos principais cobertos. |
| 15/10 | Primeira versão pública no GitHub como alfa (0.9.0a1); README em inglês, código e comentários em português (estilo do projeto CMS: seções numeradas + "Em palavras simples") | Currículo e candidatura ao CERN; a interface é em português. |
| 14/10 | Um só código + edições "Atol Material" e "Atol Life", escolhidas numa tela inicial | Núcleo validado uma vez só; cada edição liga os próprios pacotes e roteiros. |
