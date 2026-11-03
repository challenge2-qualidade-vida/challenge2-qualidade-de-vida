# Site do projeto (Astro + Starlight)

Site de documentação publicado no GitHub Pages: https://dida0982.github.io/challenge2-qualidade-de-vida/

O conteúdo vem direto da pasta [`docs/`](../docs) na raiz do repositório: não copie arquivos para cá.

- Cada `.md` em `docs/` vira uma página. O título é o primeiro `# Título` do arquivo.
- Links relativos entre documentos (`[x](../decisoes.md)`) funcionam no site e no GitHub.
- Uma pasta `docs/semana-N/` aparece no menu assim que tiver um `.md`.
- A paleta de cores fica em [`src/styles/paleta.css`](src/styles/paleta.css).

## Rodar localmente

Requer Node 22+.

```sh
cd site
npm install
npm run dev      # http://localhost:4321/challenge2-qualidade-de-vida/
npm run build    # gera site/dist/
```

## Deploy

O workflow [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) publica o site a cada push na `main` que altere `docs/` ou `site/`.
No GitHub, ative em **Settings → Pages → Source: GitHub Actions** (uma vez só).
