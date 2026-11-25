# Spec: Orquestrador da verificação de alegações

| Campo | Valor |
| --- | --- |
| Issue | #82 |
| Status | Implementada (falta a evidência dos traces reais) |
| Contexto delimitado | Verificação |
| Agente | Orquestrador (LangGraph), com Research, Analysis, Validation e Communication |

## Problema

Os quatro agentes da verificação já existem como casos de uso separados: o Research (#75), o Analysis e o Validation (#79) e o Communication (#83). Falta quem os ligue num fluxo só, que a pessoa possa chamar pela API. Hoje, o único laço Research → Analysis → Validation com retorno é o da avaliação da #79 (`verificacao/aplicacao/avaliacao.py`), que serve para medir e não para atender um pedido. Sem orquestrador, a alegação não chega ao veredito, e o ciclo de retorno do Validation não aparece no trace, que é a evidência pedida pela #72.

## Comportamento esperado

A pessoa envia uma alegação e o perfil de leitura e recebe o `Veredito`, com o histórico das etapas de cada agente. O fluxo segue a [arquitetura multiagente](../../docs/semana-4/arquitetura-agentes.md) (seções 2, 4 e 6):

1. O **Research** busca as evidências com o limite inicial.
2. O **Analysis** classifica a alegação e justifica, citando as evidências.
3. O **Validation** confere a análise e aprova ou devolve o trabalho.
4. Com a análise aprovada, ou no limite de retornos, o **Communication** redige o veredito no perfil pedido.

Quem decide o próximo nó é o código, a partir do `ResultadoDaValidacao`. O LLM não escolhe o caminho.

## Termos do domínio

Termos do [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md): alegação (`Alegacao`), evidência recuperada (`EvidenciaRecuperada`, o modelo da Verificação), classificação da alegação (`ClassificacaoDaAlegacao`), análise da alegação (`AnaliseDaAlegacao`), resultado da validação (`ResultadoDaValidacao`), veredito (`Veredito`) e perfil de leitura (`PerfilDeLeitura`).

Termos novos, que entram no modelo de domínio como **proposta** junto com esta spec:

- **Estado da verificação (`EstadoDaVerificacao`):** o que os agentes leem e escrevem durante uma verificação. Os campos estão na seção 4 da arquitetura.
- **Etapa da verificação (`EtapaDaVerificacao`):** o registro de um nó executado, com o agente, a entrada, a saída e os segundos. A lista de etapas é o histórico que a interface mostra.

## Regras de negócio

- **RN01:** a decisão do próximo nó, o limite da busca e a contagem de retornos são do código. O LLM só redige (Analysis, contradição do Validation e Communication).
- **RN10 e RN11:** as fontes do veredito vêm das evidências citadas; sem análise aprovada, o veredito diz que não foi possível concluir. As duas regras são aplicadas pelo Communication (#83).
- **RN30:** a alegação e as saídas passam pelo mascaramento antes de irem ao Langfuse.

Regras desta funcionalidade, a partir da avaliação da #79:

1. **Roteamento:** aprovado vai para o Communication. Reprovado com `retornar_para = research` vai para o Research; com `retornar_para = analysis`, vai para o Analysis. O destino vem do Validation, que já dá preferência ao Research quando há motivos para os dois.
2. **Retorno ao Research:** a busca é refeita com o dobro do limite, até o teto. A análise recomeça sem os motivos da reprovação, porque eles falam do score, que o Analysis não corrige (commit `1349bbb` da #79).
3. **Retorno ao Analysis:** as evidências se mantêm, e o Analysis recebe os motivos da reprovação.
4. **Limite de retornos:** quando a validação reprova e o número de retornos já chegou ao máximo, o fluxo vai para o Communication com a validação reprovada. O veredito sai como não conclusivo, com `aprovado_pela_validacao` igual a `false`.
5. **Valores padrão:** limite inicial de 5 trechos, teto de 10 trechos e no máximo 2 retornos, configuráveis. O teto de 10 vem da avaliação da #79: com o teto de 20, o `qwen2.5:7b` passou a descrever os trechos em vez de classificar a alegação, e com o teto de 10 e o prompt de análise v2 a acurácia foi de 87% (`resultados_v1_teto10_prompt-v2.json`).
6. **Sem limiar de score na busca do fluxo:** como na seção 5.1 da arquitetura e na avaliação da #79, o orquestrador pede as evidências sem o limiar de similaridade. Quem decide se a evidência basta é o Validation, pelo limiar de confiança. A rota `POST /api/v1/verificar` continua como está, com o limiar.
7. **Histórico:** cada nó executado vira uma etapa, na ordem em que rodou, inclusive os nós repetidos nos retornos. Num retorno, a etapa do Validation guarda os motivos e o destino.
8. **Falhas:** erro do LLM ou do Qdrant (tempo esgotado, serviço fora do ar) interrompe a verificação, e a API responde 503. Saída inválida do LLM não é erro: o Analysis devolve `None`, o Validation devolve ao Analysis, e o Communication usa a justificativa (#83, regra 5).

## Entradas e saídas

**Caso de uso** na camada `aplicacao` da verificação:

`VerificarAlegacao.executar(alegacao, perfil)` → `ResultadoDaVerificacao` (`veredito`, `historico`, `retornos`)

**Rota:** `POST /api/v1/verificacoes`, com erros em Problem Details (RFC 9457), no mesmo roteador de `api/evidencias.py`.

Requisição:

```json
{ "alegacao": "Ovo aumenta o colesterol?", "perfil": "consumidor_geral" }
```

Resposta 200:

```json
{
  "veredito": {
    "classificacao": "parcial",
    "mensagem": "Em parte. O Guia Alimentar fala do consumo de ovos, mas não de colesterol.",
    "fontes": [{ "titulo": "Guia Alimentar para a População Brasileira", "instituicao": "Ministério da Saúde", "ano": 2014, "url": null }],
    "aprovado_pela_validacao": true
  },
  "retornos": 0,
  "historico": [
    { "agente": "research", "entrada": { "limite": 5 }, "saida": { "evidencias": [{ "trecho": "guia-alimentar-0123", "score": 0.87 }] }, "segundos": 0.4 },
    { "agente": "analysis", "entrada": { "motivos": [] }, "saida": { "classificacao": "parcial", "citacoes": ["guia-alimentar-0123"], "confianca": 0.87 }, "segundos": 6.1 },
    { "agente": "validation", "entrada": {}, "saida": { "aprovado": true, "motivos": [], "retornar_para": null }, "segundos": 1.2 },
    { "agente": "communication", "entrada": { "perfil": "consumidor_geral" }, "saida": { "aprovado_pela_validacao": true }, "segundos": 3.0 }
  ]
}
```

| Situação | Status |
| --- | --- |
| Alegação vazia ou com mais de 500 caracteres, perfil desconhecido | 422 |
| LLM ou Qdrant indisponível | 503 |
| Erro inesperado | 500, sem detalhes internos |

O histórico leva os ids dos trechos e os scores, não o texto dos trechos, para a resposta não crescer a cada retorno.

## Fora do escopo

- **A interface da demo:** item seguinte da #72, que consome esta rota.
- **Mudanças nos agentes:** os casos de uso da #75, da #79 e da #83 são usados como estão.
- **Calibração do limiar de confiança (0,845) e novos prompts:** continuam com a avaliação da #79.
- **Execução assíncrona pelo worker (RQ):** a verificação roda na requisição. Com cerca de 24 s em média e 44 s no pior caso da melhor rodada da avaliação, isso pode mudar depois.
- **Memória da conversa:** cada verificação é independente.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature). O plano de implementação está em [plano.md](plano.md).

## Dependências

- **#75 (Research):** o caso de uso `PesquisarEvidencias`, chamado pelo adaptador `PesquisaDeEvidencias` da verificação.
- **#79 (Analysis e Validation):** `AnalisarAlegacao`, `ValidarAnalise`, `DestinoDoRetorno` e o laço da avaliação, que é a referência do roteamento.
- **#83 (Communication):** `ComunicarVeredito`.
- **LangGraph:** decidido em 03/11/2026 (`docs/decisoes.md`), mas ainda não está no `pyproject.toml`. Entra como dependência nesta issue.
- **Langfuse:** o `ObservadorLangfuse` da #79 e o `RegistroDeGeracoes` para as gerações.

## Pontos para a revisão

1. **Rótulo do prompt de análise:** a melhor rodada da #79 usou o `verificacao/analise` v2 (`analise@v2`). Proposta: o Paulo move o rótulo `production` para a v2 antes da demo, e o orquestrador lê sempre `production`.
2. **Limiar na busca:** a regra 6 segue a arquitetura e a avaliação da #79 (sem limiar no fluxo). A rota da #75 usa o limiar de 0,845. Proposta: manter as duas como estão e registrar a diferença em `docs/decisoes.md`.
3. **Teto de 10 trechos** em vez dos 20 da avaliação original (regra 5).
4. **Ponto aberto 4 da arquitetura:** a rota fica em `POST /api/v1/verificacoes`, no padrão de `/api/v1`, como está na #82.

## Riscos e limitações

- **Latência:** com o `qwen2.5:7b` no Mac M4, a melhor rodada da #79 teve média de 24 s e máximo de 44 s. Na rodada original, com o teto de 20 trechos, os casos com 2 retornos passaram de 1 min. A interface precisa mostrar o progresso, e o cliente HTTP precisa de um tempo limite folgado.
- **O grafo é pequeno para o LangGraph:** o laço cabe num `while`, como na avaliação. O LangGraph entra pela decisão de 03/11 e pelo trace por nó. A regra de roteamento fica numa função pura da camada `aplicacao`, testada sem o LangGraph.
- **A qualidade do veredito depende dos agentes:** o orquestrador não corrige uma análise errada que o Validation aprovou. Na melhor rodada da avaliação, 2 de 15 casos foram aprovados com a classificação errada.
