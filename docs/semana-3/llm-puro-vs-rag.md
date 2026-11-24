# Semana 3: LLM puro x LLM com RAG

Relatório da comparação entre o LLM sem base de conhecimento (LLM puro) e o LLM com RAG, na issue #69. Este relatório substitui o rascunho de 13/11/2026, que usava só o `qwen2.5:7b` e o conjunto v2. Os números saem dos arquivos JSON versionados em `data/avaliacao/`; nada aqui foi digitado à mão a partir de outra fonte.

## Resumo

- **Recuperação:** com os ajustes da semana 2, o Recall@5 subiu de 0,500 para 0,833 e o MRR@5 de 0,435 para 0,764. A base também cresceu no mesmo período, por isso o ganho não pode ser atribuído só à busca.
- **RAG + LLM (`qwen2.5:7b`):** a redação estruturada (prompt v2) levou a acurácia de comportamento de 40% para 91–93%, com 100% de recusa correta.
- **LLM puro x RAG em 5 modelos** (`qwen2.5:7b`, `qwen3.5:9b`, `gemma3:12b`, `qwen3.5:27b`, `gemma3:27b`, 67 perguntas cada):
  - o RAG aumentou o ROUGE-L em todos os modelos (de +0,06 a +0,11) e o ROUGE-1 de +0,04 a +0,11;
  - o RAG recusou 90–100% das perguntas sem resposta na base. No modo puro, três modelos responderam 40% delas;
  - a acurácia de comportamento do modo puro parece maior (94%), mas está inflada: a métrica conta como "respondeu" frases como "não tenho informações precisas sobre…";
  - o cosseno favorece o modo puro, porque mede proximidade de tema, não correção.
- **Recomendação (proposta para a equipe):** manter o RAG com resposta estruturada e segunda tentativa. Para o LLM, os candidatos são o `gemma3:12b` (melhor equilíbrio entre ROUGE, fonte citada e recusa) e o `qwen2.5:7b` (a menor latência, com qualidade próxima). Os modelos de 27B não compensam: ganho pequeno, latência 4 a 8 vezes maior e não cabem na GPU das máquinas da equipe.
- **Ponto fraco encontrado:** nenhuma métrica atual confere números. O RAG do `qwen2.5:7b` disse que o feijão carioca tem 62,92 g de fibra por 100 g, citando a TACO, que diz 8,5 g.

## 1. Contexto e objetivo

O EconoMIA responde perguntas sobre receitas, conservação, nutrição e alimentação saudável. Um LLM sozinho responde com o que aprendeu no treinamento, sem consultar as fontes do produto. No RAG, a pergunta vira um embedding, os trechos mais próximos são buscados no Qdrant e o LLM redige a resposta a partir deles, citando as fontes (RN10). Quando a base não tem a informação, a resposta diz que não encontrou (RN11).

A proposta da semana 3 foi comparar LLM puro e LLM com RAG, experimentar formas de usar o RAG, entender o que muda e por quê, e escolher a abordagem do produto, com observabilidade no Langfuse.

## 2. Desenho experimental

| Teste | O que compara | Conjunto | Modelos | Arquivos |
| --- | --- | --- | --- | --- |
| 1. Recuperação sem LLM | Busca antes e depois dos ajustes da semana 2 | v2 (67 perguntas) | e5 | `data/avaliacao/v2/recuperacao_{antes,depois}.json` |
| 2. RAG + LLM, configuração original | Prompt v1, texto livre | v2 | `qwen2.5:7b` | `data/avaliacao/v2/respostas_{antes,depois}.json` |
| 3. RAG + LLM, configurações ajustadas | Segunda tentativa, resposta estruturada (v2), busca por ingrediente | v2 | `qwen2.5:7b` | `data/avaliacao/v2/respostas_v*.json` |
| 4. LLM puro x LLM com RAG | Os dois modos, com o mesmo prompt de persona, nos mesmos parâmetros | v3 (67 perguntas, com respostas de referência) | 5 modelos | `data/avaliacao/v3/pc-linux/completo_{puro,rag}_*.json` |

