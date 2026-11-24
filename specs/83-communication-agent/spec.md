# Spec: Communication Agent

| Campo | Valor |
| --- | --- |
| Issue | #83 |
| Status | Em revisão |
| Contexto delimitado | Verificação |
| Agente | Communication Agent |

## Problema

Depois do Validation Agent (#79), a pessoa ainda recebe um resultado técnico: classificação, justificativa com números de citação, ids de trechos e confiança. Isso não serve para quem fez a pergunta. Falta quem transforme a análise aprovada numa resposta que a pessoa entenda, no tamanho que ela pediu e com as fontes. Falta também dizer com clareza quando a verificação não chegou a uma conclusão: na avaliação da #79, 3 de 15 alegações terminaram reprovadas depois dos 2 retornos, e uma análise reprovada não pode chegar à pessoa como se fosse resposta.

## Comportamento esperado

O Communication Agent é o último nó do fluxo da [arquitetura multiagente](../../docs/semana-4/arquitetura-agentes.md). Ele recebe a alegação, a análise, o resultado da validação, as evidências e o perfil de leitura e devolve o `Veredito`.

- **`consumidor_geral`:** explicação completa, em linguagem simples, citando as fontes.
- **`consumidor_rapido`:** uma ou duas frases.
- **Validação aprovada:** a mensagem explica a classificação com base na justificativa e nas evidências citadas.
- **Validação reprovada** (o orquestrador da #82 chegou ao limite de retornos): a mensagem diz que a verificação não foi conclusiva, e o veredito sai com `aprovado_pela_validacao` igual a `false`.

O LLM só redige o texto da `mensagem`. A classificação, as fontes, a fonte principal e o `aprovado_pela_validacao` são montados pelo código (RN01, RN10).

## Termos do domínio

Termos do [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md) propostos na #72: alegação (`Alegacao`), evidência recuperada (`EvidenciaRecuperada`), classificação da alegação (`ClassificacaoDaAlegacao`), análise da alegação (`AnaliseDaAlegacao`), resultado da validação (`ResultadoDaValidacao`), **veredito (`Veredito`)** e **perfil de leitura (`PerfilDeLeitura`)**. As fontes do veredito usam a `FonteEvidencia` da #75, sem termo novo. Os contratos estão na seção 5.4 da arquitetura.

## Regras de negócio

- **RN01:** a classificação, a escolha das fontes, a fonte principal e o `aprovado_pela_validacao` vêm do código. O LLM não decide nem altera esses campos.
- **RN10:** as fontes do veredito são montadas pelo código a partir das evidências citadas na análise, nunca a partir do texto do LLM.
- **RN11:** quando não há análise aprovada, o veredito diz que não foi possível concluir, em vez de inventar uma resposta.
- **RN30:** o que vai ao Langfuse passa pelo mascaramento.

Regras desta funcionalidade:

1. **Fontes:** uma por documento citado, sem repetir, na ordem das citações da análise.
2. **Fonte principal:** a fonte da evidência citada com o maior score. Em empate, a primeira citada. No perfil rápido, ela é a única fonte do veredito.
3. **Classificação `nova` sem citação:** o veredito não tem fontes, e a mensagem diz que a base não tem evidência sobre a alegação (RN11).
4. **Validação reprovada ou sem análise:** `aprovado_pela_validacao` é `false` e a mensagem é um texto fixo do código, sem chamar o LLM, dizendo que a verificação não foi conclusiva. O veredito não tem fontes, porque elas não foram confirmadas pela validação. Com análise, a classificação é a da análise, para o registro. Sem análise, o veredito não tem classificação.
5. **Saída inválida do LLM** (não é JSON, está fora do esquema ou a mensagem é vazia): a mensagem passa a ser a justificativa da análise, sem os marcadores `[n]`. O veredito não falha por causa do texto.
6. **Tamanho no perfil rápido:** se a mensagem do LLM passar de 2 frases, o código fica com as 2 primeiras.
7. **Sem "verdadeiro" nem "falso":** a classificação mede o quanto a base cobre a alegação, não se ela é verdadeira. O prompt pede isso.

## Entradas e saídas

Caso de uso na camada `aplicacao` de `verificacao`, sem API nova nesta issue. O orquestrador da #82 chama este caso de uso pela porta do Communication Agent.

**`ComunicarVeredito.executar(alegacao, analise, validacao, evidencias, perfil)`** → `Veredito`

| Parâmetro | Tipo |
| --- | --- |
| `alegacao` | `Alegacao` |
| `analise` | `AnaliseDaAlegacao` ou `None` |
| `validacao` | `ResultadoDaValidacao` |
| `evidencias` | lista de `EvidenciaRecuperada` |
| `perfil` | `PerfilDeLeitura` (`consumidor_geral` ou `consumidor_rapido`) |

Saída (`Veredito`), como na seção 5.4 da arquitetura:

```json
{
  "classificacao": "parcial",
  "mensagem": "Em parte. O Guia Alimentar fala do consumo de ovos, mas não de colesterol.",
  "fontes": [{ "titulo": "Guia Alimentar para a População Brasileira", "instituicao": "Ministério da Saúde", "ano": 2014, "url": null }],
  "aprovado_pela_validacao": true
}
```

Saída pedida ao LLM (esquema JSON): `{"mensagem": "..."}`.

**Prompt:** `verificacao/comunicacao` no prompt management do Langfuse (versão 1 criada em 24/11/2026, rótulos `production` e `latest`), lido pelo rótulo `production`, com a cópia local usada pelos prompts da #79. A mensagem ao LLM leva o perfil, a alegação, a classificação, a justificativa e as evidências citadas, numeradas. O contrato do prompt (campo `mensagem`) entra em `tests/contrato/test_prompts_no_langfuse.py`.

**Arquivos novos** (nenhum arquivo da #75, da #79 ou da #82 é alterado; o único arquivo existente que muda é o contrato dos prompts, com uma linha):

- `src/economia/verificacao/dominio/veredito.py`: `PerfilDeLeitura`, `Veredito`, montagem das fontes e escolha da fonte principal.
- `src/economia/verificacao/aplicacao/comunicar_veredito.py`: o caso de uso `ComunicarVeredito`.
- `tests/verificacao/test_veredito.py`, `tests/verificacao/test_comunicar_veredito.py` e `tests/bdd/test_communication_agent.py`.

## Fora do escopo

- **O orquestrador LangGraph, o estado compartilhado e a rota `POST /api/v1/verificacoes`:** são da #82 (Pedro Lucas).
- **A interface da demo e a integração com a rota:** itens seguintes da #72, que dependem da #82.
- **Novos perfis de leitura** além de `consumidor_geral` e `consumidor_rapido`.
- **Dizer se a alegação é verdadeira ou falsa.**

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- **#79 (Analysis e Validation):** `Alegacao`, `AnaliseDaAlegacao`, `ResultadoDaValidacao`, `ClassificacaoDaAlegacao` e a porta `ModeloDeLinguagem`. Esta branch traz a #79 até ela entrar na `main`.
- **#75 (Research):** `EvidenciaRecuperada` e a `FonteEvidencia`.
- **#82 (Orquestrador):** a porta do Communication Agent. A assinatura acima é a proposta para o orquestrador chamar.
- **#69:** o adaptador do Ollama com saída JSON e os prompts no prompt management do Langfuse.

## Pontos para a revisão

1. **Texto fixo quando não conclui** (regra 4), em vez de pedir ao LLM. Proposta: texto fixo, porque é o caso em que menos se pode errar e não gasta uma chamada.
2. **Limite do perfil rápido** (regra 6): 2 frases, cortadas pelo código.
3. **A mensagem não volta ao Validation.** O LLM pode reescrever a justificativa com outro sentido. Conferir a mensagem com a conferência de contradição da #79 custaria mais uma chamada por verificação; fica para depois da avaliação.

## Riscos e limitações

- **O LLM pode reescrever a justificativa com um sentido diferente** (ponto 3 da revisão).
- **A contagem de frases é aproximada:** abreviações como "Min." podem cortar uma frase no meio.
- **A qualidade do texto depende do LLM local** e não tem métrica automática nesta issue. É conferida nos casos da avaliação da #79.
