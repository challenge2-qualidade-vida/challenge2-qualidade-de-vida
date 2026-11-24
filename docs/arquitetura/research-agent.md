# Research Agent — Arquitetura e implementação

## 1. Objetivo

O Research Agent é responsável por recuperar evidências científicas e documentais relacionadas a uma pergunta ou alegação.

Sua função é localizar trechos relevantes na base de conhecimento, utilizando recuperação semântica, e disponibilizar essas evidências para as etapas posteriores da arquitetura multiagente.

O agente não realiza julgamento de veracidade.

## 2. Responsabilidades

- Consultar a base de documentos indexados.
- Gerar embeddings das perguntas recebidas.
- Executar busca semântica no Qdrant.
- Recuperar os trechos mais relevantes.
- Preservar a proveniência das evidências.
- Disponibilizar os resultados por meio da API FastAPI.

## 3. Organização da implementação

A implementação está organizada em camadas:

- **Domínio:** modelos de fontes, documentos, trechos e evidências recuperadas.
- **Aplicação:** portas e caso de uso `PesquisarEvidencias`.
- **Infraestrutura:** embeddings, preparação de documentos, indexação, repositório e pesquisador Qdrant.
- **API:** modelos HTTP, dependências e rotas.

## 4. Endpoint e fluxo de execução

Endpoint: `POST /verificar`

A requisição recebe uma pergunta e um limite de evidências.

Fluxo:

1. A API recebe e valida a requisição.
2. O caso de uso `PesquisarEvidencias` é executado.
3. O pesquisador gera o embedding da pergunta.
4. O Qdrant realiza a busca semântica.
5. O caso de uso aplica o limiar de similaridade configurado.
6. As evidências aprovadas são organizadas com seus metadados.
7. A API retorna os resultados em formato JSON.

**Limite de responsabilidade:** esse endpoint disponibiliza a recuperação de evidências. Ele não representa, isoladamente, a execução completa do fluxo multiagente Research → Analysis → Validation → Communication.

## 5. Saída

Modelo: `RespostaVerificacao`.

| Campo | Descrição |
|---|---|
| `pergunta` | Pergunta utilizada na recuperação. |
| `total_evidencias` | Quantidade de evidências retornadas. |
| `evidencias` | Lista de evidências recuperadas e aprovadas pelo filtro. |

Cada item de `evidencias` contém:

**Trecho**

- `id`: identificador do trecho.
- `texto`: conteúdo recuperado.
- `pagina_inicial`: página inicial do trecho.
- `pagina_final`: página final do trecho.
- `secao`: seção documental, quando disponível.

**Documento**

- `id`: identificador do documento.
- `arquivo`: nome do arquivo de origem.
- `hash_sha256`: hash do conteúdo normalizado.
- `fonte`: informações bibliográficas da fonte.

**Fonte**

- `titulo`: título da publicação.
- `instituicao`: instituição responsável.
- `ano`: ano de publicação, quando disponível.
- `url`: endereço da fonte, quando disponível.

**Score**

- Pontuação de similaridade retornada pela recuperação semântica.
- É utilizada para ordenar e comparar a relevância dos resultados.
- Não representa probabilidade de veracidade.

## 6. Tecnologias e recuperação semântica

- **Embeddings:** `intfloat/multilingual-e5-base`.
- **Dimensão dos vetores:** 768.
- **Banco vetorial:** Qdrant.
- **Distância:** similaridade por cosseno.
- **Coleção:** `evidencias_verificacao_e5`.
- **Recuperação:** busca semântica com limite configurável de resultados.

A implementação utiliza os prefixos próprios do modelo E5 para consultas e documentos, respectivamente `query:` e `passage:`.

A coleção de verificação é separada da coleção utilizada para recuperação de receitas.

**Limiar de similaridade**

A configuração atual utiliza o limiar `0,845` para o modelo E5.

O caso de uso `PesquisarEvidencias` aplica esse limiar aos resultados retornados pelo pesquisador. Portanto, uma evidência pode ser recuperada pelo Qdrant e posteriormente descartada por não atingir o valor mínimo configurado.

O projeto possui limiares distintos para E5 e Qwen3, pois os modelos apresentam escalas de similaridade diferentes.

## 7. Proveniência e rastreabilidade

Cada evidência recuperada preserva informações que permitem identificar sua origem e localização:

- Documento de origem.
- Instituição responsável.
- Ano de publicação, quando disponível.
- URL da fonte, quando disponível.
- Arquivo original.
- Hash SHA-256.
- Texto do trecho.
- Páginas inicial e final.
- Seção documental, quando disponível.

Esses dados permitem que as etapas posteriores consultem as evidências e identifiquem suas respectivas fontes.

## 8. Integração com a arquitetura multiagente

A documentação coletiva `fluxos-e-contratos.md` prevê modelos Pydantic na camada de aplicação para a comunicação entre agentes.

Ela também apresenta a relação:

`PerguntaDeConhecimento` → `RespostaComFontes`

O endpoint `/verificar` e seus modelos HTTP atuais representam a interface da implementação de recuperação, mas ainda não devem ser considerados equivalentes aos contratos internos do LangGraph.

