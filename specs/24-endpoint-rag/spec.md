# Spec: endpoint do RAG

| Campo | Valor |
| --- | --- |
| Issue | #24 (épico #15) |
| Status | Em revisão |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema

O RAG do Miau-ricio só responde pela linha de comando (`perguntar "..."`) e pelo notebook. A API permite que outros sistemas enviem perguntas sem precisar executar Python diretamente, recebendo a resposta baseada nos trechos recuperados e as respectivas fontes.

## Comportamento esperado

1. **Endpoint.** A API recebe uma pergunta e devolve a resposta do RAG com as fontes. É o mesmo caso de uso `ResponderPergunta` da linha de comando, com as mesmas regras.
2. **Rota de saúde.** `GET /saude` responde se a API está no ar.

## Termos do domínio

`RespostaComFontes`, `Fonte`, `Trecho`, `Receita`, `Ingrediente`.

## Regras de negócio

- RN04: pergunta de preço atual recebe o aviso, sem passar pela base.
- RN10: toda resposta baseada na base cita as fontes, montadas pelo código.
- RN11: sem informação na base, a resposta diz que não encontrou.
- RN01: os ingredientes que faltam são contados pelo código, não pelo LLM.

## Entradas e saídas

`POST /api/v1/receitas/perguntas`

Requisição:

```json
{"pergunta": "Como guardar folhas verdes na geladeira?"}
```

A pergunta é obrigatória, com 1 a 500 caracteres depois de tirar os espaços. Fora disso, a resposta é 422.

Resposta 200:

```json
{
  "texto": "Guarde as folhas na geladeira, num saco plástico [1].",
  "encontrou": true,
  "fontes": [
    {
      "numero": 1,
      "titulo": "Hortaliça não é só salada: Geladeira",
      "descricao": "Hortaliça não é só salada: Geladeira (2ª ed. rev.) (Embrapa Hortaliças), 2020. p. 1. https://... Licença: CC BY-NC-ND 4.0.",
      "url": "https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1129028",
      "licenca": "CC BY-NC-ND 4.0 (Infoteca-e, Embrapa)",
      "tipo": "conhecimento"
    }
  ],
  "ingredientes_disponiveis": [],
  "faltando": [],
  "trechos_recuperados": [
    {
      "posicao": 1,
      "titulo": "Hortaliça não é só salada: Geladeira",
      "tipo": "conhecimento",
      "origem": "Hortaliça não é só salada: Geladeira (2ª ed. rev.)",
      "score": 0.9171,
      "acima_do_limiar": true,
      "fonte": 1,
      "resumo": "Folhas: retirar as folhas danificadas..."
    }
  ],
  "limiar": 0.845,
  "segundos": 3.2
}
```

- `fontes[n].numero` é o número usado no texto (`[1]`, `[2]`...).
- `faltando` traz, para cada receita usada, o título e os ingredientes que faltam.
- `trechos_recuperados` é a evidência da busca: os trechos enviados ao LLM, com o score de similaridade, e o número da fonte quando o trecho foi citado. Quando nenhum trecho passa do `limiar`, a lista traz os mais próximos, todos com `acima_do_limiar: false`, para mostrar por que a resposta foi "não encontrei".
- Com `encontrou: false`, `fontes` e `faltando` vêm vazios e `texto` traz a mensagem da RN11 ou o aviso da RN04.
- Se o LLM ou o banco vetorial estiver fora do ar, a resposta é 503, com a mensagem "O Miau-ricio está indisponível agora. Tente de novo em instantes."

`GET /saude` → `{"status": "ok"}`

## Fora do escopo

- Login, histórico de perguntas e conversa com o orquestrador (`/api/v1/conversas`).

## Critérios de aceitação

Ver [cenarios.feature](cenarios.feature).

## Dependências

- [Spec 15](../15-rag-receitas/spec.md): o caso de uso `ResponderPergunta`.
- [Spec 16](../16-ampliar-base-conhecimento/spec.md): a base de 20 fontes.
- Qdrant e Ollama no ar.

## Riscos e limitações

- O Ollama atende uma pergunta por vez (`OLLAMA_NUM_PARALLEL=1`). Pedidos ao mesmo tempo esperam na fila.
