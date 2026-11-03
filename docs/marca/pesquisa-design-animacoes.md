# Pesquisa de design, animação e 3D

Pesquisa feita em 03/11/2026 para deixar o site mais bonito. Nada disto foi aplicado ainda. Os sites servem de inspiração: a ideia é criar algo próprio, sem copiar telas nem marcas.

## Referências

| Site | O que observar |
|------|----------------|
| [Zepto](https://www.zepto.com.au/) ([Awwwards](https://www.awwwards.com/sites/zepto)) | A mais próxima da EconoMIA: mascote e 3D interativo deixando finanças amigáveis |
| [The Tiny Pod](https://thetinypod.com/) | Produto em 3D que conta uma história durante a rolagem |
| [Lando Norris](https://landonorris.com/) | 3D imersivo e movimento forte |
| [Monolith Studio](https://monolithstudio.com/) | 3D a serviço da narrativa |
| [Huly](https://huly.io/) e [AuthKit](https://www.authkit.com/) | Luz, materiais e brilho |
| [Made with GSAP](https://madewithgsap.com/) e [vitrine do GSAP](https://gsap.com/showcase/) | Catálogos de efeitos |
| [Duolingo](https://blog.duolingo.com/world-character-visemes) | Personagens que reagem ao que o usuário faz |

As fontes concordam em um ponto: a animação precisa explicar ou dar retorno ao usuário, não só enfeitar ([Digidop](https://www.digidop.com/blog/5-web-design-trends-2025/index.md), [Figma](https://www.figma.com/resource-library/web-design-trends/)).

## Ferramentas

| Ferramenta | Uso | Custo | Observação |
|------------|-----|-------|------------|
| [GSAP](https://gsap.com/standard-license/) | Animações e rolagem | Grátis, inclusive os plugins | Funciona com HTML puro |
| [Lenis](https://github.com/darkroomengineering/lenis) | Rolagem suave | Grátis (MIT) | Respeita o pedido de movimento reduzido |
| Three.js | 3D no navegador | Grátis | Mais código e mais peso |
| CSS e View Transitions | Transições entre telas | Grátis | [Já nos navegadores principais](https://developer.mozilla.org/docs/Web/API/ViewTransition) |
| [Spline](https://spline.design/pricing) | Editor 3D visual | Grátis com marca d'água | Remover exige plano pago |
| [Rive](https://rive.app/pricing) | Mascote interativo | Grátis com tela de abertura da Rive | Remover exige plano pago |

## Ferramentas para o Claude

| Ferramenta | Para quê | Situação nesta máquina |
|------------|----------|------------------------|
| [frontend-design](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design) (Anthropic) | Direção visual própria, tipografia, cor e animação | Não instalado |
| Claude in Chrome | Ver o site de verdade e testar | Já em uso |
| Figma e Canva | Trazer designs para o código | Listados na conta |
| Three.js 3D Viewer | Prévia de cenas 3D | Listado na conta |
| [Magic UI](https://playbooks.com/mcp/magic-ui) e [21st.dev](https://lobehub.com/nl/mcp/21st-dev-magic-mcp) | Componentes animados prontos | Exigem Node.js, e são feitos para React. O site usa HTML puro |
| [BlenderMCP](https://agentpedia.codes/mcp/blender) | Modelar os gatos em 3D | Exige instalar o Blender |

## Cuidados

- **Público:** quem usa o app pode ter celular simples e pouco pacote de dados. Animação pesada fica só onde compensa, e o 3D só carrega quando for preciso.
- **Acessibilidade:** respeitar o pedido de movimento reduzido do sistema.
- **Vídeo:** nesta pesquisa não encontramos ganho que justifique o peso em telas de uso. Seria só um trecho curto na abertura.
