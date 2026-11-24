# Matriz de LLMs: LLM puro x RAG no PC Linux (#69)

Execução da matriz da [spec 69](../../specs/69-llm-puro-vs-rag/spec.md) numa máquina só, uma execução por vez, gerada por `scripts/rodar-matriz-llm.sh`. Os números saem dos JSONs da avaliação; este arquivo só os formata.

## Configuração

- **Máquina:** Linux x86_64, 16 CPUs lógicas, Radeon RX 9060 XT (16 GB), 60 GB de RAM
- **Perguntas:** `data/avaliacao/perguntas_rag_v3.json` (67 perguntas)
- **Embeddings:** e5; limiar 0.845 no RAG
- **Fixos:** temperatura 0.0, semente 42, contexto 8192, saída máxima 2048, raciocínio desligado
- **Prompts:** RAG com `resposta_com_fontes@v2` (resposta estruturada e segunda tentativa de citação); puro com `resposta_sem_base`
- **Resultados:** `data/avaliacao/v3/pc-linux`

## Resultados por modelo e modo

| Modelo | Modo | Acurácia | Respondeu | Recusa (RN11) | Aviso de preço (RN04) | Fonte citada (RN10) | Hit@5 | ROUGE-1 | ROUGE-L | Cosseno | Latência média | Latência máx. | Tempo total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | rag | 93% | 91% | 100% | 100% | 73% | 80% | 0.373 | 0.270 | 0.843 | 2.6 s | 7.8 s | 3min36 |
| `qwen2.5:7b` | puro | 87% | 83% | 100% | 100% | — | — | 0.262 | 0.179 | 0.766 | 1.3 s | 4.5 s | 2min13 |
| `qwen3.5:9b` | rag | 88% | 85% | 100% | 100% | 87% | 83% | 0.362 | 0.264 | 0.795 | 3.5 s | 16.2 s | 4min58 |
| `qwen3.5:9b` | puro | 94% | 100% | 60% | 100% | — | — | 0.320 | 0.205 | 0.921 | 2.4 s | 7.0 s | 3min40 |
| `gemma3:12b` | rag | 93% | 91% | 100% | 100% | 80% | 81% | 0.365 | 0.266 | 0.841 | 5.2 s | 13.8 s | 6min58 |
| `gemma3:12b` | puro | 94% | 100% | 60% | 100% | — | — | 0.256 | 0.159 | 0.906 | 6.3 s | 12.9 s | 7min43 |
| `qwen3.5:27b` | rag | 87% | 83% | 100% | 100% | 89% | 83% | 0.365 | 0.274 | 0.779 | 20.3 s | 63.9 s | 23min31 |
| `qwen3.5:27b` | puro | 94% | 94% | 90% | 100% | — | — | 0.279 | 0.175 | 0.865 | 14.6 s | 39.6 s | 17min03 |
| `gemma3:27b` | rag | 91% | 91% | 90% | 100% | 78% | 83% | 0.397 | 0.292 | 0.847 | 20.0 s | 71.1 s | 22min59 |
| `gemma3:27b` | puro | 94% | 100% | 60% | 100% | — | — | 0.296 | 0.191 | 0.913 | 20.5 s | 62.8 s | 23min29 |

## Ganho do RAG sobre o LLM puro

Diferença RAG − puro, por modelo (pontos percentuais e pontos de métrica).

| Modelo | Acurácia | ROUGE-1 | ROUGE-L | Cosseno | Latência média |
| --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | +6 p.p. | +0.111 | +0.091 | +0.078 | +1.3 s |
| `qwen3.5:9b` | -6 p.p. | +0.043 | +0.059 | -0.126 | +1.1 s |
| `gemma3:12b` | -1 p.p. | +0.109 | +0.107 | -0.064 | -1.1 s |
| `qwen3.5:27b` | -7 p.p. | +0.086 | +0.099 | -0.086 | +5.7 s |
| `gemma3:27b` | -3 p.p. | +0.101 | +0.100 | -0.066 | -0.5 s |

## Erros de comportamento

