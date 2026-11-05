# Tópico 26 — Abertura 3D refeita

**Status:** ✅ concluído em 05/11/2026; falta testar em celular real

O Guilherme trouxe um briefing de design: moedas genéricas com "$", comida facetada, cesta de arame escondida atrás da gata e animação sem ligação com o resto da página. A ideia central foi mantida: **cada real vira comida de verdade**.

## O que mudou

| Parte | Antes | Agora |
|-------|-------|-------|
| Cesta | Cone de arame atrás da gata | Cestinha de mercado com parede vazada, borda dourada e duas alças, ao lado da gata |
| Moedas | 80 iguais, com "$", passando pelo título | 32 (14 em aparelho fraco), em três tipos, nunca atrás do título, do texto ou do botão |
| Comida | Formas geométricas facetadas | 28 imagens no estilo dos gatos |
| História | A moeda sumia ao entrar na cesta | A moeda vira comida, a comida cai, a cesta balança e o anel de nutrição pulsa |

O título da abertura passou a ser "Faça seu dinheiro render" em 05/11/2026, a pedido do Guilherme.

## Moedas

Inspiradas nas moedas do real, sem copiar o desenho oficial:

| Tipo | Proporção | Aparência |
|------|-----------|-----------|
| Bimetálica | 50% | Miolo prateado, anel dourado, serrilha e "R$" |
| Dourada | 30% | Serrilha e "R$" |
| Acobreada | 20% | Menor, borda lisa e patinha de gato |

Tudo é gerado por código em `cena3d.js`: o relevo é pintado em um canvas e convertido em mapa de normais, e o campo é mais fosco que o relevo. Faixas de luz no ambiente fazem o reflexo deslizar quando a moeda gira.

## Alimentos

O briefing pedia para testar primeiro as imagens de `img/alimentos`, e depois modelos gratuitos como o Kenney Food Kit. As duas opções foram descartadas:

- **Fotos do projeto:** são quadradas, com 240 px e fundo, então cairiam como quadradinhos.
- **Modelos do Kenney e similares:** são facetados, justamente o problema apontado pelo briefing. Não chegaram a ser baixados.

Os 28 alimentos foram gerados com o FLUX.1 schnell no Mac, no mesmo estilo dos gatos, cerca de 3 minutos cada. O `isnet-general-use`, usado nos gatos, cortou uma banana porque o fundo também era amarelo, então os alimentos usam o `birefnet-general-lite`.

Em `src/web/img/comida.webp`, cada alimento tem 192 × 192 px, e o conjunto pesa 193 KB. Eles também aparecem na cesta da tela Cesta, com os itens calculados.

```bash
HF_HOME=hf flux/bin/mflux-generate --model dhairyashil/FLUX.1-schnell-mflux-4bit --base-model schnell \
  --steps 4 --seed 7 --width 512 --height 512 --output comida/<id>.png --prompt "<alimento>, <base>"

# Em um ambiente com rembg: remove(imagem, session=new_session("birefnet-general-lite")), salvo em comida/<id>_recorte.png
.venv/bin/python experimentos/gatos3d/comida.py comida
```

Descrição base:

> cute 3D animated movie style food icon, soft rounded shapes, Pixar Disney style render, soft studio lighting, subsurface scattering, glossy highlights, warm saturated colors, single centered object fully visible with space around, no text, no letters, no label, no logo, plain solid light cream background, no shadow

A ordem de `ORDEM` em `comida.py` precisa ser igual à de `ATLAS` em `cena3d.js`. Um teste confere isso.

## Coreografia

| Etapa | Duração | O que acontece |
|-------|---------|----------------|
| Antecipação | 150 ms | A moeda acelera o giro e encolhe 10% |
| Transformação | 250 ms | A moeda some, sobem faíscas e o alimento surge com um salto |
| Queda | 550 ms | O alimento faz um arco até a vaga na cesta, esticando na queda |
| Impacto | 220 ms | O alimento amassa e quica, e a cesta balança |
| Recompensa | 620 ms | Uma faísca na cor do grupo voa até o anel e ele pulsa, se estiver na tela |

- **Rolagem:** a primeira comida sai em menos de 1 s, depois uma a cada 1,7 s, ou mais rápido conforme a rolagem. A cesta enche até o fim da abertura.
- **Cesta cheia:** a Mia dá um pulinho. Se a pessoa continuar no topo da página, cinco alimentos saem depois de 6 s e a história recomeça.
- **Mia:** ela pisca quando um alimento cai.
- **Anéis:** Energia (dourado), Proteína (terracota), Fibra (marrom) e Frutas e hortaliças (verde).

## Diferenças em relação ao briefing

| O briefing pedia | O que foi feito | Por quê |
|------------------|-----------------|---------|
| Cesta verde-floresta `#463708` | Verde `#2f6b3f` | `#463708` é o mostarda escuro da paleta, não verde, e sumiria no fundo |
| Coreografia com GSAP | Código próprio no laço da cena e Web Animations | Os objetos já são atualizados a cada quadro, e o GSAP não carrega para quem pede menos movimento |
| Serrilha por mapa de normais | Serrilha na geometria | Mais simples com o mesmo efeito. Em aparelho fraco, não há serrilha |
| `InstancedMesh` por tipo de alimento | Um `Sprite` por alimento | No máximo 18 alimentos na tela, e cada um é uma imagem |
| Pausar fora da abertura | Pausa com a aba oculta; a coreografia para fora da abertura | As moedas das beiradas continuam em todas as telas, como antes |
| Modelos Kenney, gltf-transform | Não usados | Ver "Alimentos" |

