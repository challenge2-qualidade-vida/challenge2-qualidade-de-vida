# Bibliotecas de animação e 3D

Cópias locais, para o site não depender de outro servidor. Usadas por `animacoes.js` e `cena3d.js`.

| Biblioteca | Versão | Arquivos | Licença |
|------------|--------|----------|---------|
| [GSAP](https://gsap.com) | 3.15.0 | `gsap.min.js`, `ScrollTrigger.min.js` | [Gratuita, com regras próprias](https://gsap.com/standard-license/) |
| [Lenis](https://github.com/darkroomengineering/lenis) | 1.3.27 | `lenis.min.js` | MIT |
| [Three.js](https://threejs.org) | 0.187.0 | `three.min.js` | MIT |

`three.min.js` tem só as classes listadas em `three-entrada.js`. Para adicionar outra, inclua o nome nesse arquivo e gere de novo, com o pacote `three` instalado:

```bash
npx esbuild three-entrada.js --bundle --minify --format=esm --legal-comments=none --outfile=three.min.js
```

O arquivo tem 550 KB, ou 137 KB comprimido, e só é baixado quando o aparelho pode mostrar o 3D.
