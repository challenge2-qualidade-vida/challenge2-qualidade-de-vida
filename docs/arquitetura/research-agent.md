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
5. As evidências recuperadas são organizadas com seus metadados.
6. A API retorna os resultados em formato JSON.

## 5. Saída

Modelo: `RespostaVerificacao`.

| Campo | Descrição |
|---|---|
| `pergunta` | Pergunta utilizada na recuperação. |
| `total_evidencias` | Quantidade de evidências retornadas. |
| `evidencias` | Lista de evidências recuperadas. |

Cada item de `evidencias` contém:

**trecho**

- `id`: identificador do trecho.
- `texto`: conteúdo recuperado.
- `pagina_inicial`: página inicial do trecho.
- `pagina_final`: página final do trecho.
- `secao`: seção documental, quando disponível.

**documento**

- `id`: identificador do documento.
- `arquivo`: nome do arquivo de origem.
- `hash_sha256`: hash do conteúdo normalizado.
- `fonte`: informações bibliográficas da fonte.

**fonte**

- `titulo`: título da publicação.
- `instituicao`: instituição responsável.
- `ano`: ano de publicação, quando disponível.
- `url`: endereço da fonte, quando disponível.

**score**

- Pontuação de similaridade retornada pela recuperação semântica.
- É utilizada para ordenar e comparar a relevância dos resultados.
- Não representa probabilidade de veracidade.

## 6. Tecnologias e recuperação semântica

- **Embeddings:** `intfloat/multilingual-e5-base`.
- **Dimensão dos vetores:** 768.
- **Banco vetorial:** Qdrant.
- **Distância:** similaridade por cosseno.
- **Coleção:** `evidencias_verificacao_e5` (nome correspondente à configuração E5 atual).
- **Recuperação:** busca semântica com limite configurável de resultados.

A implementação utiliza os prefixos próprios do modelo E5 para consultas e documentos, respectivamente `query:` e `passage:`.

A coleção de verificação é separada da coleção utilizada para recuperação de receitas.

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

A implementação foi submetida a testes automatizados e validação de integração.

Resultados registrados na implementação:

- 208 testes aprovados na suíte geral.
- Verificação estática com Ruff aprovada.
- Indexação de 21 documentos, totalizando 1.810 trechos.
- Recuperação semântica testada com Qdrant.
- Endpoint `/verificar` exercitado por requisição HTTP real.

Esses resultados correspondem à execução registrada durante o desenvolvimento da implementação.

## 11. Limites de interpretação

A recuperação semântica identifica trechos relacionados à pergunta, mas similaridade textual ou semântica não comprova que uma alegação seja verdadeira.

A ausência de evidências recuperadas também não demonstra que uma informação seja falsa.

A análise de conteúdo, a identificação de contradições e a validação das conclusões devem ocorrer nas etapas responsáveis da arquitetura multiagente.