## Recibo da tela Cupom

Refeito em 05/11/2026, depois de pesquisar recibos, papel em 3D e o cupom fiscal brasileiro. Tudo é desenhado por código em `cena3d.js`:

- **Papel:** branco quente e fosco, com fibras, bordas serrilhadas, curvatura com a ponta de baixo enrolando e sombra macia.
- **Conteúdo:** logo, itens com os alimentos do site, total, economia com marca-texto, QR code e chave de acesso.
- **Animação:** o feixe desce em 3 s, cada item ganha um ✓ e o Recibaldo carimba "CONFERIDO". O ciclo tem 7 s e, com menos movimento pedido, o recibo aparece parado e já conferido.

**É uma ilustração, não um documento.** O papel diz "CUPOM DE EXEMPLO" e "SEM VALOR FISCAL", o QR code não abre nada, e a chave de acesso é só de zeros. Os preços são inventados, e o total confere com a soma dos itens.

Referências: [recibo térmico da shadcn.io](https://www.shadcn.io/blocks/features-receipt-itemized-printout), [papel 3D enrolado](https://www.ui-skills.com/skills/mengto/3d-paper-material), [simulações de papel de recibo](https://kimi-k26-ollama.pages.dev/physics/PROMPT.md), [campos do DANFE](https://www.nuvemshop.com.br/blog/o-que-e-danfe/) e [linha de leitura](https://codemyui.com/barcode-scan-line-animation-pure-css/). Só serviram de ideia; nenhum código ou imagem delas está no projeto. A simulação física do papel ficou de fora, porque uma curvatura calculada é mais leve e bastou para o efeito.

## Mapa da tela Perto

Refeito em 05/11/2026, depois de pesquisar mapas estilizados, marcadores de apps de entrega e os princípios de cartografia. O radar de cones virou uma cidade em miniatura, toda criada por código em `cena3d.js`:

- **Chão:** pintado em canvas, com ruas claras, dois eixos largos em cruz e um lago curvo, um aceno a Brasília. Água e parque têm cores bem diferentes, e só os marcadores têm cor forte.
- **Volume:** prédios e árvores são peças repetidas com `InstancedMesh`, para pesar pouco.
- **Marcadores:** você é um ponto azul, e os pinos são gotas com um carrinho. O destaque é verde e maior, então não depende só da cor.
- **Animação:** ondas saem da sua posição, um leque gira e cada pino salta e solta um eco quando ele passa. Uma rota tracejada anda até o pino verde. Com menos movimento pedido, tudo fica parado.

**É ilustração.** Os pinos não mostram mercados reais, o traçado não é o mapa real de Brasília e o pino verde não indica um mercado de verdade. Os mercados aparecem na lista abaixo do mapa.

Referências: [cartografia da Mapbox](https://mcpservers.org/pt-BR/agent-skills/mapbox/mapbox-cartography), [crítica às cores do Google Maps](https://www.techradar.com/computing/software/google-maps-now-looks-more-like-apple-maps-and-a-lot-of-people-arent-happy), [marcadores personalizados](https://www.digitalthriveai.com/en-ca/resources/how-to/web-design/building-custom-react-native-map-markers/), [movimento suave de marcadores](https://vp0.com/blogs/live-tracking-map-marker-animation-react-native), [elementos de mapa isométrico](https://stock.adobe.com/images/isometric-3d-map-elements-set-with-minimalist-buildings-trees-and-location-pins-for-a-city-constructor-or-navigation-app-design/1689285685) e [cidade procedural em Three.js](https://dev.to/bingkahu/building-the-round-city-of-baghdad-in-threejs-a-journey-through-history-and-performance-15pf). Só serviram de ideia; nenhum código ou imagem delas está no projeto.

## Como foi testado

| Teste | Resultado |
|-------|-----------|
| Testes automáticos | 224 passando, incluindo o atlas de alimentos |
| Velocidade, em computador a 1470 px | 62 quadros por segundo |
| Título, texto e botão | Sem moedas por trás nas capturas |
| Cesta ao rolar | Fica abaixo da barra do topo, sem cortes |
| Enchimento com a página rolada | 14 alimentos, 13 faíscas nas 4 cores, e a Mia reagiu à cesta cheia |
| Tela Cesta | Alimentos calculados caem na cesta nova |
| Largura de 390 px, em um quadro dentro da página | Sem rolagem lateral |
| Tamanho do 3D | Three.js com 144 KB comprimido, mais 193 KB de comida |

## Limitações

- **Celular real:** não foi testado, e a queda de qualidade em aparelhos fracos segue sendo a principal dúvida.
- **Menos movimento:** quem pede menos movimento no sistema vê o 3D sem a chuva, com a cesta cheia e parada. Esse modo foi escrito, mas não foi testado.
- **Aparelhos simples:** desde 05/11/2026 o 3D fica sempre ligado, então também é baixado com economia de dados, 2G e pouca memória. Se a cena ficar abaixo de 24 quadros por segundo, a resolução cai, mas ela não desliga.
- **Movimento a olho:** os testes conferem capturas e contagens. A suavidade precisa ser avaliada por uma pessoa.
- **Faísca:** com a página no topo, o cartão de anéis costuma estar fora da tela, e por isso nem toda comida gera faísca.
