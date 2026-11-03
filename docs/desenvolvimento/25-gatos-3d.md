# Tópico 25 — Gatos em 3D e cores novas

**Status:** 🟡 Mia refeita e aguardando aprovação; Cifrão, Miau-ricio e Recibaldo ainda não foram feitos

O pedido foi trocar os gatos por personagens em 3D, com pelo e visual de filme de animação, que respiram e olham para o cursor, mexendo cabeça e olhos, no estilo de [pawzo.netlify.app](https://pawzo.netlify.app/). As cores do site também passaram a ser as dessa página. A cesta com as moedas virando comida (tópico 24) continua igual.

## Por que a Mia foi refeita

A primeira versão foi modelada por script no Blender e o Guilherme a achou feia. Olhos pareciam bolas coladas no rosto, e o pelo e as proporções ficaram longe das referências. Ele mandou a Pawzo e pins do Pinterest no estilo "3D cartoon estilizado". Vários desses pins têm o selo "Modificado por IA": esse visual vem de geração de imagem, e não de modelagem por script.

A Mia agora é **uma imagem gerada por IA, não um modelo 3D**. O movimento é uma deformação em tempo real dessa imagem. As imagens da Pawzo e do Pinterest serviram só de referência de estilo; nenhuma foi copiada para o projeto.

## Como a Mia funciona

| Etapa | Como é feita |
|-------|--------------|
| Imagem | FLUX.1 schnell, no espaço gratuito do Hugging Face, sem conta (`experimentos/gatos3d/gerar_imagem.py`) |
| Recorte | Máscara inicial do `rembg` (`isnet-general-use`), corrigida por `experimentos/gatos3d/recorte_mia.py`: tapa os buracos nas orelhas, tira a franja clara do pelo, contorna as patas e troca a moeda pela de outra imagem, que saiu com um cifrão legível |
| Arquivo | `src/web/img/gatos3d/mia.webp`, 790 × 990 px e cerca de 85 KB. A grade de poses da versão do Blender tinha 2,5 MB |
| Movimento | `src/web/gatos.js`, com um shader em WebGL 2 |

O shader calcula, para cada pixel, de onde na imagem ele deve vir:

- **Cabeça:** gira como uma esfera. O miolo anda mais que a borda, o focinho avança e as orelhas recuam.
- **Olhos:** o miolo do olho anda e a borda fica parada, como um globo na órbita.
- **Respiração:** o peito expande e a cabeça sobe e desce um pouco.
- **Piscada:** a pálpebra desce a intervalos aleatórios de 2,2 a 6,4 s, em 170 ms.
- **Sem mouse:** depois de 6 s parado, e sempre no toque, a Mia olha em volta devagar.

Como nenhum quadro é misturado, o rosto não duplica. Sem WebGL 2 ou com menos movimento pedido no sistema, fica a imagem parada; só sem WebGL 2 ela respira pelo CSS.

**Limite da técnica:** a imagem só tem a frente da gata. Por isso o giro é pequeno, e os brilhos dos olhos andam junto com a íris, o que não aconteceria em um modelo 3D de verdade.

## Como refazer

```bash
python3 experimentos/gatos3d/gerar_imagem.py "<descrição>" 11 mia_11.webp
python3 experimentos/gatos3d/gerar_imagem.py "<descrição da moeda>" 55 mia_55.webp

# rembg em um ambiente separado, para não pesar no projeto
python3 -m venv recorte && recorte/bin/pip install "rembg[cpu]"
recorte/bin/python -c "from PIL import Image; from rembg import remove, new_session; remove(Image.open('mia_11.webp').convert('RGB'), session=new_session('isnet-general-use'), alpha_matting=True, alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=15, alpha_matting_erode_size=8).save('mia_recorte.png')"

.venv/bin/python experimentos/gatos3d/recorte_mia.py mia_11.webp mia_recorte.png mia_55.webp mia_final.png
.venv/bin/python -c "from PIL import Image; Image.open('mia_final.png').crop((60,0,850,990)).save('src/web/img/gatos3d/mia.webp', quality=88, method=6, alpha_quality=95)"
```

Descrição da imagem usada (semente 11):

> Adorable 3D animated movie character render of a fluffy tuxedo kitten, black fur with white chest, white muzzle and white paws, sitting upright facing the camera, head looking straight at the viewer, perfectly symmetrical face, huge expressive round golden amber eyes with large glossy catchlights, small pink nose, gentle smile, long soft silky individually detailed fur, fluffy cheeks and chest tuft, big soft ears with pink inside, thin red collar with a small round gold coin pendant, Pixar Disney style, soft studio lighting, subsurface scattering, full body, plain solid light cream background, no shadow

Descrição da moeda (semente 55):

> Adorable 3D animated movie character render of a fluffy tuxedo kitten, black fur with white chest, white muzzle and white paws, sitting upright with front paws together, facing the camera, head straight, perfectly symmetrical face, big round golden amber eyes looking straight at the viewer with medium round black pupils and two glossy catchlights, small pink nose, closed gentle smile, long soft silky individually detailed fur, fluffy cheeks and chest tuft, soft ears with pink inside, thin red collar with a small round plain gold coin pendant with dollar sign, Pixar Disney style, soft studio lighting, subsurface scattering, full body with space around, plain solid light cream background

Para um gato novo, as medidas (cabeça, olhos, focinho, orelhas, peito) entram em `GATOS`, no início de `gatos.js`, e a imagem usa `data-gato="<nome>"`. As medidas das patas e da moeda ficam no início de `recorte_mia.py`.

## Problemas encontrados

| Problema | Causa | Solução |
|----------|-------|---------|
| Mia feia | Modelagem por script não chegou no nível das referências | Imagem gerada por IA, com movimento no shader. Os scripts do Blender saíram do projeto e continuam no histórico do git |
| Rosto duplicado na versão do Blender | Mistura de poses vizinhas | A técnica nova não mistura quadros |
| Buracos nas orelhas e franja clara | O `rembg` confundiu o rosa com o fundo | Preenchimento dos buracos e cor da borda tirada do pelo vizinho |
| Olhos deformados no extremo do olhar | Giro forte demais | Giro reduzido |
| Piscada com aparência de óculos | A pálpebra copiava a sobrancelha branca | Pálpebra na cor do pelo, com vinco escuro |
| Espaço gratuito recusando pedidos | Cota do uso sem conta | Aproveitadas as três imagens que já tinham sido geradas |
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

- 223 testes passando, incluindo `test_mia_e_uma_imagem_animada_pelo_gatos_js`.
- No Chrome, a 1470 px: a Mia acompanha o mouse nos extremos e no alto, a 62 quadros por segundo, sem erro de WebGL nem do site no console.
- Piscada: quadros de meio e de olho fechado conferidos um a um.
- Largura de 390 px, simulada em um quadro dentro da página: sem rolagem lateral. As patas ficam atrás da barra inferior até rolar a página.
- Cores das telas Início, Cesta, Perto, Mia e Cupom.

## O que falta

- Aprovação da Mia pelo Guilherme e pelo grupo.
- Fazer Cifrão, Miau-ricio e Recibaldo. Até lá, os gatos de `.mascote`, `.acao-gato`, `.cabecalho-tela` e `.turma` continuam sendo os desenhos verdes antigos, que destoam da paleta nova.
- Avaliar o movimento a olho, inclusive a piscada: o teste automático confere quadros parados.
- Testar em celular real.
- Citar no relatório final que a Mia foi gerada por IA.
