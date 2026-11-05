# Tudo o que foi usado no front da EconoMIA

Situação em 05/11/2026, na branch `develop_gui`, incluindo o [tópico 26](desenvolvimento/26-abertura-3d.md). O como e o porquê de cada parte estão nos tópicos de [docs/desenvolvimento/](desenvolvimento/README.md).

**Resumo:** o site é feito em HTML, CSS e JavaScript puros, sem framework e sem etapa de build. O FastAPI entrega os arquivos de `src/web/` e responde à API. Todas as ferramentas usadas são gratuitas.

## Linguagens e formatos

| Linguagem | Onde | Para quê |
|-----------|------|----------|
| HTML5 | `src/web/index.html` (438 linhas) | Estrutura das telas |
| CSS3 | `src/web/estilo.css` (958 linhas) | Visual, temas, layout responsivo |
| JavaScript | `app.js` (1059), `cena3d.js` (388), `gatos.js` (243), `animacoes.js` (73), `sw.js` (33) | Telas, 3D, gatos, animações, modo sem internet |
| GLSL ES 3.00 | Dentro de `gatos.js` | Shader que movimenta os gatos |
| JSON | `manifest.webmanifest` | Dados do app instalável |
| Python | `experimentos/gatos3d/`, `src/economia/api.py` | Preparar as imagens dos gatos e servir o site |
| YAML | `.github/workflows/testes.yml` | Testes automáticos no GitHub |
| Markdown | `docs/` | Documentação |

## Arquivos do site

| Arquivo | Papel | Tópico |
|---------|-------|--------|
| `index.html` | Todas as telas em uma página só | [5](desenvolvimento/README.md), [14](desenvolvimento/14-interface-app.md) |
| `estilo.css` | Cores, temas claro e escuro, layout | [23](desenvolvimento/23-layout-responsivo.md), [25](desenvolvimento/25-gatos-3d.md) |
| `app.js` | Navegação, formulários, chamadas à API | [5](desenvolvimento/README.md) |
| `cena3d.js` | Moedas, cesta com comida, radar e cupom em 3D | [24](desenvolvimento/24-visual-3d.md) |
| `animacoes.js` | Abertura, rolagem e animação da cesta | [24](desenvolvimento/24-visual-3d.md) |
| `gatos.js` | Gatos que respiram, piscam e olham para o cursor | [25](desenvolvimento/25-gatos-3d.md) |
| `sw.js`, `manifest.webmanifest` | App instalável e abertura sem internet | [20](desenvolvimento/20-pwa-e-protecao.md) |
| `vendor/` | Cópias locais das bibliotecas | [24](desenvolvimento/24-visual-3d.md) |
| `img/` | Gatos, logo, ícones e fotos de alimentos | [17](desenvolvimento/17-fotos-alimentos.md), [25](desenvolvimento/25-gatos-3d.md) |

## Bibliotecas que rodam no site

Ficam em `src/web/vendor/`, então o site não depende de outro servidor para usá-las.