O teste 4 do rascunho de 13/11 (`scripts/avaliar_llm_sem_rag.py`, `respostas_llm_sem_rag.json`) não está no repositório e não tinha nenhuma métrica além da latência. Ele foi refeito como modo da própria avaliação (`avaliar-respostas --modo puro`), para que os dois modos passem pelas mesmas perguntas, métricas e registro no Langfuse.

## 3. Metodologia

### 3.1 Conjunto de avaliação

`data/avaliacao/perguntas_rag_v3.json` tem as mesmas 67 perguntas e gabaritos da v2, em 13 categorias (receitas em português e entre idiomas, Guia Alimentar, conservação, nutrição, alimentação infantil, desperdício, segurança alimentar, orientação nutricional, comportamento alimentar, robustez, sem resposta e preço). Cada pergunta tem um comportamento esperado: responder (54), não encontrar (10, RN11) ou aviso de preço (3, RN04).

A v3 acrescenta a **resposta de referência** nas 54 perguntas que devem ser respondidas. Cada referência foi escrita a partir dos trechos do gabarito, não do conhecimento geral, e revisada por uma pessoa da equipe (Mariah, 17/11/2026). Três referências têm ressalvas conhecidas: h01 (o documento só traz o exemplo do leite), c06 e d04 (respostas parciais).

### 3.2 O que ficou fixo

| Item | Valor |
| --- | --- |
| Temperatura e semente | 0 e 42 |
| Janela de contexto | 8192 tokens |
| Saída máxima | 2048 tokens |
| Modo de raciocínio (Qwen 3.5) | desligado em todos os modelos |
| Quantização | Q4_K_M (padrão das tags do Ollama), com o digest gravado em cada execução |
| Embeddings | `intfloat/multilingual-e5-base`, limiar 0,845, top-5 |
| Prompt do RAG | `miau-ricio/resposta_com_fontes@v2`, resposta estruturada e segunda tentativa de citação |
| Prompt do modo puro | `miau-ricio/resposta_sem_base`: mesma persona, sem trechos, pode dizer que não sabe e não dá preço atual |

Os prompts vêm do prompt management do Langfuse, e a versão usada fica gravada em cada execução (`versoes_dos_prompts`).

### 3.3 Máquinas

- **PC Linux** (matriz oficial): x86_64, 16 CPUs lógicas, Radeon RX 9060 XT com 16 GB, 60 GB de RAM. Rodou os 10 casos (5 modelos x 2 modos) em fila, com `scripts/rodar-matriz-llm.sh`, na noite de 18/11/2026.
- **Mac M4** (segunda medida): 24 GB de memória unificada. Rodou 5 dos 10 casos. Os modelos de 27B não couberam na GPU (o Ollama dividiu a carga em 11% CPU / 89% GPU) e a equipe não tem permissão para aumentar o limite de memória da GPU no macOS, por isso ficaram fora no Mac.

### 3.4 Procedimento

Teste 4, para cada modelo e cada modo:

```bash
poetry run python -m economia.receitas.cli avaliar-respostas \
  --modo rag --llm gemma3:12b \
  --perguntas data/avaliacao/perguntas_rag_v3.json \
  --prompt resposta_com_fontes_v2 --estruturada --segunda-tentativa \
  --saida data/avaliacao/v3/pc-linux/completo_rag_gemma3-12b.json
```

A comparação de duas execuções usa `comparar-execucoes <antes.json> <depois.json>`, e as tabelas deste relatório saem de `scripts/relatorio_matriz_llm.py`.

## 4. Métricas e como ler cada uma

