# Challenge 2 — Big Idea: Qualidade de Vida

Residência em IA Brasília (TIC em Trilhas / Mentes em Modo IA em Ação) — Turma 2

> **Big Idea:** empoderar pessoas com IA para compreender melhor, decidir melhor e viver melhor.

## Desafio

Projetar e desenvolver uma solução baseada em IA capaz de apoiar a tomada de decisão em um contexto relacionado à qualidade de vida.

**Essential Question do grupo:** _a definir na semana 1_

## Links do projeto

- **Organização:** https://github.com/challenge2-qualidade-vida
- **Repositório:** https://github.com/challenge2-qualidade-vida/challenge2-qualidade-de-vida
- **Quadro de tarefas (GitHub Projects):** https://github.com/orgs/challenge2-qualidade-vida/projects/1

## Equipe

| Foto | Nome | GitHub | Papel |
|------|------|--------|-------|
| <img src="https://github.com/dida0982.png" width="60" alt="Foto de Guilherme Barros"> | Guilherme Barros | [@dida0982](https://github.com/dida0982) | AI Engineering e frontend |
| <img src="https://github.com/gpaulovit.png" width="60" alt="Foto de Paulo Vitor Gomes"> | Paulo Vitor Gomes | [@gpaulovit](https://github.com/gpaulovit) | AI Engineering e LLMOps |
| <img src="https://github.com/iAiBel.png" width="60" alt="Foto de Isabel Azar"> | Isabel Azar | [@iAiBel](https://github.com/iAiBel) | Engenharia de dados e backend |
| <img src="https://github.com/pedrolucasdourado.png" width="60" alt="Foto de Pedro Lucas Dourado"> | Pedro Lucas Dourado | [@pedrolucasdourado](https://github.com/pedrolucasdourado) | Arquiteto de LLMOps |
| <img src="https://github.com/necrophagial.png" width="60" alt="Foto de Mariah Gladys"> | Mariah Gladys | [@necrophagial](https://github.com/necrophagial) | Scrum master e documentação |

## Site

Documentação publicada em **https://dida0982.github.io/challenge2-qualidade-de-vida/** (gerada a partir de `docs/` com Astro + Starlight). Veja [site/README.md](site/README.md).

## Restrições do desafio

- [ ] Entender o problema antes da solução
- [ ] Justificar decisões técnicas
- [ ] Explicitar riscos e limitações
- [ ] Validar com métricas objetivas
- [ ] Utilizar evidências confiáveis

## Roadmap

| Semana | Foco | Entregável principal | Pasta |
|--------|------|----------------------|-------|
| 1 | Problema, stakeholders, riscos e métricas | Definições do projeto | [docs/semana-1](docs/semana-1) |
| 2 | Base de conhecimento e recuperação | Primeiro mecanismo RAG | [docs/semana-2](docs/semana-2) |
| 3 | Comparação LLM x RAG | Respostas baseadas em evidências | [docs/semana-3](docs/semana-3) |
| 4 | Sistema multiagentes | Primeiro sistema multiagentes | [docs/semana-4](docs/semana-4) |
| 5 | Multimodalidade | Agentes multimodais | [docs/semana-5](docs/semana-5) |
| 6 | Integração completa | Aplicação funcional | [docs/semana-6](docs/semana-6) |
| 7 | Testes e refinamento | Relatório final + apresentação | [docs/semana-7](docs/semana-7) |

## Estrutura do repositório

```
docs/                    documentação e entregáveis de cada semana
  arquitetura/           modelo de domínio, visão geral da arquitetura, fluxos e contratos
  produto/               escopo do MVP e priorização
  processo/              fluxo de trabalho e convenções da equipe
  decisoes.md            decisões do projeto, com justificativa e validação
  semana-1/              definições do projeto (problema, stakeholders, riscos, métricas)
  challenge2_resumo.xlsx resumo do desafio
specs/                   specs e cenários BDD de cada funcionalidade
data/base-conhecimento/  documentos e fontes confiáveis usados no RAG
src/economia/            código do backend, um módulo por contexto (ver a visão geral da arquitetura)
notebooks/               experimentos e análises
site/                    site de documentação (Astro + Starlight), publicado no GitHub Pages
tests/                   testes de unidade e passos BDD
```

A arquitetura e as pastas previstas (`prompts/`, `migracoes/`, `frontend/`) estão na [visão geral da arquitetura](docs/arquitetura/visao-geral.md). As pastas do código são criadas na #36.

## Como trabalhar no repositório

Veja [CONTRIBUTING.md](CONTRIBUTING.md).
