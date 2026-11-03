# Tópico 24 — Visual com 3D e animações

**Status:** ✅ concluído em 03/11/2026

O grupo escolheu o caminho de maior impacto, com 3D em várias telas. A referência foi a [pesquisa de design](../marca/pesquisa-design-animacoes.md) e as orientações do plugin `frontend-design`.

## A ideia

**Moedas viram comida e caem na cesta.** O título "Faça o dinheiro do mercado render" e as cores vêm da marca: verde-floresta, ouro e os gatos do grupo.

| Tela | O que acontece |
|------|----------------|
| Início | Chuva de moedas em 3D. Ao rolar, as moedas entram na cesta e viram comida. A Mia entra pulando, e os gatos seguem o mouse |
| Cesta | **Os alimentos da cesta calculada** caem em uma cesta 3D. Se couber no orçamento, moedas saltam dela. O total sobe contando |
| Perto | Radar 3D com pinos. É decorativo: os pinos não mostram mercados reais |
| Cupom | Cupom 3D com um feixe de leitura |
| Preços | Moeda grande girando |
| Mia e Configurações | Poucas moedas nas beiradas, para não atrapalhar a leitura |

## Como funciona

| Arquivo | Papel |
|---------|-------|
| [cena3d.js](../../src/web/cena3d.js) | Cena em Three.js, com modelos feitos por código, sem baixar arquivos 3D |
| [animacoes.js](../../src/web/animacoes.js) | Abertura, rolagem e cesta animada, com GSAP e Lenis |
| [app.js](../../src/web/app.js) | Avisa a tela aberta e os alimentos da cesta, em `window.economia` e nos eventos `economia:aba` e `economia:cesta` |
| [vendor/](../../src/web/vendor/README.md) | Cópias locais das bibliotecas |

O canvas fica fixo atrás do site, e cada objeto segue um "palco" do HTML (`#palco-cesta`, por exemplo). Por isso, ele rola junto com a página e acompanha o tamanho da tela.

## Cuidados com quem tem celular simples

- **Quando o 3D fica desligado:** com economia de dados, internet 2G, 2 GB de memória ou menos, 2 núcleos ou menos, pedido de menos movimento ou sem WebGL. Nesses casos, o Three.js nem é baixado.
- **Tamanho:** o Three.js foi reduzido de 2 MB para 550 KB, ou 137 KB comprimido. O servidor agora comprime os arquivos.
- **Se ficar lento:** abaixo de 24 quadros por segundo, a resolução cai; se continuar, o 3D desliga sozinho.
- **Escolha da pessoa:** Configurações → Efeitos 3D (Automático, Ligado ou Desligado).
- **Acessibilidade:** o título mantém o texto para leitores de tela, e o site funciona se as animações falharem.

## Como foi testado

No Chrome, em computador:

| Teste | Resultado |
|-------|-----------|
| Telas Início, Cesta, Perto, Cupom e Preços, nos dois temas de cor | Conferidas em capturas (nos dois temas, a tela Início) |
| Velocidade | 61 quadros por segundo nesta máquina |
| 3D desligado | Sem canvas, sem baixar o Three.js, e a cesta funciona |
| Larguras de 320, 390, 768, 1024 e 1440 px | Sem rolagem horizontal |
| Testes automáticos | 222 passando |
| Compressão | Three.js entregue com 140 KB |

## Limitações

- **Não foi testado em celular de verdade.** O desempenho em aparelhos simples é a principal dúvida, então vale testar em um antes da apresentação.
- Com "Ligado", o 3D funciona mesmo com pedido de menos movimento no sistema, porque é uma escolha explícita. As animações de GSAP continuam desligadas.
- Os gatos são imagens planas com efeito de profundidade, não modelos 3D. Modelar exigiria o Blender e bastante trabalho de arte.
- O efeito de vidro e o 3D gastam mais bateria.
- A fonte Fredoka vem do Google Fonts, como a Nunito. Sem internet, o site usa uma fonte do sistema.
