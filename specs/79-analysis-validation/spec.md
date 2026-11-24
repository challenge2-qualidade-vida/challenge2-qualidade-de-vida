# Spec: Analysis Agent e Validation Agent

| Campo | Valor |
| --- | --- |
| Issue | #79 |
| Status | Em revisão |
| Contexto delimitado | Verificação |
| Agente | Analysis Agent e Validation Agent (papel da Mia) |

## Problema

O Research Agent (#75) devolve as evidências mais próximas de uma alegação, mas não diz o que elas significam. Falta quem leia as evidências, diga se a base já cobre a alegação e explique por quê, citando as fontes. Falta também quem confira essa análise antes de ela chegar à pessoa: uma justificativa que cita um trecho inexistente, contradiz a evidência ou se apoia numa evidência fraca não pode virar veredito.

## Comportamento esperado

**Analysis Agent.** Recebe a alegação, as evidências do Research e, num retorno, os motivos da reprovação anterior. Pede ao LLM, com saída em JSON, a classificação (`reciclada`, `parcial` ou `nova`) e a justificativa, citando as evidências pelo número. O código converte os números nos ids dos trechos e calcula a confiança. O LLM não calcula valores (RN01).

**Validation Agent.** Recebe a alegação, as evidências e a análise e decide se a análise é aprovada. Primeiro faz as conferências determinísticas no código. Se todas passam, pergunta ao LLM se a justificativa contradiz as evidências citadas. Quando reprova, diz os motivos e para qual agente o trabalho volta: o **Research**, quando a evidência é insuficiente, ou o **Analysis**, quando a análise está errada. Quem decide o destino é o código, não o LLM.

**Avaliação.** Um comando roda o fluxo Research → Analysis → Validation num conjunto de 10 a 20 alegações fictícias com a classificação esperada, com até 2 retornos, e gera uma tabela simples dos resultados.

## Termos do domínio

Termos propostos no [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md) na #72: alegação (`Alegacao`), evidência recuperada (`EvidenciaRecuperada`, #75), classificação da alegação (`ClassificacaoDaAlegacao`), análise da alegação (`AnaliseDaAlegacao`) e resultado da validação (`ResultadoDaValidacao`). Os contratos estão em [arquitetura-agentes.md](../../docs/semana-4/arquitetura-agentes.md), seção 5.

## Regras de negócio

- **RN01:** a confiança e todas as conferências da validação são calculadas pelo código. O LLM só classifica, justifica e aponta contradições.
- **RN10:** toda análise se apoia em fonte. `reciclada` e `parcial` citam ao menos uma evidência recuperada. Uma análise `nova` também cita, sempre que a busca trouxe evidência no limiar mínimo ou acima: precisa mostrar as evidências que examinou e explicar por que elas não cobrem a alegação. A `nova` fica sem citação só quando nenhuma evidência chega ao limiar.
- **RN30:** o que vai ao Langfuse passa pelo mascaramento. As alegações da avaliação são fictícias.

Regras desta funcionalidade:

1. As evidências vão ao LLM numeradas a partir de 1. O LLM devolve os números citados. Números fora da lista ficam registrados na análise como citações inválidas, sem serem descartados.
2. A **confiança** da análise é o maior score entre as evidências citadas (0 quando não há citação válida). É similaridade, não probabilidade de veracidade.
3. Uma saída do LLM que não é JSON válido, ou não segue o schema, não vira análise: o Analysis devolve "sem análise".
4. Conferências do Validation, nesta ordem (todos os motivos são registrados):

   | Conferência | Se falhar, volta para |
   | --- | --- |
   | Há uma análise (o LLM devolveu JSON válido) | Analysis |
   | A justificativa não é vazia | Analysis |
   | Todas as citações existem entre as evidências | Analysis |
   | `reciclada` ou `parcial` cita ao menos uma evidência | Analysis |
   | `reciclada` ou `parcial` com a confiança no limiar mínimo ou acima | Research |
   | `nova`, quando há evidência no limiar mínimo ou acima, cita ao menos uma dessas evidências | Analysis |
   | A justificativa não contradiz as evidências citadas (LLM) | Analysis |

5. Quando há motivos para os dois destinos, o trabalho volta para o **Research**: sem evidência suficiente, refazer a análise não resolve.
6. A conferência de contradição só roda quando as conferências determinísticas passam. Se a saída do LLM da contradição for inválida, a análise é reprovada e volta para o Analysis.
7. O limiar mínimo de confiança é configurável (`LIMIAR_CONFIANCA_VERIFICACAO`). O valor inicial é o mesmo limiar do e5 no RAG (0,845), a calibrar com a avaliação.
8. Na avaliação, um retorno ao Research busca de novo com o dobro do limite (máximo 20), e um retorno ao Analysis repete a análise com os motivos. O limite é de 2 retornos por caso.

## Entradas e saídas

Casos de uso na camada `aplicacao` de `verificacao`, sem API nova nesta issue. Os modelos seguem os contratos da [arquitetura](../../docs/semana-4/arquitetura-agentes.md).

**`AnalisarAlegacao.executar(alegacao, evidencias, motivos=())`** → `AnaliseDaAlegacao | None`

```json
{
  "classificacao": "parcial",
  "justificativa": "O Guia Alimentar trata do consumo de ovos [1], mas não fala de colesterol.",
  "citacoes": ["guia-alimentar-0123"],
  "citacoes_invalidas": [],
  "confianca": 0.87
}
```

Saída pedida ao LLM (schema JSON): `{"classificacao": "reciclada|parcial|nova", "justificativa": "...", "citacoes": [1]}`.

**`ValidarAnalise.executar(alegacao, evidencias, analise)`** → `ResultadoDaValidacao`

```json
{
  "aprovado": false,
  "motivos": ["A citação 7 não está entre as 5 evidências recuperadas"],
  "retornar_para": "analysis"
}
```

`retornar_para` é `null` quando aprovado.

**Avaliação:**
- **Conjunto:** `data/avaliacao/verificacao/casos_v1.json`, com `id`, `alegacao` e `classificacao_esperada`.
- **Comando:**
  ```bash
  poetry run python -m economia.verificacao.cli avaliar \
    --casos data/avaliacao/verificacao/casos_v1.json \
    --saida data/avaliacao/verificacao/resultados_v1.json
  ```
- **O que grava por caso:** classificação obtida, se acertou, aprovado direto, retornos, destino de cada retorno e latência.
- **O que grava por execução:** acurácia da classificação, taxa de aprovação direta, média de retornos e latência média.
- **Tabela:** o comando imprime a tabela em Markdown para a seção 9 da arquitetura.

**Prompts:** `verificacao/analise` e `verificacao/validacao` no prompt management do Langfuse, lidos pelo rótulo `production`, com a cópia local já usada pelo Miau-ricio.

## Fora do escopo

- **O orquestrador LangGraph, o estado compartilhado do grafo e o limite de retornos no fluxo real:** são do Pedro Lucas. Os casos de uso são funções sobre modelos tipados, prontas para virar nós.
- **O Communication Agent e os perfis de leitura:** são do Guilherme.
- **A rota `POST /verificar` com o fluxo completo e a interface da demo.**
- **Dizer se a alegação é verdadeira ou falsa:** a classificação mede o quanto a base cobre a alegação.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- **#75 (Research Agent):** os modelos `EvidenciaRecuperada`, `TrechoEvidencia` e `DocumentoEvidencia`, a busca no Qdrant (coleção `evidencias_verificacao_e5`) e a base de 21 documentos. Esta branch traz a #75 até ela entrar na `main`.
- **#72 (arquitetura):** os contratos e os termos do domínio.
- **#69:** o adaptador do Ollama com saída JSON (`gerar_json`), o gancho de registro no Langfuse e os prompts no prompt management.

## Riscos e limitações

- **A confiança é o score da busca,** que fica quase sempre entre 0,7 e 0,9 com o e5. O limiar precisa de calibração, e 10 a 20 casos são pouco para isso.
- **A conferência de contradição depende do LLM local** e pode errar nos dois sentidos.
- **O score alto não prova que a evidência cobre a alegação,** só que o tema é próximo. Por isso uma `nova` com evidência forte não é reprovada pelo score: é reprovada quando não cita essa evidência, e a conferência de contradição avalia se a explicação se sustenta.
- **As fronteiras entre `reciclada` e `parcial` são subjetivas:** a classificação esperada de cada caso é uma decisão da equipe.
- **As alegações são fictícias,** e a base tem só 21 documentos.