| Métrica | O que mede | O que não mede |
| --- | --- | --- |
| Acurácia de comportamento | Se o sistema respondeu, recusou (RN11) ou avisou sobre preço (RN04) quando devia | Se o conteúdo está certo |
| Taxa de resposta / recusa correta | As duas metades da acurácia: perguntas com resposta na base e perguntas sem resposta | Idem |
| Fonte esperada citada | Se a resposta do RAG citou um documento do gabarito (RN10) | Se a resposta interpretou bem o documento. Não se aplica ao modo puro |
| Recall@5, MRR@5 e Hit@5 | Se um trecho do gabarito está entre os 5 recuperados, e em que posição | A qualidade do texto. Hit@5 só existe no RAG |
| ROUGE-1 F1 | Palavras em comum com a resposta de referência (sem acento, sem caixa, sem citações) | Correção: penaliza a resposta certa escrita com outras palavras |
| ROUGE-L F1 | A maior sequência de palavras em comum com a referência, na ordem | Idem |
| Cosseno textual | Proximidade de sentido entre a resposta e a referência, pelos embeddings do e5 | Correção: textos do mesmo tema ficam quase sempre entre 0,7 e 1,0 |
| Latência | Tempo por pergunta, da pergunta à resposta final | Depende da máquina; só vale comparar na mesma máquina |

Uma recusa vale 0 no ROUGE e no cosseno: sem isso, um modelo que recusa as perguntas difíceis teria médias maiores. Todas as contas são funções determinísticas do código, com testes (RN01). O ROUGE foi implementado no projeto, sem biblioteca nova.

## 5. Resultados

### 5.1 Teste 1: recuperação sem LLM

| Medição | Recall@5 | MRR@5 | Latência média | Limiar sugerido |
| --- | --- | --- | --- | --- |
| Antes | 0,500 | 0,435 | 0,040 s | 0,835 |
| Depois | 0,833 | 0,764 | 0,034 s | 0,846 |

Os trechos certos passaram a aparecer com mais frequência e em posições melhores. Entre as duas medições, porém, a base passou de 4.346 para 6.151 trechos (semana 2, de 7 para 20 fontes): a melhora mistura o efeito da busca e o da base maior.

### 5.2 Testes 2 e 3: RAG + LLM com o `qwen2.5:7b`

| Configuração | Acurácia | Taxa de resposta | Recusa correta | Fonte esperada | Latência média |
| --- | --- | --- | --- | --- | --- |
| Original, antes dos ajustes | 40,3% | 25,9% | 100% | 85,7% | 1,60 s |
| Original, depois dos ajustes da base | 47,8% | 35,2% | 100% | 84,2% | 2,89 s |
| v1 + segunda tentativa | 71,6% | 64,8% | 100% | 82,9% | 3,13 s |
| v2 estruturada | 91,0% | 88,9% | 100% | 77,1% | 2,54 s |
| v2 estruturada + segunda tentativa | 91,0% | 88,9% | 100% | 77,1% | 2,16 s |
| v2 + busca por ingrediente | 92,5% | 90,7% | 100% | 73,5% | 2,51 s |

O gargalo da configuração original estava na redação: o LLM respondia sem citar os trechos e a resposta virava "não encontrei" (RN10). A resposta estruturada, com o JSON dos trechos usados, resolveu a maior parte. A busca por ingrediente responde um pouco mais, mas cita a fonte esperada com menos frequência. A configuração "v2 estruturada + segunda tentativa" é a usada no teste 4.

### 5.3 Teste 4: LLM puro x LLM com RAG (PC Linux)

