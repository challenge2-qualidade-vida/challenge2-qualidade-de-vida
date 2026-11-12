# Challenge 2 — Big Idea: Qualidade de Vida

Residência em IA Brasília (TIC em Trilhas / Mentes em Modo IA em Ação) — Turma 2

> **Big Idea:** empoderar pessoas com IA para compreender melhor, decidir melhor e viver melhor.

## Desafio

Projetar e desenvolver uma solução baseada em IA capaz de apoiar a tomada de decisão em um contexto relacionado à qualidade de vida.

**Essential Question do grupo:** Como podemos utilizar inteligência artificial para otimizar o orçamento de compras e reduzir o desperdício de alimentos por meio da gestão automatizada de inventário doméstico e rastreamento de preços locais?

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

Documentação publicada em **[https://dida0982.github.io/challenge2-qualidade-de-vida/](https://dida0982.github.io/challenge2-qualidade-de-vida/)** (gerada a partir de `docs/` com Astro + Starlight). Veja [site/README.md](site/README.md).

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

```text
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

A arquitetura e as pastas previstas (`prompts/`, `migracoes/`, `frontend/`) estão na [visão geral da arquitetura](docs/arquitetura/visao-geral.md).

## Estrutura do backend

O backend do EconoMIA segue uma arquitetura de monólito modular, organizada por contextos de negócio.

```text
src/
└── economia/
    ├── compartilhado/
    ├── planejamento/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── precos/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── receitas/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── leitura_documentos/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── verificacao/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── conversa/
    │   ├── dominio/
    │   ├── aplicacao/
    │   └── infraestrutura/
    ├── api/
    └── worker/
```

Cada contexto de negócio possui três camadas:

- `dominio`: regras e conceitos de negócio.
- `aplicacao`: casos de uso e orquestração.
- `infraestrutura`: integrações e detalhes técnicos.

O diretório `compartilhado` reúne elementos utilizados por diferentes contextos. A API e o worker são pontos de entrada distintos que utilizam o mesmo código do backend.

A camada `dominio` não deve importar componentes de infraestrutura, frameworks ou bibliotecas de LLM.

## Como executar o projeto localmente

Este guia explica como preparar o ambiente e executar os serviços do EconoMIA no seu computador, mesmo que você ainda não tenha trabalhado com o projeto.

### 1. Pré-requisitos

Antes de começar, instale as seguintes ferramentas:

- **Git:** permite baixar o código do GitHub. [Instruções de instalação](https://git-scm.com/downloads).
- **Python:** versão 3.11 ou superior, inferior à 4.0. [Download do Python](https://www.python.org/downloads/).
- **Poetry:** ferramenta utilizada para instalar e gerenciar as dependências Python. [Instalação do Poetry](https://python-poetry.org/docs/#installation).
- **Docker Desktop:** permite executar serviços em contêineres, como o Qdrant. [Download do Docker Desktop](https://www.docker.com/products/docker-desktop/).

Após instalar o Docker Desktop, abra o programa e aguarde até que o Docker esteja em execução.

### 2. Baixar o projeto

Abra o terminal do seu computador.

Copie e execute o comando abaixo para baixar o repositório:

```bash
git clone https://github.com/challenge2-qualidade-de-vida/challenge2-qualidade-de-vida.git
```

Entre na pasta do projeto:

```bash
cd challenge2-qualidade-de-vida
```

### 3. Instalar as dependências

Com o terminal aberto na pasta do projeto, execute:

```bash
poetry install
```

Esse comando instala as bibliotecas necessárias e prepara o ambiente virtual utilizado pelo projeto.

Aguarde a conclusão da instalação antes de continuar.

### 4. Configurar as variáveis de ambiente (opcional)

O projeto disponibiliza o arquivo `.env.example`, que contém configurações de referência.

Para criar seu próprio arquivo de configuração, execute:

```bash
cp .env.example .env
```

Essa etapa é opcional para iniciar a API e testar o endpoint de saúde. Outros módulos podem utilizar essas configurações.

### 5. Iniciar o Qdrant

O Qdrant é o banco de dados vetorial utilizado pelo projeto para armazenamento e recuperação de informações.

Certifique-se de que o Docker Desktop esteja aberto e em execução.

Na pasta do projeto, execute:

```bash
docker compose up -d
```

Esse comando inicia os serviços definidos no arquivo `docker-compose.yml`.

Para verificar se o Qdrant está em execução:

```bash
docker compose ps
```

Agora teste a disponibilidade do serviço:

```bash
curl http://localhost:6333/healthz
```

A resposta esperada é:

```text
healthz check passed
```

### 6. Iniciar a API

A API é executada localmente pelo Poetry.

No terminal, ainda dentro da pasta do projeto, execute:

```bash
poetry run uvicorn economia.api.main:app --reload
```

Mantenha esse terminal aberto enquanto estiver utilizando a API.

A opção `--reload` permite que o servidor reinicie automaticamente quando houver alterações no código.

Se aparecer o erro `Address already in use`, significa que a porta 8000 já está sendo utilizada. Antes de tentar iniciar outra instância, abra o endereço http://localhost:8000/health no navegador. Se a resposta for `{"status":"ok"}`, a API já está funcionando. Caso contrário, verifique se existe outro servidor em execução e encerre-o pelo terminal em que foi iniciado, pressionando `Ctrl + C`.

### 7. Verificar se a API está funcionando

Com a API em execução, abra o navegador e acesse:

http://localhost:8000/health

A resposta esperada é:

```json
{"status":"ok"}
```

Se essa resposta aparecer, a API está funcionando.

### 8. Executar os testes

Para verificar se os testes automatizados do projeto estão passando, abra outro terminal, entre novamente na pasta do repositório e execute:

```bash
poetry run pytest
```

O pytest apresentará o resultado dos testes executados.

### 9. Verificar a qualidade do código

Para executar a verificação estática de código com Ruff:

```bash
poetry run ruff check .
```

Quando todas as verificações forem aprovadas, o resultado esperado será:

```text
All checks passed!
```

### 10. Encerrar os serviços

Quando terminar de utilizar o projeto:

1. No terminal em que a API está executando, pressione `Ctrl + C`.
2. Na pasta do projeto, execute:

```bash
docker compose down
```

Esse comando encerra os serviços iniciados pelo Docker Compose. Os dados armazenados nos volumes persistentes são preservados.

### Observação sobre a configuração atual

Atualmente, o Docker Compose disponibiliza o Qdrant. A API é iniciada separadamente pelo Poetry, conforme as instruções deste guia.

## Como trabalhar no repositório

Veja [CONTRIBUTING.md](CONTRIBUTING.md).
