# Plano da versão 1 do RAG de receitas

Plano de execução e registro do andamento da versão 1 do RAG (épico #15, entrega da semana 2). Serve para retomar o trabalho em qualquer máquina, por qualquer pessoa ou assistente de IA. O comportamento esperado está na [spec](spec.md), e as decisões em [docs/decisoes.md](../../docs/decisoes.md).

## Entregáveis da semana 2

- Base de conhecimento curada, com pelo menos 20 documentos-fonte.
- Descrição da estratégia de chunking.
- Descrição da estratégia de embeddings.
- Banco vetorial implementado.
- Demonstração: consulta enviada, trechos recuperados, resposta baseada neles e as fontes usadas.

## Andamento

Branch: `feat/15-rag-receitas`. O PR usa `Refs #15` e `Closes` para as sub-issues #16, #17, #18, #19, #20 e #21. Ficam fora a #22 (TACO, fora do MVP), a #23 (fechada; o conjunto de avaliação só a cita) e a #24 (endpoint da API).

Cada fase termina com os testes e o Ruff passando e **um commit**, em Conventional Commits, em português, sem `Co-Authored-By` nem menção a IA.

| Fase | Entrega | Commit | Situação |
| --- | --- | --- | --- |
| 0 | Branch `feat/15-rag-receitas` | — | Feita |
| 1 | Troca da fonte de receitas na documentação, RN26 a definir, seção "Versão 1" na spec | `docs(receitas): troca a fonte de receitas para afrodite.json e RecipeNLG` | Feita |
| 2 | `docs/semana-2/estrategia-rag.md`: fluxo do RAG, chunking, embeddings, banco vetorial, limitações (entregável descritivo, sai no site) | `docs(receitas): descreve a estratégia de chunking e de embeddings do RAG` | Feita |
| 3 | `pyproject.toml` (Poetry), `docker-compose.yml` com o Qdrant, `.env.example`, configuração com pydantic-settings | `build(receitas): configura o projeto Python e o Qdrant no Docker Compose` | Feita |
| 4 | Decisões das bibliotecas, do Ollama, dos candidatos de embeddings e da estratégia de chunking, com a justificativa perguntada à pessoa (skill `registrar-decisao`) | `docs(decisoes): registra as escolhas do RAG de receitas` | Feita (4 decisões sem justificativa) |
| 5 | Domínio (`Fonte`, `Trecho`, `Receita`, `Ingrediente`, `RespostaComFontes`) e fragmentação, com testes de unidade | `feat(receitas): adiciona os trechos e a estratégia de fragmentação` | **Próxima** |
| 6 | Carregadores, os dois adaptadores de embeddings, o repositório Qdrant e o caso de uso `indexar` | `feat(receitas): indexa os trechos no Qdrant` | |
| 7 | Caso de uso `responder`, adaptador do Ollama, prompt versionado, CLI e passos BDD | `feat(receitas): responde perguntas com os trechos e as fontes` | |
| 7b | Extração dos ingredientes da pergunta, contagem dos que faltam e desempate do top-5, com testes; regra proposta no modelo de domínio | `feat(receitas): desempata as receitas pelos ingredientes que faltam` | |
| 8 | Ingestão das receitas e dos textos de orientação; FONTES.md preenchido | `feat(receitas): adiciona a base de conhecimento curada` | |
| 9 | Conjunto de avaliação, comando `comparar`, escolha do modelo de embeddings e limiar calibrado | `feat(receitas): compara os modelos de embeddings` + `docs(decisoes): registra o modelo de embeddings escolhido` | |
| 10 | Notebook da demonstração `notebooks/01-rag-receitas-passo-a-passo.ipynb` | `docs(receitas): adiciona o notebook de demonstração do RAG` | |

O PR só é aberto quando a pessoa pedir. Atualize a coluna "Situação" a cada fase concluída.

## Escolhas desta versão

Tomadas por Paulo Vitor em 05/11/2026. As que já estão em `docs/decisoes.md` dizem isso; as outras entram na fase 4.

| Escolha | Situação no decisoes.md |
| --- | --- |
| Receitas do **afrodite.json** (todas) e de uma **amostra do RecipeNLG** (cerca de 3.000), no lugar do TudoGostoso | Registrada; validação contestada em parte (afrodite sem licença) |
| **RN26** (busca sob demanda) a definir, fora da versão 1 | Registrada |
| **Guia Alimentar para a População Brasileira** (Ministério da Saúde, 2014) como documento-âncora da orientação, mais de 2 a 5 textos de conservação e aproveitamento (Embrapa, MS, FAO) | Fase 4 |
| Comparar os embeddings **intfloat/multilingual-e5-base** e **qwen3-embedding:4b** e escolher pelo resultado | Fase 4 (candidatos) e fase 9 (escolha) |
| LLM local com **Ollama**, modelo `qwen2.5:7b`, atrás do adaptador | Fase 4 |
| **Qdrant em Docker**, igual ao que vai para a VM | Fase 4 |
| Código modular em `src/economia/receitas`, seguindo a [visão geral](../../docs/arquitetura/visao-geral.md) | Já previsto na arquitetura |
| **Desempate do top-5:** com scores numa faixa de tolerância (0,01), vem primeiro a receita com menos ingredientes faltando | Fase 4, e proposta de regra no modelo de domínio na fase 7b |

## Estratégia de chunking

- **Receita = 1 trecho.** A receita é curta e autocontida; separar ingredientes do modo de preparo quebra a recuperação. Texto embedado: `Receita: {título}. Ingredientes: {...}. Modo de preparo: {...}`, cortado em 512 tokens (limite do e5), priorizando título e ingredientes. O texto completo fica no payload.
- **Guia Alimentar:** extraído do PDF com pypdf, dividido pelos capítulos e seções do sumário e depois por parágrafo, até cerca de 350 tokens, com 50 tokens de sobreposição. Cada um dos "Dez passos para uma alimentação adequada e saudável" vira um trecho próprio. Cabeçalhos, rodapés e números de página repetidos saem. Cada trecho guarda `capitulo`, `secao` e `pagina`.
- **Outros textos de orientação:** mesma divisão por seção e parágrafo.
- **Payload:** `tipo` (receita | conhecimento), `documento_id`, `titulo`, `secao`, `pagina`, `fonte`, `instituicao`, `ano`, `url`, `licenca`, `idioma` e `ingredientes` (só nas receitas). Índices de payload em `tipo`, `fonte` e `idioma`.
- **Curadoria das receitas:** saem as que não têm ingredientes ou modo de preparo. Os ingredientes divididos em subseções ("Massa:", "Recheio:") são juntados.

## Estratégia de embeddings

| | `intfloat/multilingual-e5-base` | `qwen3-embedding:4b` |
| --- | --- | --- |
| Execução | sentence-transformers, no processo | Ollama (`/api/embed`), o mesmo servidor do LLM |
| Dimensões | 768 | 2560 |
| Contexto | 512 tokens | 32 mil tokens |
| Prefixos | `query: ` na pergunta e `passage: ` no trecho | `Instruct: <tarefa>\nQuery: <pergunta>` na pergunta; trecho sem prefixo |

- Vetores normalizados, distância cosseno, **uma coleção por modelo** (`base_conhecimento_e5` e `base_conhecimento_qwen3`).
- Comparação justa: os mesmos trechos, o mesmo chunking e o mesmo top-k (5).
- Conjunto de avaliação em `data/avaliacao/perguntas_rag_v1.json`, com cerca de 20 perguntas e gabarito: receitas brasileiras, receitas em inglês com pergunta em português (busca entre idiomas), pelo menos 4 sobre o Guia Alimentar e 3 sem resposta na base.
- Métricas: Recall@5, MRR, separação dos scores entre perguntas com e sem resposta (para calibrar o limiar da RN11, valor inicial 0,80), latência por consulta e tempo de indexação.
- Critério de produção: a VM tem 2 vCPUs e não tem GPU, então a latência na CPU pesa tanto quanto a qualidade.

## Arquitetura do código

```text
pyproject.toml          Poetry: qdrant-client, sentence-transformers, ollama, pypdf, pydantic-settings; dev: pytest, pytest-bdd, ruff
docker-compose.yml      Qdrant (a #36 completa com os outros serviços)
.env.example            QDRANT_URL, OLLAMA_URL, OLLAMA_MODELO, MODELO_EMBEDDINGS, LIMIAR_SIMILARIDADE, TOLERANCIA_EMPATE
prompts/miau-ricio/resposta_com_fontes_v1.md
prompts/miau-ricio/extrair_ingredientes_v1.md
src/economia/compartilhado/configuracao.py
src/economia/compartilhado/infraestrutura/llm_ollama.py
src/economia/receitas/
  dominio/modelos.py               Fonte, Trecho, Receita, Ingrediente, RespostaComFontes
  dominio/correspondencia.py       conta os ingredientes que faltam (função pura, RN01)
  dominio/ordenacao.py             desempate do top-5 pela faixa de tolerância
  aplicacao/portas.py              GeradorDeEmbeddings, RepositorioDeTrechos, ModeloDeLinguagem (Protocols)
  aplicacao/fragmentacao.py        regras de chunking
  aplicacao/indexar_base.py        carregar → fragmentar → embedar → gravar
  aplicacao/responder_pergunta.py  preço (RN04) → recuperar → limiar (RN11) → LLM → fontes (RN10)
  infraestrutura/embeddings_e5.py, embeddings_ollama.py, repositorio_qdrant.py
  infraestrutura/carregadores.py   afrodite (JSON), RecipeNLG (Parquet, amostra com semente fixa), orientação (PDF/Markdown)
  cli.py                           indexar | perguntar "..." | comparar
```

- As **fontes da resposta são montadas pelo código** a partir do payload dos trechos usados, nunca redigidas pelo LLM. O LLM recebe os trechos numerados [1]…[n] e cita os números; o código troca cada número pela fonte (título, origem, ano, link e licença).
- O LLM só **interpreta** a pergunta (lista de ingredientes disponíveis, em português e em inglês, validada por Pydantic). A contagem do que falta é determinística: normaliza o texto (minúsculas, sem acento, singular simples) e compara com as linhas de ingredientes do afrodite e com o campo `NER` do RecipeNLG. Sal, água e óleo vêm de uma lista provisória na configuração.

## Dados

Os dados brutos ficam em `data/raw/receitas/`, que o `.gitignore` já ignora. Em outra máquina, baixe de novo:

```bash
mkdir -p data/raw/receitas data/raw/orientacao
curl -fL -o data/raw/receitas/afrodite.json \
  https://raw.githubusercontent.com/adrianosferreira/afrodite.json/master/afrodite.json
curl -fL -o data/raw/receitas/recipenlg_0000.parquet \
  "https://huggingface.co/datasets/SandhyaKilari/RecipeNLG_dataset/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
curl -fL -o data/raw/orientacao/guia_alimentar_populacao_brasileira_2ed.pdf \
  https://bvsms.saude.gov.br/bvs/publicacoes/guia_alimentar_populacao_brasileira_2ed.pdf
```

O que já foi verificado nesses arquivos:

| Arquivo | O que tem |
| --- | --- |
| `afrodite.json` (3 MB) | 8.183 receitas: `nome` e `secao[]` com `nome` e `conteudo`. Só 7.924 têm "Ingredientes" e 7.283 têm "Modo de Preparo". Há subseções como "Massa:" e "Recheio:". Os nomes das seções podem ter espaço no começo |
| `recipenlg_0000.parquet` (218 MB) | O primeiro dos 5 arquivos Parquet: 780 mil receitas, todas da origem `Gathered` e com `link`. Colunas: `title`, `ingredients`, `directions`, `link`, `source`, `NER`. As listas `ingredients`, `directions` e `NER` vêm como texto JSON |
| Guia Alimentar (4,2 MB) | PDF oficial. Falta confirmar o texto exato da nota de reprodução na ficha catalográfica |

O repositório oficial do RecipeNLG no Hugging Face (`mbien/recipe_nlg`) não tem os dados, só um script que exige download manual. A cópia `SandhyaKilari/RecipeNLG_dataset` está completa. Ela se declara "cc-by-4.0", mas os termos que valem são os do dataset original (uso não comercial em pesquisa e ensino).

## Preparar a máquina

| Ferramenta | Como instalar | Para quê |
| --- | --- | --- |
| Docker Desktop | aberto e rodando | Qdrant |
| Ollama | `ollama pull qwen2.5:7b` e `ollama pull qwen3-embedding:4b` (cerca de 7 GB) | LLM e embeddings |
| Poetry | `brew install poetry` ou `python3 -m pip install --user poetry` | dependências Python |
| GitHub CLI | `brew install gh` e `gh auth login` | `scripts/nova-branch.sh` e o PR |
| pre-commit | `pipx install pre-commit` e `pre-commit install` | hooks do repositório |

A máquina do laboratório não deixa usar o Homebrew sem `sudo`. Lá, o Poetry foi instalado com `pip --user`, em `~/Library/Python/3.14/bin`, e o `gh` pelo binário oficial, em `~/.local/bin`. As duas pastas precisam estar no `PATH`.

## Pendências

- Conferir os termos de uso do RecipeNLG no site oficial e atualizar a validação no decisoes.md.
- Confirmar a nota de reprodução do Guia Alimentar.
- Escolher de 2 a 5 textos de conservação e aproveitamento, com a licença conferida.
- Pontos em aberto do modelo de domínio que a versão 1 contorna: ingredientes básicos sempre disponíveis, origem das substituições da RN28, RN26.

## Como retomar com um assistente de IA

Abra o repositório na branch `feat/15-rag-receitas` e peça: "Continue o plano em `specs/15-rag-receitas/plano-v1.md` a partir da próxima fase, explicando a teoria de cada fase e fazendo um commit ao final de cada uma."
