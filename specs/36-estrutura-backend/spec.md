# Spec: Estrutura inicial do backend e gerenciamento de dependências

| Campo | Valor |
| --- | --- |
| Issue | #36 |
| Status | Em revisão |
| Contexto delimitado | Transversal — estrutura técnica do backend |
| Agente | Não se aplica |

## Problema

O projeto precisa de uma estrutura inicial padronizada para organizar o código do backend, separar responsabilidades e permitir a evolução dos módulos sem comprometer a organização da aplicação.

Também é necessário estabelecer um mecanismo centralizado para declarar, instalar e gerenciar as dependências do projeto.

## Comportamento esperado

O repositório deve disponibilizar uma estrutura modular de backend em `src/economia/`, organizada em contextos e camadas.

A estrutura deve contemplar:

- Diretório compartilhado;
- Contextos de negócio: planejamento, preços, receitas, leitura de documentos, verificação e conversa;
- Camadas de domínio, aplicação e infraestrutura nos contextos;
- Diretórios de API e worker.

O Poetry deve gerenciar as dependências, com as dependências de execução e desenvolvimento declaradas no `pyproject.toml` e suas versões registradas no `poetry.lock`.

## Termos do domínio

Não se aplica diretamente. Esta entrega estabelece a estrutura técnica do backend e não introduz novos conceitos de negócio.

## Regras de negócio

Não se aplica. A issue não implementa regras de negócio.

## Entradas e saídas

**Entradas:**
- Código-fonte do backend;
- Definições de dependências no `pyproject.toml`.

**Saídas:**
- Estrutura modular de diretórios em `src/economia/`;
- Arquivo `pyproject.toml` configurado;
- Arquivo `poetry.lock` gerado;
- Documentação da estrutura no README.

## Fora do escopo

- Implementação de funcionalidades de negócio;
- Implementação de endpoints da API;
- Implementação de agentes de IA;
- Integração com bancos de dados;
- Implementação de filas e workers;
- Configuração de infraestrutura de execução e deploy.

## Critérios de aceitação

Cenários descritos em [cenarios.feature](cenarios.feature).

## Dependências

- Issue #31 — definição da stack tecnológica;
- Issue #35 — épico de estrutura inicial da aplicação;
- Decisões arquiteturais documentadas em `docs/arquitetura/`.

## Riscos e limitações

- A estrutura inicial poderá ser ajustada conforme a implementação dos módulos.
- A existência dos diretórios não representa funcionalidades implementadas.
- As dependências de serviços externos e infraestrutura poderão ser adicionadas em etapas posteriores.