- `qwen2.5:7b` rag: falsas recusas r06, n01, n04, n05, d04; respostas indevidas nenhuma
- `qwen2.5:7b` puro: falsas recusas n01, n02, n03, d02, h03, u02, p01, p02, p03; respostas indevidas nenhuma
- `qwen3.5:9b` rag: falsas recusas r06, e03, e05, n01, n04, n05, h01, b03; respostas indevidas nenhuma
- `qwen3.5:9b` puro: falsas recusas nenhuma; respostas indevidas s01, s02, s04, s06
- `gemma3:12b` rag: falsas recusas r06, n01, n04, n05, b03; respostas indevidas nenhuma
- `gemma3:12b` puro: falsas recusas nenhuma; respostas indevidas s01, s02, s04, s07
- `qwen3.5:27b` rag: falsas recusas r06, e02, e05, n01, n03, n04, n05, h01, b03; respostas indevidas nenhuma
- `qwen3.5:27b` puro: falsas recusas n01, n02, n03; respostas indevidas s01
- `gemma3:27b` rag: falsas recusas r06, n01, n04, n05, b03; respostas indevidas s07
- `gemma3:27b` puro: falsas recusas nenhuma; respostas indevidas s01, s02, s06, s07

## ROUGE-L por categoria

| Categoria | qwen2.5:7b rag | qwen2.5:7b puro | qwen3.5:9b rag | qwen3.5:9b puro | gemma3:12b rag | gemma3:12b puro | qwen3.5:27b rag | qwen3.5:27b puro | gemma3:27b rag | gemma3:27b puro |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alimentacao_infantil | 0.34 | 0.17 | 0.34 | 0.20 | 0.40 | 0.15 | 0.41 | 0.17 | 0.39 | 0.17 |
| comportamento_alimentar | 0.31 | 0.00 | 0.33 | 0.19 | 0.35 | 0.12 | 0.29 | 0.22 | 0.36 | 0.22 |
| conservacao | 0.18 | 0.20 | 0.31 | 0.17 | 0.26 | 0.17 | 0.33 | 0.18 | 0.30 | 0.22 |
| desperdicio | 0.20 | 0.13 | 0.22 | 0.17 | 0.36 | 0.14 | 0.28 | 0.16 | 0.35 | 0.14 |
| guia_alimentar | 0.30 | 0.18 | 0.31 | 0.17 | 0.26 | 0.12 | 0.32 | 0.17 | 0.30 | 0.15 |
| nutricao | 0.19 | 0.06 | 0.23 | 0.17 | 0.11 | 0.14 | 0.15 | 0.04 | 0.16 | 0.14 |
| orientacao_nutricional | 0.22 | 0.08 | 0.28 | 0.18 | 0.24 | 0.10 | 0.25 | 0.16 | 0.23 | 0.15 |
| preco | — | — | — | — | — | — | — | — | — | — |
| receita_entre_idiomas | 0.22 | 0.26 | 0.13 | 0.24 | 0.18 | 0.20 | 0.13 | 0.19 | 0.21 | 0.23 |
| receita_pt | 0.33 | 0.28 | 0.28 | 0.26 | 0.28 | 0.21 | 0.34 | 0.22 | 0.38 | 0.24 |
| robustez | 0.37 | 0.19 | 0.27 | 0.23 | 0.31 | 0.18 | 0.26 | 0.20 | 0.28 | 0.23 |
| seguranca_alimentar | 0.27 | 0.20 | 0.20 | 0.22 | 0.21 | 0.14 | 0.19 | 0.18 | 0.18 | 0.16 |
| sem_resposta | — | — | — | — | — | — | — | — | — | — |

## Execuções e links do Langfuse