| Modelo | Modo | Acurácia | Respondeu | Recusa (RN11) | Aviso de preço | Fonte citada | Hit@5 | ROUGE-1 | ROUGE-L | Cosseno | Latência média |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | rag | 93% | 91% | 100% | 100% | 73% | 80% | 0,373 | 0,270 | 0,843 | 2,6 s |
| `qwen2.5:7b` | puro | 87% | 83% | 100% | 100% | — | — | 0,262 | 0,179 | 0,766 | 1,3 s |
| `qwen3.5:9b` | rag | 88% | 85% | 100% | 100% | 87% | 83% | 0,362 | 0,264 | 0,795 | 3,5 s |
| `qwen3.5:9b` | puro | 94% | 100% | 60% | 100% | — | — | 0,320 | 0,205 | 0,921 | 2,4 s |
| `gemma3:12b` | rag | 93% | 91% | 100% | 100% | 80% | 81% | 0,365 | 0,266 | 0,841 | 5,2 s |
| `gemma3:12b` | puro | 94% | 100% | 60% | 100% | — | — | 0,256 | 0,159 | 0,906 | 6,3 s |
| `qwen3.5:27b` | rag | 87% | 83% | 100% | 100% | 89% | 83% | 0,365 | 0,274 | 0,779 | 20,3 s |
| `qwen3.5:27b` | puro | 94% | 94% | 90% | 100% | — | — | 0,279 | 0,175 | 0,865 | 14,6 s |
| `gemma3:27b` | rag | 91% | 91% | 90% | 100% | 78% | 83% | 0,397 | 0,292 | 0,847 | 20,0 s |
| `gemma3:27b` | puro | 94% | 100% | 60% | 100% | — | — | 0,296 | 0,191 | 0,913 | 20,5 s |

Ganho do RAG sobre o modo puro (RAG − puro):

| Modelo | Acurácia | Recusa (RN11) | ROUGE-1 | ROUGE-L | Cosseno | Latência média |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | +6 p.p. | 0 | +0,111 | +0,091 | +0,078 | +1,3 s |
| `qwen3.5:9b` | −6 p.p. | +40 p.p. | +0,043 | +0,059 | −0,126 | +1,1 s |
| `gemma3:12b` | −1 p.p. | +40 p.p. | +0,109 | +0,107 | −0,064 | −1,1 s |
| `qwen3.5:27b` | −7 p.p. | +10 p.p. | +0,086 | +0,099 | −0,086 | +5,7 s |
| `gemma3:27b` | −3 p.p. | +30 p.p. | +0,101 | +0,100 | −0,066 | −0,5 s |

A tabela completa, com os erros de comportamento por pergunta e o ROUGE-L por categoria, está em [matriz-llm-pc-linux.md](matriz-llm-pc-linux.md).

### 5.4 Segunda máquina (Mac M4)

| Modelo | Modo | Acurácia no Mac | Acurácia no PC Linux | Latência no Mac | Latência no PC Linux |
| --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | rag | 92,5% | 92,5% | 15,4 s | 2,6 s |
| `qwen3.5:9b` | rag | 88,1% | 88,1% | 18,5 s | 3,5 s |
| `qwen3.5:9b` | puro | 89,6% | 94,0% | 11,3 s | 2,4 s |
| `gemma3:12b` | rag | 92,5% | 92,5% | 31,1 s | 5,2 s |
| `gemma3:12b` | puro | 94,0% | 94,0% | 22,0 s | 6,3 s |

Com temperatura 0 e semente fixa, o comportamento se repetiu em 4 das 5 execuções, em máquinas e sistemas diferentes. A exceção é o `qwen3.5:9b` puro. Entre as duas rodadas, o prompt saiu do arquivo local (`resposta_sem_base_v1.md`, no Mac) e passou para o Langfuse (`miau-ricio/resposta_sem_base` versão 1, no PC Linux). A comparação do texto dos dois prompts ainda não foi feita. A latência no Mac é de 4 a 6 vezes maior. O ROUGE e o cosseno do Mac não entram na comparação: duas execuções (`rag qwen2.5:7b` e `puro qwen3.5:9b`) rodaram antes da revisão das referências.

## 6. Discussão

**O RAG melhora o texto e a recusa, em todos os modelos.** O ROUGE-1 e o ROUGE-L sobem com o RAG nos 5 modelos, e as maiores diferenças estão nas categorias em que a resposta depende de um documento específico: alimentação infantil (+0,14 a +0,25 de ROUGE-L), comportamento alimentar, desperdício e Guia Alimentar. Nas perguntas sem resposta, o RAG recusa quase sempre (RN11); no modo puro, `qwen3.5:9b`, `gemma3:12b` e `gemma3:27b` responderam 4 das 10, como a dose de vitamina D (s02) e as calorias de um Big Mac (s06).