A adaptação entre a implementação atual e o estado compartilhado do orquestrador deverá respeitar os modelos e campos definidos pela equipe.

**Pendente de alinhamento:**

- Contrato definitivo de entrada do Research Agent no LangGraph.
- Contrato definitivo de saída para o Analysis Agent.
- Adaptação entre os modelos HTTP atuais e os modelos internos de aplicação.

A integração não altera a responsabilidade central do Research Agent: recuperar evidências e preservar sua proveniência, sem realizar julgamento de veracidade.

## 9. Tratamento de erros e validações

O caso de uso valida:

- Pergunta não vazia.
- Limite de evidências positivo.

A API também valida o limite permitido pelo modelo HTTP e transforma erros de validação do caso de uso em respostas HTTP 422.

## 10. Testes e validação da implementação

A implementação foi submetida a testes automatizados, verificações estáticas e experimentos de recuperação semântica.

### 10.1. Testes automatizados

Resultados registrados:

- 458 testes aprovados na suíte geral.
- 18 testes desmarcados (`deselected`).
- Verificação estática com Ruff aprovada.
- `git diff --check` sem problemas.
- Indexação de 21 documentos, totalizando 1.810 trechos, conforme registro anterior da implementação.

### 10.2. Experimentos de recuperação semântica

Os experimentos foram executados diretamente pelo caso de uso oficial `PesquisarEvidencias`, utilizando o modelo `intfloat/multilingual-e5-base` e a coleção `evidencias_verificacao_e5`.

Configuração utilizada:

- Modelo de embeddings: `intfloat/multilingual-e5-base`.
- Banco vetorial: Qdrant.
- Limite de recuperação: 5 evidências.
- Limiar de similaridade E5: 0,845.

**Experimento 1 — Caso v01: recuperação aprovada**

Alegação: "Alimentos ultraprocessados devem ser evitados."

Resultado:

- 5 evidências recuperadas e aprovadas pelo filtro.
- Scores entre 0,8542 e 0,8575.
- Primeira evidência: score 0,8575.
- Fonte: *Protocolos de Uso do Guia Alimentar para a População Brasileira na Orientação Alimentar: Fascículo 1*.
- Instituição: Ministério da Saúde / Universidade de São Paulo.
- Ano: 2021.
- Página: 21.

O trecho recuperado contém a recomendação explícita de que se evite o consumo de alimentos ultraprocessados.

O resultado é compatível com a classificação esperada `reciclada` no conjunto `data/avaliacao/verificacao/casos_v1.json`. Essa classificação pertence ao conjunto de avaliação e não é produzida pelo Research Agent.

**Experimento 2 — Caso v06: recuperação abaixo do limiar**

Alegação: "Ultraprocessados devem ser evitados porque causam câncer em poucas semanas de consumo."

Resultado da busca bruta no Qdrant:

- 5 evidências recuperadas.
- Scores entre 0,8295 e 0,8366.
- Primeira evidência: score 0,8366.
- Fonte: *Protocolos de Uso do Guia Alimentar para a População Brasileira na Orientação Alimentar: Fascículo 1*.
- Página: 21.

Resultado após aplicação do limiar de 0,845:

- 0 evidências aprovadas.

O experimento demonstra que o Qdrant recuperou documentos semanticamente relacionados à alegação, mas todos os resultados ficaram abaixo do limiar configurado e foram descartados pelo caso de uso.

Esse comportamento evidencia uma limitação relevante: alegações compostas podem obter scores inferiores mesmo quando parte de seu conteúdo está coberta pela base documental.

### 10.3. Experimento exploratório de recuperação geral

Também foi realizada uma consulta exploratória:

"Quais são as recomendações para uma alimentação saudável e equilibrada?"

Resultado:

- 5 evidências recuperadas.
- Scores entre 0,8625 e 0,8684.
- Fontes incluindo o Guia Alimentar para a População Brasileira (2014), publicações da OPAS e protocolos do Ministério da Saúde / USP.

O experimento demonstrou a recuperação de diferentes documentos relacionados ao tema, preservando os respectivos metadados bibliográficos.

### 10.4. Interpretação dos resultados

Os experimentos demonstram que:

- O Research Agent consegue recuperar evidências relacionadas a alegações presentes na base.
- A proveniência documental é preservada nos resultados.
- O limiar de similaridade influencia diretamente a quantidade de evidências disponibilizadas às etapas posteriores.
- A calibração do limiar para alegações compostas permanece como ponto de avaliação da equipe.

Os resultados de recuperação não representam uma classificação de veracidade. A análise de cobertura, a identificação de informações parcialmente sustentadas e a validação das conclusões são responsabilidades das etapas posteriores da arquitetura multiagente.

## 11. Limites de interpretação

A recuperação semântica identifica trechos relacionados à pergunta, mas similaridade textual ou semântica não comprova que uma alegação seja verdadeira.

A ausência de evidências aprovadas pelo filtro não demonstra que uma informação seja falsa ou que não existam documentos relacionados na base.

A análise de conteúdo, a identificação de contradições e a validação das conclusões devem ocorrer nas etapas responsáveis da arquitetura multiagente.
