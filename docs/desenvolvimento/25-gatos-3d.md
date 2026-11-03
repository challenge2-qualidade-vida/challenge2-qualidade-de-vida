# Tópico 25 — Gatos em 3D e cores novas

**Status:** 🟡 Mia pronta e aguardando aprovação; Cifrão, Miau-ricio e Recibaldo ainda não foram feitos

O pedido foi trocar os gatos por personagens em 3D, com pelo e visual de filme de animação, que respiram e olham para o cursor, mexendo cabeça e olhos, no estilo de [pawzo.netlify.app](https://pawzo.netlify.app/). As cores do site também passaram a ser as dessa página. A cesta com as moedas virando comida (tópico 24) continua igual.

## Como a Mia funciona

Desenhar pelo de verdade em tempo real pesaria demais no navegador. Por isso, a Mia é renderizada antes, no Blender, em várias poses. O site só escolhe qual pose mostrar.

| Parte | Como é feita |
|-------|--------------|
| Modelo e pelo | Script em Python no Blender 5.2 (`experimentos/gatos3d/gato.py`), com render Cycles e pelo de partículas |
| Poses | Grade de 13 × 9 = 117 poses: a cabeça gira de 6° em 6° na horizontal (±36°) e de 4° em 4° na vertical (±16°). Os olhos giram um pouco além da cabeça |
| Imagem do site | `experimentos/gatos3d/grade.py` junta as poses em `src/web/img/gatos3d/mia.webp` (2,5 MB) e gera `mia-frente.webp` (33 KB), a imagem parada |
| Olhar | `src/web/gatos.js` calcula a pose a partir da posição do mouse e desenha no `<canvas>`. Com o mouse parado por 6 s, a Mia olha em volta devagar |
| Respiração | Animação em CSS (`@keyframes respirar`), que desliga quando a pessoa pede menos movimento |

A Pawzo usa um vídeo que só olha na horizontal. A grade também permite olhar para cima e para baixo.

### Quando a grade não é carregada

Em telas de toque, com economia de dados ou com menos movimento pedido no sistema, o site mostra só `mia-frente.webp`. No toque não há cursor para seguir, então os 2,5 MB não compensam. No toque e com economia de dados, a Mia continua respirando.

## Como refazer

São cerca de 20 s por pose, ou cerca de 40 minutos para a grade inteira, e não é preciso ter conta em nenhum serviço.

```bash
~/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python experimentos/gatos3d/gato.py -- --gato mia --grade <pasta das poses> \
  --amostras 48 --largura 640 --altura 780 --qualidade 1.0

.venv/bin/python experimentos/gatos3d/grade.py <pasta das poses> mia
```

Se mudar o tamanho da grade, atualize `YAWS` e `PITCHES` em `gato.py`, `COLUNAS, LINHAS` em `grade.py` e `COLUNAS, LINHAS` em `gatos.js`.

## Problemas encontrados

| Problema | Causa | Solução |
|----------|-------|---------|
| Olhos e boca duplicados | O site misturava poses vizinhas conforme a posição do mouse. Reduzir a distância entre as poses de 12° para 6° não bastou: com o mouse parado entre duas poses, o rosto continuava duplicado | O gato mostra sempre uma pose pura. A mistura acontece só na troca, por 80 ms |
| Mia olhava para o lado oposto na vertical | Na grade, a primeira linha (pitch positivo) olha para baixo, e o código supunha o contrário | Eixo invertido no `gatos.js` e comentário corrigido no `gato.py` |
| Título borrado | A sombra do texto usava a cor clara do fundo | Sombra em mostarda escuro |
| Logo verde ilegível no fundo mostarda | O arquivo do logo é verde | Filtro em CSS que deixa o nome creme |
| Conteúdo passando por baixo do logo ao rolar | Barra do topo transparente | Barra com o gradiente opaco |
| Cores diferentes no Chrome do Guilherme | A extensão Dark Reader recoloria a página | `<meta name="darkreader-lock">`, porque o site já tem tema escuro próprio |

## Cores

As cores vêm da página da Pawzo e ficam nas variáveis do início de `src/web/estilo.css`.

| Grupo | Cores |
|-------|-------|
| Mostarda | `#463708`, `#57450f`, `#6b5614`, `#80671a`, `#97791f`, `#b08d26` |
| Creme | `#FAF5EA`, `#efe6d0`, `#fffdf7` |
| Destaque | `#f5cf5f`, `#e3b62f`, `#fbf3d7`, `#f8e3a6` |
| Verde | `#6f8f4f` |
| Texto | `#3c332a`, `#76675e` |

`src/web/cena3d.js`, `src/web/manifest.webmanifest` e o `theme-color` do `index.html` também mudaram. O cache do site (`sw.js`) subiu para `economia-v5`.

## O que foi conferido

- 223 testes passando, incluindo `test_mia_tem_imagem_parada_e_grade_de_poses`.
- No Chrome, a 1470 px: a Mia acompanha o mouse nos quatro lados, com o rosto limpo com o mouse parado; barra ao rolar; console sem erros do site.
- Cores das telas Início, Cesta, Perto, Mia e Cupom.
- Largura de 390 px, simulada em um quadro dentro da página: sem rolagem lateral, Mia e cesta visíveis.

## O que falta

- Aprovação da Mia pelo Guilherme e pelo grupo.
- Fazer Cifrão, Miau-ricio e Recibaldo. Até lá, os gatos de `.mascote`, `.acao-gato`, `.cabecalho-tela` e `.turma` continuam sendo os desenhos verdes antigos, que destoam da paleta nova.
- Olhar a troca de poses em movimento: o teste automático confere o gato parado, e a suavidade precisa ser avaliada por uma pessoa.
- Testar em celular real.