**A acurácia do modo puro está inflada.** Ela mede o comportamento, e o modo puro "responde" quase tudo. Respostas como "Eu não tenho informações precisas sobre o valor calórico do arroz branco cozido…" (`gemma3:27b`, n01) contam como resposta correta, porque o modelo devolveu `encontrou: true`. O mesmo vale para o Big Mac. Nas perguntas de nutrição, o modo puro do `qwen3.5:9b`, do `gemma3:12b` e do `gemma3:27b` tem 100% de "acurácia" sem dar nenhum número da TACO.

**O cosseno não serve para escolher entre os modos.** Ele é maior no modo puro em 4 dos 5 modelos. As respostas do modo puro são genéricas e falam do mesmo tema da referência; as do RAG trazem detalhes do documento (quantidades, nomes de fontes) que afastam o embedding. O cosseno serve para comparar execuções do mesmo modo, não puro contra RAG.

**Onde o RAG perde.** A busca não acha as linhas da TACO para perguntas de nutrição: a acurácia do RAG em nutrição fica entre 20% e 40% em todos os modelos, com falsas recusas em n01, n04 e n05. Isso vem da recuperação, não do LLM: a TACO foi indexada como texto e a tabela perde a estrutura. A carga da TACO como consulta estruturada (issue #22) resolve na origem. A r06 (couve-flor) e a b03 (pão de queijo com erro de digitação) também falham na maioria dos modelos.

**Nenhuma métrica atual confere números.** O RAG do `qwen2.5:7b` respondeu à n03 que o feijão carioca cozido tem "62,92 gramas de fibra por 100 gramas", citando a TACO, que diz 8,5 g. A resposta conta como correta no comportamento e na fonte citada. Esse tipo de erro só aparece com o juiz ou com a anotação humana, que não rodaram nesta matriz (seção 8).

**Tamanho do modelo.** Os modelos de 27B não melhoram o RAG de forma consistente: o `gemma3:27b` tem o melhor ROUGE-L (0,292), mas o `qwen3.5:27b` tem a pior acurácia do RAG (87%), com 9 falsas recusas. Os dois levam cerca de 20 s por pergunta no PC Linux, contra 2,6 s do `qwen2.5:7b`, e nos 16 GB da placa parte do modelo fica na RAM, o que também pesa na latência.

## 7. Escolha para o produto

**Configuração recomendada:** RAG com resposta estruturada (prompt v2) e segunda tentativa de citação. Ela mantém 100% de recusa correta, cita a fonte esperada em 73% a 89% das respostas, conforme o modelo, e tem o maior ganho de texto sobre o modo puro.

**LLM:** é uma proposta para a equipe decidir, com os números lado a lado.

| Candidato | A favor | Contra |
| --- | --- | --- |
| `gemma3:12b` | Melhor equilíbrio: 93% de acurácia, 80% de fonte citada, ROUGE-L 0,266 e 100% de recusa correta | 5,2 s por pergunta no PC Linux e 31 s no Mac |
| `qwen2.5:7b` | O mais rápido (2,6 s), mesma acurácia (93%) | A menor taxa de fonte citada (73%) e o erro de número da n03 |
| `qwen3.5:9b` | Fonte citada em 87% | Acurácia de 88%, com 8 falsas recusas |

O LLM puro não é recomendado como arquitetura principal: responde perguntas sem base, não cita fontes e não tem como mostrar de onde veio um número.

Critérios para validar o MVP:

- recusa correta de pelo menos 95% nas perguntas sem base (RN11);
- fonte esperada citada como métrica principal de rastreabilidade (RN10);
- conferência de números (juiz ou anotação) antes de liberar respostas de nutrição;
- latência medida na máquina de produção antes de fixar um limite.

## 8. Limites

- **O juiz não avaliou a matriz.** Os evaluators do Langfuse (Gemini como juiz de fidelidade e relevância) só avaliam as perguntas da API, nos ambientes `producao` e `local`. As execuções da avaliação são itens de experimento, que a regra atual não pega.
- **Sem anotação humana.** A fila de anotação no Langfuse e a amostra para a equipe ainda não foram criadas. Sem ela e sem o juiz, nenhuma métrica confere a correção factual.
- **ROUGE e cosseno dependem das referências.** As referências foram revisadas, mas foram escritas pela equipe a partir dos trechos; uma resposta correta com outras palavras perde ROUGE.
- **Uma máquina por matriz.** A matriz completa rodou só no PC Linux. A latência dos modelos de 27B mede também o transbordo da GPU para a RAM.
- **Perguntas fictícias,** escritas pela equipe, e 67 perguntas no total: diferenças de 1 ou 2 pontos percentuais equivalem a uma pergunta.
- **Configurações completas.** Os testes 2 e 3 comparam configurações inteiras; não isolam o efeito de cada mudança. O teste 1 mistura o efeito da busca e o da base maior.
- **Langfuse Cloud.** Houve falhas de envio por timeout durante as execuções (spans e scores descartados). Os números deste relatório vêm dos arquivos JSON, que ficam completos mesmo quando o envio falha.

## 9. Próximos passos

1. Criar a regra do juiz para os itens de experimento (ambiente `avaliacao`) e reavaliar os runs da matriz.
2. Criar a fila de anotação humana no Langfuse, com uma amostra de cerca de 15 respostas por modo, e medir a concordância entre o juiz e as pessoas.
3. Corrigir a classificação do modo puro: uma resposta que diz "não tenho a informação" deve contar como recusa.
4. Carregar a TACO como consulta estruturada (#22), para as perguntas de nutrição.
5. Registrar em `docs/decisoes.md` a escolha do LLM e da configuração, depois da decisão da equipe.

## 10. Observabilidade no Langfuse

- Cada execução é um *run* do dataset `miau-ricio-perguntas_rag_v3`, com o modelo, o modo, o prompt e a máquina no nome e no metadado. Os links estão em [matriz-llm-pc-linux.md](matriz-llm-pc-linux.md#execuções-e-links-do-langfuse).
- Cada pergunta é um registro com a busca no Qdrant (trechos e scores) e cada chamada ao LLM (prompt e versão, tokens de entrada e saída, tempo).
- As métricas de cada pergunta (comportamento, fonte esperada, ROUGE-1, ROUGE-L, cosseno, Hit@5 e latência) entram como scores, e o Langfuse calcula as médias por run.
- Como configurar e ler: [observabilidade.md](observabilidade.md).

## 11. Código e dados

| O quê | Onde |
| --- | --- |
| Perguntas e referências | `data/avaliacao/perguntas_rag_v3.json` (v2: `perguntas_rag_v2.json`) |
| Avaliação das respostas e métricas | `src/economia/receitas/aplicacao/avaliacao_respostas.py`, `metricas_de_texto.py` |
| Modo LLM puro | `src/economia/receitas/aplicacao/responder_sem_base.py` |
| Comparação de execuções | `src/economia/receitas/aplicacao/comparacao_de_avaliacoes.py` |
| Experimento no Langfuse | `src/economia/receitas/infraestrutura/experimento_langfuse.py` |
| Fila da matriz e relatório | `scripts/rodar-matriz-llm.sh`, `scripts/relatorio_matriz_llm.py` |
| Resultados dos testes 1 a 3 | `data/avaliacao/v2/` |
| Resultados do teste 4 | `data/avaliacao/v3/pc-linux/` (oficial) e `data/avaliacao/v3/` (Mac) |
| Spec e plano | `specs/69-llm-puro-vs-rag/` |
