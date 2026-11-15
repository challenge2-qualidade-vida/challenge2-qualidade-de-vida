# Spec: Containerização da API e do banco de dados

| Campo | Valor |
| --- | --- |
| Issue | #38 |
| Status | Rascunho |
| Contexto delimitado | Transversal — infraestrutura de execução do backend |
| Agente | Não se aplica |

## Problema

O backend do EconoMIA precisa de um ambiente de execução padronizado, que permita iniciar a API e o banco de dados localmente sem exigir a instalação e configuração manual desses serviços na máquina de cada pessoa desenvolvedora.

Atualmente, o Docker Compose disponibiliza apenas o Qdrant. É necessário ampliar a infraestrutura para incluir a API e o PostgreSQL.

## Comportamento esperado

A pessoa desenvolvedora deve conseguir iniciar a API e o PostgreSQL por meio do Docker Compose.

A imagem da API deve ser construída a partir do código do projeto, utilizando as dependências gerenciadas pelo Poetry.

O PostgreSQL deve estar disponível para a API pela rede interna do Docker.

O serviço Qdrant existente deve continuar disponível, preservando seu volume de dados.

## Termos do domínio

Não se aplica diretamente. Esta entrega trata da infraestrutura de execução da aplicação.

## Regras de negócio

Não se aplica. A issue não implementa regras de negócio.

## Entradas e saídas

**Entradas:**
- Código-fonte do backend;
- Dependências declaradas no `pyproject.toml` e registradas no `poetry.lock`;
- Configurações de ambiente;
- Configuração dos serviços no Docker Compose.

**Saídas:**
- Dockerfile da API;
- Docker Compose com API, PostgreSQL e Qdrant;
- Volume persistente para os dados do PostgreSQL;
- Comunicação entre API e PostgreSQL pela rede interna do Docker.

## Fora do escopo

- Implementação de funcionalidades de negócio;
- Implementação de novos endpoints;
- Implementação do worker e da fila Redis;
- Containerização do frontend;
- Configuração do Caddy e HTTPS;
- Deploy na VM de produção;
- Implementação das migrações SQL do Flyway.

## Critérios de aceitação

Cenários descritos em [cenarios.feature](cenarios.feature).

## Dependências

- Issue #31 — definição da stack tecnológica;
- Issue #36 — estrutura inicial do backend;
- Issue #37 — implementação da API e do healthcheck;
- Decisões arquiteturais documentadas em `docs/arquitetura/`;
- Decisão de uso do PostgreSQL e Docker Compose registrada em `docs/decisoes.md`.

## Riscos e limitações

- A construção da imagem da API depende da disponibilidade do código da API na branch de integração.
- Os serviços devem utilizar endereços compatíveis com a rede interna do Docker.
- Os dados do PostgreSQL devem permanecer disponíveis após a recriação do contêiner.
- A disponibilidade do contêiner do banco não garante, isoladamente, que a API esteja pronta para receber requisições.
