# Tópico 25 — Gatos em 3D e cores novas

**Status:** 🟡 os quatro gatos no site; a Mia foi aprovada pelo Guilherme, os outros três aguardam a avaliação dele; falta testar em celular real

O pedido foi trocar os gatos por personagens em 3D, com pelo e visual de filme de animação, que respiram e olham para o cursor, mexendo cabeça e olhos, no estilo de [pawzo.netlify.app](https://pawzo.netlify.app/). As cores do site também passaram a ser as dessa página. A cesta com as moedas virando comida (tópico 24) continua igual.

## Por que a Mia foi refeita

A primeira versão foi modelada por script no Blender e o Guilherme a achou feia. Olhos pareciam bolas coladas no rosto, e o pelo e as proporções ficaram longe das referências. Ele mandou a Pawzo e pins do Pinterest no estilo "3D cartoon estilizado". Vários desses pins têm o selo "Modificado por IA": esse visual vem de geração de imagem, e não de modelagem por script.

Depois que o Guilherme aprovou a Mia nessa técnica, Cifrão, Miau-ricio e Recibaldo foram feitos do mesmo jeito. Cada gato é **uma imagem gerada por IA, não um modelo 3D**. O movimento é uma deformação em tempo real dessa imagem. As imagens da Pawzo e do Pinterest serviram só de referência de estilo; nenhuma foi copiada para o projeto.

## Como os gatos funcionam

| Etapa | Como é feita |
|-------|--------------|
| Imagem | FLUX.1 schnell. A Mia veio do espaço gratuito do Hugging Face (`experimentos/gatos3d/gerar_imagem.py`). Quando a cota sem conta acabou, os outros três foram gerados no próprio Mac com o `mflux`, cerca de 6,5 min por imagem |
| Recorte | Máscara inicial do `rembg` (`isnet-general-use`), corrigida por `experimentos/gatos3d/recorte.py`: tapa os buracos nas orelhas, tira a franja clara do pelo e contorna as patas. Na Mia, troca a moeda por uma de cifrão legível; no Recibaldo, recupera o recibo e o rabo |
| Arquivos | `src/web/img/gatos3d/mia.webp` (85 KB) na abertura; `src/web/img/<gato>.webp` (30 a 40 KB) no resto do site; `src/web/img/turma.webp`, montada por `experimentos/gatos3d/turma.py`. A grade de poses da versão do Blender tinha 2,5 MB |
| Movimento | `src/web/gatos.js`, com um shader em WebGL 2. Os 16 gatos do site dividem um só contexto, porque o navegador limita quantos podem existir, e só os visíveis são desenhados |

O shader calcula, para cada pixel, de onde na imagem ele deve vir:

- **Cabeça:** gira como uma esfera. O miolo anda mais que a borda, o focinho avança e as orelhas recuam.
- **Olhos:** o miolo do olho anda e a borda fica parada, como um globo na órbita.
- **Respiração:** o peito expande e a cabeça sobe e desce um pouco.
- **Piscada:** a pálpebra desce a intervalos aleatórios de 2,2 a 6,4 s, em 170 ms.
- **Sem mouse:** depois de 6 s parado, e sempre no toque, o gato olha em volta devagar.
- **Miau-ricio:** de óculos escuros, não tem olhos nem piscada; só a cabeça acompanha o cursor.

Avatares do chat e o ícone do cardápio são pequenos demais para o movimento aparecer e ficam parados. O logo e os ícones do app usam o rosto da Mia (`experimentos/gatos3d/logo.py`); o nome continua o mesmo, e os desenhos originais ficam em `docs/marca/`.

Como nenhum quadro é misturado, o rosto não duplica. Sem WebGL 2 ou com menos movimento pedido no sistema, ficam as imagens paradas; a da abertura respira pelo CSS se só faltar o WebGL 2.

**Limite da técnica:** cada imagem só tem a frente do gato. Por isso o giro é pequeno, e os brilhos dos olhos andam junto com a íris, o que não aconteceria em um modelo 3D de verdade.

## Como refazer

```bash
python3 experimentos/gatos3d/gerar_imagem.py "<descrição>" 11 mia_11.webp
python3 experimentos/gatos3d/gerar_imagem.py "<descrição da moeda>" 55 mia_55.webp

# rembg em um ambiente separado, para não pesar no projeto
python3 -m venv recorte && recorte/bin/pip install "rembg[cpu]"
recorte/bin/python -c "from PIL import Image; from rembg import remove, new_session; remove(Image.open('mia_11.webp').convert('RGB'), session=new_session('isnet-general-use'), alpha_matting=True, alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=15, alpha_matting_erode_size=8).save('mia_recorte.png')"

.venv/bin/python experimentos/gatos3d/recorte.py mia mia_11.webp mia_recorte.png mia_final.png mia_55.webp
.venv/bin/python -c "from PIL import Image; Image.open('mia_final.png').save('src/web/img/gatos3d/mia.webp', quality=88, method=6, alpha_quality=95)"
```

Descrição da imagem usada (semente 11):

> Adorable 3D animated movie character render of a fluffy tuxedo kitten, black fur with white chest, white muzzle and white paws, sitting upright facing the camera, head looking straight at the viewer, perfectly symmetrical face, huge expressive round golden amber eyes with large glossy catchlights, small pink nose, gentle smile, long soft silky individually detailed fur, fluffy cheeks and chest tuft, big soft ears with pink inside, thin red collar with a small round gold coin pendant, Pixar Disney style, soft studio lighting, subsurface scattering, full body, plain solid light cream background, no shadow

Descrição da moeda (semente 55):

> Adorable 3D animated movie character render of a fluffy tuxedo kitten, black fur with white chest, white muzzle and white paws, sitting upright with front paws together, facing the camera, head straight, perfectly symmetrical face, big round golden amber eyes looking straight at the viewer with medium round black pupils and two glossy catchlights, small pink nose, closed gentle smile, long soft silky individually detailed fur, fluffy cheeks and chest tuft, soft ears with pink inside, thin red collar with a small round plain gold coin pendant with dollar sign, Pixar Disney style, soft studio lighting, subsurface scattering, full body with space around, plain solid light cream background

### Os outros três gatos

Geração no Mac, sem cota (são cerca de 9 GB de modelo e 17 GB de memória durante a geração):

```bash
uv venv --python 3.12 flux && uv pip install --python flux/bin/python mflux
flux/bin/mflux-generate --model dhairyashil/FLUX.1-schnell-mflux-4bit --base-model schnell \
  --steps 4 --width 896 --height 1024 --seed <semente> --output <gato>.png --prompt "<descrição>"

.venv/bin/python experimentos/gatos3d/recorte.py <gato> <gato>.png <gato>_recorte.png <gato>_final.png
.venv/bin/python experimentos/gatos3d/turma.py <pasta com os <gato>_final.png>
.venv/bin/python experimentos/gatos3d/logo.py <mia_final.png sem o corte>
```

Cifrão (semente 102) e Recibaldo (semente 301) usam esta base, seguida da descrição de cada um:

> Adorable 3D animated movie character render of a fluffy tuxedo kitten, black fur with white muzzle and white paws, sitting upright facing the camera, head looking straight at the viewer, perfectly symmetrical face, small pink nose, gentle smile, long soft silky individually detailed fur, fluffy cheeks, big soft ears with pink inside, Pixar Disney style, soft studio lighting, subsurface scattering, full body with space around, plain solid light cream background, no shadow

- **Cifrão:** huge expressive round golden amber eyes with large glossy catchlights, wearing a dark green baseball cap tilted to the side with a small gold crown emblem, dark green hoodie, thick shiny gold chain necklace with a big gold dollar sign pendant
- **Recibaldo:** huge expressive round golden amber eyes with large glossy catchlights, wearing a dark green plaid detective deerstalker hat, dark green suit vest, green bow tie, holding a big round magnifying glass with a gold frame in one paw and a long white paper receipt in the other paw

Miau-ricio (semente 212), com descrição própria, porque na base comum o bigode não aparecia:

> Adorable 3D animated movie character render of a fluffy tuxedo kitten with a big thick black curled handlebar mustache on its white muzzle right under the pink nose, wearing round black sunglasses with thin gold rims, one single dark green bow tie at the neck, dark green suit jacket, gold wristwatch on one paw, black fur with white muzzle and white paws, sitting upright facing the camera, head looking straight at the viewer, perfectly symmetrical face, gentle smile, long soft silky individually detailed fur, fluffy cheeks, big soft ears with pink inside, Pixar Disney style, soft studio lighting, subsurface scattering, full body with space around, plain solid light cream background, no shadow

Para um gato novo, as medidas (cabeça, olhos, focinho, orelhas, peito) entram em `GATOS`, no início de `gatos.js`, e a imagem usa `data-gato="<nome>"`. As medidas do recorte ficam em `GATOS`, no início de `recorte.py`.

## Problemas encontrados

| Problema | Causa | Solução |
|----------|-------|---------|
| Mia feia | Modelagem por script não chegou no nível das referências | Imagem gerada por IA, com movimento no shader. Os scripts do Blender saíram do projeto e continuam no histórico do git |
| Rosto duplicado na versão do Blender | Mistura de poses vizinhas | A técnica nova não mistura quadros |
| Buracos nas orelhas e franja clara | O `rembg` confundiu o rosa com o fundo | Preenchimento dos buracos e cor da borda tirada do pelo vizinho |
| Olhos deformados no extremo do olhar | Giro forte demais | Giro reduzido |
| Piscada com aparência de óculos | A pálpebra copiava a sobrancelha branca | Pálpebra na cor do pelo, com vinco escuro |
| Espaço gratuito recusando pedidos | Cota do uso sem conta | O mesmo modelo rodando no Mac com o `mflux`, sem cota |
| Miau-ricio sem bigode e com duas gravatas | A descrição comum não destacava o bigode | Descrição própria e quatro novas opções |
| Recibo e rabo do Recibaldo apagados | Branco sobre fundo claro e parte fina longe do corpo | Polígono do recibo e área do rabo indicados em `recorte.py` |
| Olhos menores achatavam no extremo do olhar | O deslocamento era igual para todos os olhos | Deslocamento proporcional ao tamanho do olho e giro vertical menor |
| Recibaldo com cinco patas | A imagem gerada trouxe as duas de trás, as duas da frente no chão e a que segura a lupa | A pata da frente abaixo do braço levantado virou barriga, com um remendo de pelo em `recorte.py`. Os outros gatos foram conferidos e têm quatro |
| Mão do Recibaldo preta, diferente das outras patas | A imagem gerada trouxe a mão que segura a lupa em preto | O punho e o polegar são clareados em `recorte.py`, mantendo dobras e textura. O braço continua escuro, como nas outras patas |
| Limite de contextos de WebGL | Um contexto por gato estouraria o limite do navegador com 16 gatos | Um só contexto compartilhado |
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

- 223 testes passando, incluindo `test_gatos_sao_imagens_animadas_pelo_gatos_js`.
- No Chrome, a 1470 px: os 16 gatos ativos, a 62 quadros por segundo, sem erro do site no console. Cifrão e Recibaldo foram conferidos ampliados nos extremos do olhar.
- Cabeçalhos das telas Cesta, Cupom e Mia, cartões do Início e imagem da turma.
- Largura de 390 px, simulada em um quadro dentro da página: sem rolagem lateral.
- Cores das telas Início, Cesta, Perto, Mia e Cupom.

## O que falta

- Avaliar o movimento a olho, inclusive a piscada: o teste automático confere quadros parados. O Miau-ricio não foi conferido ampliado, e o ajuste final dos olhos não foi revisto nos extremos.
- Testar em celular real, inclusive o desempenho.
- Citar no relatório final que os gatos foram gerados por IA.
