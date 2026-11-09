# Spec: coleta da base de conhecimento

| Campo | Valor |
| --- | --- |
| Issue | #16 |
| Status | Rascunho |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema
O RAG precisa de fontes confiáveis, rastreáveis e compatíveis com o uso previsto pelo projeto.

## Comportamento esperado
Manter documentos em `data/base-conhecimento/` e registrar cada fonte em `FONTES.md`, com arquivo, título, instituição, ano, URL, tipo de conteúdo, situação da licença/permissão e justificativa de confiabilidade.

## Termos do domínio
`Fonte`, `Trecho`, `Receita`, `Alimento`.

## Regras de negócio
- RN10: respostas baseadas na base citam a fonte.
- RN11: sem informação, o sistema informa que não encontrou, sem inventar.
- RN04: a base não é fonte de preço atual.

## Entradas e saídas
Entrada: documentos de fontes públicas e oficiais e metadados verificados.
Saída: arquivos preservados em `data/base-conhecimento/` e catálogo `FONTES.md`.

## Fora do escopo
Indexação vetorial, embeddings, recuperação semântica e preços atuais.

## Critérios de aceitação
Ver `cenarios.feature`.

## Dependências
Épico #15; verificação de fontes/licenças; issue #17.

## Riscos e limitações
Acesso público não significa licença aberta. Nenhum documento será redistribuído sem verificação de licença, termos e atribuição.