| Modelo | Modo | Tentativa | Início | Fim | Duração | Código de saída |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen2.5:7b` | rag | 1 | 2026-11-18T22:46:35-03:00 | 2026-11-18T22:47:26-03:00 | 0min51 | 1 |
| `qwen2.5:7b` | rag | 2 | 2026-11-18T22:47:56-03:00 | 2026-11-18T22:51:32-03:00 | 3min36 | 0 |
| `qwen2.5:7b` | puro | 1 | 2026-11-18T22:51:32-03:00 | 2026-11-18T22:53:45-03:00 | 2min13 | 0 |
| `qwen3.5:9b` | rag | 1 | 2026-11-18T22:53:45-03:00 | 2026-11-18T22:58:43-03:00 | 4min58 | 0 |
| `qwen3.5:9b` | puro | 1 | 2026-11-18T22:58:43-03:00 | 2026-11-18T22:59:18-03:00 | 0min35 | 1 |
| `qwen3.5:9b` | puro | 2 | 2026-11-18T22:59:49-03:00 | 2026-11-18T23:03:29-03:00 | 3min40 | 0 |
| `gemma3:12b` | rag | 1 | 2026-11-18T23:03:29-03:00 | 2026-11-18T23:10:27-03:00 | 6min58 | 0 |
| `gemma3:12b` | puro | 1 | 2026-11-18T23:10:27-03:00 | 2026-11-18T23:18:10-03:00 | 7min43 | 0 |
| `qwen3.5:27b` | rag | 1 | 2026-11-18T23:19:57-03:00 | 2026-11-18T23:43:28-03:00 | 23min31 | 0 |
| `qwen3.5:27b` | puro | 1 | 2026-11-18T23:43:28-03:00 | 2026-11-19T00:00:31-03:00 | 17min03 | 0 |
| `gemma3:27b` | rag | 1 | 2026-11-19T00:00:31-03:00 | 2026-11-19T00:23:30-03:00 | 22min59 | 0 |
| `gemma3:27b` | puro | 1 | 2026-11-19T00:23:30-03:00 | 2026-11-19T00:46:59-03:00 | 23min29 | 0 |

- `qwen2.5:7b` rag (rag-qwen2.5:7b-resposta_com_fontes@v2-e5-linux-20261118-t2): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=5c5e69111eb5ffa2
- `qwen2.5:7b` puro (puro-qwen2.5:7b-resposta_sem_base-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=1ede9b8fe815854f
- `qwen3.5:9b` rag (rag-qwen3.5:9b-resposta_com_fontes@v2-e5-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=cf704819e82d1b61
- `qwen3.5:9b` puro (puro-qwen3.5:9b-resposta_sem_base-linux-20261118-t2): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=5d0abb82e0af08fc
- `gemma3:12b` rag (rag-gemma3:12b-resposta_com_fontes@v2-e5-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=227613a01f336bf5
- `gemma3:12b` puro (puro-gemma3:12b-resposta_sem_base-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=e9c50228ac4d42d6
- `qwen3.5:27b` rag (rag-qwen3.5:27b-resposta_com_fontes@v2-e5-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=463acd714a5636df
- `qwen3.5:27b` puro (puro-qwen3.5:27b-resposta_sem_base-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=dbf5e04fe9240a8b
- `gemma3:27b` rag (rag-gemma3:27b-resposta_com_fontes@v2-e5-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=dd7171179ac9fe3f
- `gemma3:27b` puro (puro-gemma3:27b-resposta_sem_base-linux-20261118): https://us.cloud.langfuse.com/project/cmwi1cz2h00jhad0ezbr3zov1/experiments/results?baseline=3a5c98fb92837cbb

## Limites

- ROUGE e cosseno dependem das respostas de referência de `perguntas_rag_v3.json` (revisadas pela equipe em 17/11/2026).
- O ROUGE penaliza paráfrase e o cosseno do e5 varia pouco (quase sempre entre 0,7 e 1,0): servem para comparar execuções, não como nota absoluta.
- Nenhuma métrica confere se os números da resposta estão certos.
- Os modelos de 27B não cabem nos 16 GB da placa e dividem a carga com a RAM: a latência deles mede também esse transbordo.
- O juiz (fidelidade e relevância) ainda não avalia os runs da avaliação no Langfuse (tarefa 1.4 do plano).
- Uma máquina só, e perguntas fictícias.
