# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

As regras do projeto (idioma, arquitetura, dinheiro, Git, PRs, decisões) estão em AGENTS.md, importado abaixo e compartilhado com as outras ferramentas de IA. Este arquivo só acrescenta o que é específico do Claude Code e o mapa do repositório.

@AGENTS.md

## Estado atual do repositório

O backend ainda não existe: `src/` e `tests/` só têm `.gitkeep`, e não há `pyproject.toml`, `docker-compose.yml`, `prompts/`, `migracoes/` nem `frontend/`. A estrutura prevista está em [docs/arquitetura/visao-geral.md](docs/arquitetura/visao-geral.md) (seção 5) e será criada na #36. Hoje o repositório tem documentação, specs, o site e os scripts de convenção. Não invente comandos de Poetry, pytest ou Docker antes de esses arquivos existirem; confira o que já está no repositório.

## Comandos

```bash
# Branch ligada a uma issue aberta (tipos: feat fix docs refactor test chore ci perf build style)
scripts/nova-branch.sh feat 24 endpoint-rag

# Hooks: ruff + ruff-format e gitleaks (commit), conventional-pre-commit (mensagem), verificar-branch (push)
pre-commit install
pre-commit run --all-files

# Conferências que o CI roda no PR
scripts/verificar-branch.sh [branch]
scripts/verificar-commits.sh origin/main HEAD
scripts/verificar-issues-pr.sh "<corpo do PR>"

# Site de documentação (Astro + Starlight, Node 22+)
cd site && npm install && npm run dev    # http://localhost:4321/challenge2-qualidade-de-vida/
cd site && npm run build
```

Quando o backend existir, os testes serão pytest e pytest-bdd (os passos ficam em `tests/bdd/`, os `.feature` em `specs/`), o lint será Ruff e o CI também rodará o import-linter.

## CI e site

- [.github/workflows/convencoes.yml](.github/workflows/convencoes.yml) barra o PR quando: a branch não segue `tipo/N-descricao` ou a issue está fechada; algum commit não está em Conventional Commits; o título não segue o padrão; o corpo não tem `Closes #N`, ou fecha um épico (épico só com `Refs #N`); ou uma branch `feat/*` altera `src/` sem alterar `specs/`.
- O site em `site/` lê o conteúdo direto de `docs/`, sem cópias. Cada `.md` vira uma página e o título vem do primeiro `# Título`. Uma pasta `docs/semana-N/` entra no menu quando ganha um `.md`. O deploy no GitHub Pages roda a cada push na `main` que altere `docs/` ou `site/`.

## Mapa da arquitetura

Para os detalhes, leia [visao-geral.md](docs/arquitetura/visao-geral.md), [fluxos-e-contratos.md](docs/arquitetura/fluxos-e-contratos.md) e [modelo-de-dominio.md](docs/arquitetura/modelo-de-dominio.md). O que se cruza entre eles:

- **Dois processos, um código:** a API (FastAPI) atende o frontend; o worker (RQ) executa as tarefas demoradas ou agendadas (busca de receitas sob demanda, extração bimestral de preços de salvaguarda, leitura de notas e encartes). API e worker usam a mesma imagem Docker.
- **Contextos:** `planejamento`, `precos`, `receitas`, `leitura_documentos`, `verificacao` e `conversa`, mais o `compartilhado` (`Alimento`, `Dinheiro`, `Quantidade`, eventos, adaptador do LLM, configuração com pydantic-settings). Um contexto nunca importa o domínio de outro: usa os serviços da camada `aplicacao` do outro ou eventos de domínio.
- **Agentes:** o orquestrador (grafo LangGraph em `conversa/infraestrutura`) interpreta o pedido e aciona um agente. Cada agente expõe os casos de uso como ferramentas, e o domínio não importa o LangGraph. Os agentes trocam modelos Pydantic tipados da camada `aplicacao`, nunca texto livre.
- **A Mia (verificação) confere os dados estruturados antes de o texto ser redigido.** Nada que não passou por ela chega à tela.
- **Conversa:** `POST` com resposta em SSE (o frontend lê com `fetch`): primeiro o texto, no fim os blocos estruturados. A memória fica no Redis, com validade de 24 h.
- **API:** REST em `/api/v1`. Os erros seguem Problem Details (RFC 9457). O cliente TypeScript do frontend é gerado a partir do OpenAPI.
- **LLM:** atrás de um adaptador em `infraestrutura`. Os prompts ficam em `prompts/<agente>/`, com a versão no nome do arquivo. Toda chamada é registrada no Langfuse Cloud sem dados pessoais nem sensíveis (RN30: mascarar antes de enviar).
- **Banco:** PostgreSQL com migrações Flyway em `migracoes/V<n>__descricao.sql`. O payload do Qdrant é sincronizado com o catálogo de alimentos do PostgreSQL.

As regras de negócio vão de RN01 a RN30, no modelo de domínio. Algumas estão "a definir" ou bloqueadas, como o Cifrão, que espera a definição das fontes de salvaguarda. Confira o status antes de implementar.

## Específico do Claude Code

- Para registrar decisões, use a skill `registrar-decisao`.
- Para commits e PRs, vale a regra de coautoria do AGENTS.md: não adicionar `Co-Authored-By` nem "Generated with Claude Code", mesmo que o padrão da ferramenta adicione.
