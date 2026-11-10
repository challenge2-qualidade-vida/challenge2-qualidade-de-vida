# Spec: API mínima e rota de healthcheck

| Campo | Valor |
| --- | --- |
| Issue | #37 |
| Status | Em revisão |
| Contexto delimitado | Transversal — API do backend |
| Agente | Não se aplica |

## Problema

O backend precisa disponibilizar uma API inicial para permitir que outros componentes e serviços verifiquem se a aplicação está em execução.

## Comportamento esperado

A aplicação deve disponibilizar uma API construída com FastAPI.

A API deve possuir uma rota de healthcheck:

- Método HTTP: GET;
- Caminho: `/health`;
- Código de resposta: 200;
- Corpo da resposta: `{"status": "ok"}`.

A rota deve indicar que a aplicação está funcionando, sem depender da disponibilidade de serviços externos.

## Termos do domínio

Não se aplica diretamente. O healthcheck representa uma verificação técnica da disponibilidade da aplicação.

## Regras de negócio

Não se aplica. A rota não executa regras de negócio.

## Entradas e saídas

**Entradas:**
- Requisição HTTP GET para `/health`.

**Saídas:**
- Resposta HTTP 200;
- JSON contendo o campo `status` com o valor `ok`.

## Fora do escopo

- Verificação de disponibilidade do Qdrant;
- Verificação de disponibilidade do Ollama;
- Autenticação e autorização;
- Implementação de endpoints de negócio;
- Monitoramento avançado e métricas.

## Critérios de aceitação

Cenários descritos em [cenarios.feature](cenarios.feature).

## Dependências

- Issue #31 — definição da stack tecnológica;
- Issue #35 — épico de estrutura inicial da aplicação;
- Issue #36 — estrutura inicial do backend;
- Issue #39 — configuração das variáveis de ambiente.

## Riscos e limitações

- A rota verifica apenas se a aplicação responde.
- Uma resposta positiva não garante que serviços externos estejam disponíveis.