| Biblioteca | Versão | Para quê | Licença |
|------------|--------|----------|---------|
| [Three.js](https://threejs.org) | r187 | Cena 3D. Reduzida às classes usadas e baixada só em aparelhos que aguentam | MIT |
| [GSAP](https://gsap.com) | 3.15.0 | Animações | [Gratuita, com regras próprias](https://gsap.com/standard-license/) |
| ScrollTrigger (do GSAP) | 3.15.0 | Animações ligadas à rolagem | Igual à do GSAP |
| [Lenis](https://github.com/darkroomengineering/lenis) | 1.3.27 | Rolagem suave com mouse | MIT |

## Serviços externos usados pelo site

| Serviço | Para quê | Sem ele |
|---------|----------|---------|
| [Google Fonts](https://fonts.google.com): Fredoka (títulos) e Nunito (textos) | Fontes | O site usa uma fonte do sistema |

## Recursos do navegador

| Recurso | Para quê |
|---------|----------|
| WebGL | 3D do Three.js |
| Web Animations (`element.animate`) | Faísca que voa até o anel de nutrição |
| WebGL 2 e Canvas 2D | Movimento dos gatos, com um só contexto compartilhado |
| Service Worker e Cache | Abrir sem internet |
| Web App Manifest | Instalar como app |
| localStorage | Última cesta e preferências, só no aparelho |
| Geolocation | Mercados por perto |
| `<input type="file" capture>` | Foto do cupom |
| Fetch | Chamadas à API |
| View Transitions | Troca suave de tela, quando o navegador tem |
| Pointer Events | Posição do cursor |
| `matchMedia` | Menos movimento, tema do sistema e tipo de ponteiro |
| `navigator.connection` | Economia de dados e internet lenta |
| MutationObserver | Animar o cardápio quando ele aparece |

## Recursos de CSS

Variáveis (`--nome`), Grid, Flexbox, 16 blocos de `@media`, `prefers-color-scheme`, `prefers-reduced-motion`, `backdrop-filter`, `env(safe-area-inset-*)`, `@keyframes`, `:is()` e `filter: drop-shadow`.

Também há `<meta name="darkreader-lock">`, que impede a extensão Dark Reader de recolorir o site.

## Como o site é servido e testado

| Ferramenta | Versão | Para quê |
|------------|--------|----------|
| [FastAPI](https://fastapi.tiangolo.com) (`StaticFiles`, `GZipMiddleware`) | 0.162.0 | Entrega e comprime os arquivos e responde à API |
| [Uvicorn](https://www.uvicorn.org) | 0.54.0 | Servidor local |
| pytest | 9.2.0 | 223 testes do projeto, incluindo os que conferem arquivos do site |
| GitHub Actions | `testes.yml` | Roda os testes a cada envio |
| Chrome, com a extensão Claude in Chrome | Não se aplica | Conferência visual, console e larguras de tela |

## Ferramentas usadas para criar arquivos

Nada disto roda no site. São ferramentas usadas durante o desenvolvimento.

| Ferramenta | Versão | Para quê | Licença |
|------------|--------|----------|---------|
| [esbuild](https://esbuild.github.io), via `npx` | Não registrada | Gerar o Three.js reduzido | MIT |
| [Pillow](https://python-pillow.org) | 13.0.0 | Redimensionar, cortar e salvar em WebP | MIT-CMU |
| [NumPy](https://numpy.org) e [SciPy](https://scipy.org) | NumPy 2.5.4 e SciPy 1.18.1 | Recorte dos gatos | BSD |
| [FLUX.1 schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell) | Versão de 4 bits no Mac | Gerar as imagens dos gatos | Apache 2.0 |
| [Hugging Face Spaces](https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell) | Não se aplica | Rodar o FLUX online, sem conta (Mia) | Não se aplica |
| [mflux](https://github.com/mflux-community/mflux) e MLX | 0.24.0 e 0.32.4 | Rodar o FLUX no Mac (Cifrão, Miau-ricio, Recibaldo) | MIT |
| [rembg](https://github.com/danielgatis/rembg) e ONNX Runtime | 2.0.86 e 1.31.1 | Máscara do recorte, com os modelos `isnet-general-use` (gatos) e `birefnet-general-lite` (alimentos) | MIT |
| [uv](https://docs.astral.sh/uv/) | Não registrada | Ambiente temporário em Python 3.12 para o mflux | MIT ou Apache 2.0 |
| [API da Wikimedia Commons](https://commons.wikimedia.org) | Não se aplica | Fotos de alimentos, com créditos em [creditos-fotos-alimentos.md](marca/creditos-fotos-alimentos.md) | Varia por foto |
| Claude Code | Não se aplica | Escrever o código, os testes e a documentação | Não se aplica |

Scripts em `experimentos/gatos3d/`: `gerar_imagem.py`, `recorte.py`, `turma.py`, `logo.py` e `comida.py`.

## Testado e deixado de fora

| Ferramenta | O que aconteceu |
|------------|-----------------|
| [Blender](https://www.blender.org) 5.2.3, com Cycles | Primeira versão da Mia. O resultado foi reprovado e os scripts saíram do projeto, mas continuam no histórico do git |
| [Pollinations](https://pollinations.ai) | Gerador de imagens sem conta. Testado uma vez; veio com marca d'água e qualidade fraca |
| Fotos de `img/alimentos` na cena 3D | Avaliadas para a chuva de comida; são quadradas e têm fundo, então continuam só nas listas |

## Instalados, sem nada no site

| Ferramenta | Situação |
|------------|----------|
| Plugin [frontend-design](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design) (Claude Code) | Instalado. Serviu de orientação de design no [tópico 24](desenvolvimento/24-visual-3d.md); não adiciona código ao site |
| [Magic UI](https://magicui.design) (MCP) | Configurado. Nenhum componente usado, porque é feito para React |
| [21st.dev](https://21st.dev) (MCP `magic`) | Removido em 05/11/2026: não conectava e nenhum componente foi usado, porque é feito para React |

## Referências visuais

Só serviram de inspiração. Nenhuma imagem delas está no projeto.

- [Pawzo](https://pawzo.netlify.app/): origem da paleta mostarda e creme e do estilo dos personagens.
- Pins do Pinterest no estilo "3D cartoon estilizado", enviados pelo Guilherme.
- [Pesquisa de design e animações](marca/pesquisa-design-animacoes.md): sites, técnicas e ferramentas pesquisadas.

## Imagens

| Imagem | Origem |
|--------|--------|
| Gatos, turma, logo e ícones | Gerados por IA com FLUX.1 schnell e montados pelos scripts acima |
| Alimentos da cena 3D (`img/comida.webp`) | Gerados por IA com FLUX.1 schnell, recortados com o modelo `birefnet-general-lite` |
| Nome "EconoMIA" no logo | Arte original, em `src/web/img/logo-nome.png` |
| Desenhos verdes antigos | Guardados em `docs/marca/` |
| Alimentos nas listas | Fotos da Wikimedia Commons |
| Ícones da navegação | SVGs escritos à mão no HTML |
| Moedas, cesta, radar e cupom em 3D | Criados por código em `cena3d.js`, sem arquivos de modelo |

## Decisões que valem para o front todo

- **Sem framework:** o site roda como está, sem instalar nem compilar nada. Por isso, bibliotecas feitas para React ficaram de fora.
- **Aparelhos simples:** o 3D não é baixado com economia de dados, internet 2G, pouca memória, poucos núcleos, menos movimento pedido ou sem WebGL.
- **Privacidade:** a posição e as respostas do chat não entram no cache do site.

As decisões completas estão em [decisoes.md](decisoes.md).
