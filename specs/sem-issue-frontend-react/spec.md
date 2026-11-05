# Spec: frontend da EconoMIA em React

| Campo | Valor |
| --- | --- |
| Issue | Sem issue (nome provisório; a issue precisa ser criada pela equipe) |
| Status | Em revisão |
| Contexto delimitado | Todos (interface) |
| Agente | Nenhum |

## Problema

O site da EconoMIA, aprovado pelo grupo, foi feito na `develop_gui` antes das decisões técnicas. Ele usa HTML, CSS e JavaScript puros, chama a API à mão e não segue a organização, o contrato nem as convenções da `main`. Por isso, não encaixa no projeto da equipe.

## Comportamento esperado

O site novo, em `frontend/`, tem **a mesma aparência** do site de `src/web/` no commit `e149814` (tag local `referencia-visual-antigo`): mesmas telas, textos, gatos, cena 3D e animações, com o tema escuro e a navegação inferior no celular e lateral no computador. Por dentro, segue as decisões do grupo:

- React, Vite e TypeScript, como app separado que consome a API.
- Cliente da API gerado do OpenAPI, sob `/api/v1`, com `openapi-typescript` e `openapi-fetch`.
- Erros da API em Problem Details (RFC 9457), tratados num só lugar.
- Conversa com resposta em streaming SSE, lida com `fetch`.
- Notificações por consulta periódica.
- Login com e-mail e senha, token de acesso de 15 minutos e de renovação de 7 dias, com as telas Entrar e Criar conta no mesmo estilo.
- Dados falsos tipados pelo mesmo cliente, ligados por variável de ambiente, enquanto o backend não tem as rotas.
- Funcionalidades fora do MVP atrás de flags desligadas por padrão.

## Termos do domínio

Orçamento (`Orcamento`), Período (`Periodo`), Casa, Restrição (`Restricao`), Lista de compras, Item da lista, Estabelecimento, Preço (`Preco`), Preço por unidade, Ingredientes disponíveis, Receita, Nota fiscal (`NotaFiscal`), Item extraído (`ItemExtraido`), Revisão, Pedido, Conversa, Notificação (`Notificacao`), Limitação, Fonte.

A tela usa ainda "cesta", "metas nutricionais" e "mercado", que vêm do protótipo e não estão no modelo de domínio. Os componentes usam os termos do modelo quando eles existem.

## Regras de negócio

- RN01: o frontend nunca calcula preço nem soma de compra; só exibe o que a API devolve.
- RN02 e RN03: todo preço exibido mostra data e fonte, quando a API envia.
- RN13: os ingredientes de casa valem só para o pedido.
- Dinheiro em centavos no contrato, formatado em reais só na tela.

## Entradas e saídas

Ver `frontend/openapi/provisorio.yaml`. Os contratos que ainda faltam no backend estão listados em `frontend/README.md`.

## Fora do escopo

- Mudanças de visual, texto ou animação.
- Backend, issues e PRs dos colegas.
- Apagar `src/web/` antes da aprovação do Guilherme.
- Central de notificações com tela: só a consulta periódica entra agora.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature). São verificados pelos testes do Playwright em `frontend/testes/`, porque dependem do navegador. O pytest-bdd do grupo cobre o backend.

## Dependências

Decisões do frontend em `docs/decisoes.md`, na seção "Frontend em React". Contratos da API a combinar com o backend.

## Riscos e limitações

- A cena 3D e as animações variam com o tempo. A comparação visual congela o movimento, e o 3D é conferido à mão.
- Os dados falsos vêm das respostas do protótipo e podem divergir do contrato final do backend.
