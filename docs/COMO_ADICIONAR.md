# Como adicionar uma ferramenta

Exemplo: um passo novo chamado "Esqueletizar" (chave `esqueleto`). Siga a ordem: ciência e teste primeiro,
interface por último.

## 1. Núcleo — `atol/nucleo/passos.py` (ou `medidas.py`, se for uma medida)

```python
class Esqueletizar(Passo):
    nome = "Esqueleto"

    def __init__(self, poda: int = 5):
        super().__init__()          # cria self.ativo
        self.poda = poda

    def aplicar(self, imagem):
        ...                         # recebe NumPy, devolve NumPy. Nada de Qt aqui.
```

Exporte em `atol/nucleo/__init__.py` (no `import` e no `__all__`).

## 2. Teste — `tests/test_atol.py`

Escreva um teste com uma entrada cuja resposta você conhece (uma imagem sintética, um valor de norma,
uma saída do ImageJ). Compare números reais com `approx`, nunca com `==`.

```python
def test_esqueleto_linha_reta():
    ...
    assert comprimento == approx(100, abs=1)
```

Rode `pytest`: o novo teste e os antigos têm que passar.

## 3. Menu e dependências — `atol/tutor/roteiros.py`

- Em `TEMAS`, adicione `("esqueleto", "Esqueleto")` no tema certo.
- Em `PRECISA`, se ele exigir outro passo: `"esqueleto": "limiar"`.
- Em `ROTEIRO`, coloque a chave na posição da ordem de processamento.
- Se fizer parte de uma análise guiada, adicione-a no roteiro certo em `ROTEIROS`, com uma dica.

## 4. Interface — `atol/interface/janela.py`

1. Em `__init__`: crie o passo (`self.esqueleto = Esqueletizar()`) e coloque-o em `self.passos`
   **na posição certa** (a ordem importa).
2. Em `criar_lateral`: crie o `Painel` com os controles e guarde em `self.paineis["esqueleto"]`;
   inclua a chave na tupla que adiciona os painéis na lateral.
3. Em `ao_alternar`: `elif chave == "esqueleto": self.esqueleto.ativo = ligado`.
4. Crie os slots dos controles (`ao_mudar_poda`), que mudam o parâmetro e chamam `self.renderizar()`.

## 5. Ajuda — `atol/ajuda/`

- Em `__init__.py`, adicione `AJUDA["esqueleto"]` (nome, técnica, o que acontece por trás, fórmulas, referência).
- Fórmulas novas: em `gerar.py`, adicione em `FORMULAS` e rode `python -m atol.ajuda.gerar`.

## 6. Conferir

- `pytest` (tudo verde), `python main.py`, ligar a chave, passar o mouse para ver o cartão de ajuda.
- Anotar no `CONTEXTO.md` e, se tiver validação, no `validacao/RELATORIO.md`.

---

# Plano dos add-ons (ainda não implementado)

Objetivo: alguém do laboratório cria uma ferramenta **sem abrir o código da interface**.

```
Atol/complementos/materiais/
├── pacote.json        {"nome": "Materiais", "versao": "1.0", "autor": "...", "atol_minimo": "0.9"}
└── ferramentas.py     classes que herdam de Passo
```

```python
from atol.nucleo import Passo

class Esqueletizar(Passo):
    nome = "Esqueleto da trinca"
    explicacao = "Afina a trinca até 1 pixel para medir o comprimento."
    parametros = {
        "poda": {"tipo": "inteiro", "padrao": 5, "min": 0, "max": 50,
                 "rotulo": "Remover galhos menores que", "unidade": "px"},
    }

    def aplicar(self, imagem):
        ...
```

- `atol/complementos/carregador.py` varre a pasta, lê cada `pacote.json`, importa as ferramentas.
- Cada pacote vira um tema na barra de cima, com o nome da pasta.
- O painel é montado a partir de `parametros`, pelo tipo: inteiro → caixa com setas; decimal → caixa
  decimal; escolha → lista; sim/não → caixinha.
- Menu "Complementos" com uma chave por pacote. Pacote novo chega **desligado**: é código de terceiros
  e roda com as mesmas permissões do Atol.
- Pacotes podem trazer os próprios roteiros do Tutor.
