# Plano de testes: orquestrador da verificação (#82)

Plano para a [spec](spec.md) e o [plano de implementação](plano.md). Ele diz o que precisa ser conferido, em que nível, com quais dados e qual resultado conta como aprovado. A situação de cada item reflete a worktree em 25/11/2026: a implementação já existe, mas ainda não tem commit.

## 1. Objetivo

Garantir que o orquestrador:

- liga os quatro agentes na ordem certa;
- decide o próximo nó só pelo código (RN01);
- respeita o teto da busca e o limite de retornos;
- devolve o veredito e o histórico pela API, com os erros em Problem Details;
- deixa no Langfuse um trace por verificação, com os retornos visíveis.

Também garante que a avaliação do Paulo continua medindo a mesma coisa depois de passar pelo orquestrador.

## 2. Escopo

| Entra | Não entra |
| --- | --- |
| Roteamento, estado e retornos (`aplicacao/orquestracao.py`) | A qualidade da classificação de cada agente, que é testada na #79 e na #83 |
| Caso de uso `VerificarAlegacao`, nos dois motores (`LacoSimples` e `GrafoLangGraph`) | A calibração do limiar de confiança |
| Rota `POST /api/v1/verificacoes` | A interface da demo |
| Observabilidade da verificação no Langfuse | A busca do Research, que é testada na #75 |
| Avaliação rodando pelo orquestrador (`avaliacao.py`, CLI) | Carga e concorrência em produção |

## 3. Níveis de teste

| Nível | O que confere | Ferramenta | Dependências externas | Onde |
| --- | --- | --- | --- | --- |
| **Unidade: roteamento** | `proximo_no`, `rotear_validacao`, `preparar_retorno`, parâmetros | pytest | Nenhuma | `tests/verificacao/test_orquestracao.py` |
| **Unidade: caso de uso** | Fluxo completo com os agentes de verdade e o LLM roteirizado, nos dois motores | pytest, fixture `motor` | Nenhuma (dublês) | `tests/verificacao/test_verificar_alegacao.py` |
| **BDD** | Os 9 cenários da spec | pytest-bdd | Nenhuma (dublês) | `tests/bdd/test_orquestrador_verificacao.py` |
| **API** | Status, corpo, Problem Details e OpenAPI | `TestClient`, `dependency_overrides` | Nenhuma | `tests/api/test_verificacoes.py` |
| **Observabilidade** | Trace, spans, metadado do retorno, falha do Langfuse | pytest, cliente falso | Nenhuma | `tests/verificacao/test_observabilidade_langfuse.py` |
| **Arquitetura** | Domínio e aplicação sem LangGraph; verificação sem o domínio do Research | pytest com `ast` | Nenhuma | `test_verificar_alegacao.py`, `test_independencia_dos_contextos.py` |
| **Regressão da avaliação** | `avaliar_caso`, resumo e CLI pelo orquestrador | pytest | Nenhuma | `tests/verificacao/test_avaliacao.py`, `test_cli.py` |
| **Contrato dos prompts** | Os quatro prompts no Langfuse (`latest` e `production`) | `pytest -m langfuse` | Langfuse Cloud | `tests/contrato/test_prompts_no_langfuse.py` |
| **Integração local** | O fluxo de ponta a ponta com o Ollama, o Qdrant e o e5 de verdade | CLI `avaliar` e `curl` | Ollama, Qdrant, e5 | Manual (seção 7) |
| **Evidência para a #72** | Traces reais: um aprovado direto e um com retorno | Langfuse | Todas | Manual (seção 8) |

Os testes automáticos rodam sem LLM, sem Qdrant e sem rede, como pede o critério de pronto da #82.

## 4. Matriz de rastreabilidade

Cada regra da spec, com os testes que a cobrem. **Situação:** ✅ coberto; ⚠️ coberto em parte; ❌ falta.

| Regra da spec | Teste | Situação |
| --- | --- | --- |
| Valores padrão: 5, 10 e 2 (regra 5) | `test_padroes_seguem_a_spec` (roteamento e CLI) | ✅ |
| Parâmetros inválidos | `test_parametros_invalidos` | ✅ |
| Aprovado vai para o Communication (regra 1) | `test_aprovado_vai_para_o_communication`, cenário "Análise aprovada direto" | ✅ |
| Reprovado volta ao destino do Validation (regra 1) | `test_reprovado_volta_para_o_destino_da_validacao` | ✅ |
| Retorno ao Research dobra o limite e limpa os motivos (regra 2) | `test_retorno_ao_research_dobra_o_limite_e_limpa_os_motivos`, cenário correspondente | ✅ |
| Teto da busca (regra 2) | `test_retorno_ao_research_nao_passa_do_teto`, cenário "A busca não passa do teto" | ✅ |
| Retorno ao Analysis mantém as evidências e repassa os motivos (regra 3) | `test_retorno_ao_analysis_mantem_as_evidencias_e_repassa_os_motivos`, cenário correspondente | ✅ |
| Limite de retornos leva ao veredito não conclusivo (regra 4) | `test_no_limite_de_retornos_vai_para_o_communication`, `test_limite_de_retornos_da_veredito_nao_conclusivo_sem_chamar_o_communication`, cenário correspondente | ✅ |
| Zero retornos permitidos | `test_sem_retornos_permitidos_a_reprovacao_vai_direto_ao_communication` | ✅ |
| Busca sem limiar de score no fluxo (regra 6) | — | ❌ o código de `criar_verificar_alegacao` (CLI) monta a busca sem o limiar, mas nenhum teste confere isso |
| Histórico na ordem, com os nós repetidos (regra 7) | Cenários "Análise aprovada direto" e "Limite de retornos" | ✅ |
| Motivos e destino na etapa do Validation (regra 7) | `test_retorno_ao_research_guarda_os_motivos_e_o_destino_na_etapa` | ✅ |
| Segundos de cada etapa | `test_cada_etapa_tem_os_segundos_do_relogio` | ✅ |
| Histórico sem o texto dos trechos | — | ❌ `descrever_evidencias` devolve só `trecho` e `score`, mas nenhum teste confere isso |
| Falha do LLM ou do Qdrant interrompe (regra 8) | `test_falha_do_llm_interrompe_a_verificacao`, `test_falha_do_research_interrompe_a_verificacao` | ✅ |
| Saída inválida do LLM não é falha (regra 8) | `test_saida_invalida_do_analysis_nao_e_falha` | ✅ |
| Perfil chega ao Communication | Cenário "O perfil de leitura chega ao Communication" | ✅ |
| Rota: 200 com veredito e histórico | `test_devolve_o_veredito_e_o_historico`, cenário correspondente | ✅ |
| Rota: perfil padrão | `test_perfil_padrao_e_consumidor_geral` | ✅ |
| Rota: 422 (vazia, mais de 500 caracteres, perfil desconhecido) | `test_entrada_invalida_e_422`, cenário "Alegação vazia é recusada" | ✅ |
| Rota: 503 (LLM ou Qdrant) | `test_llm_ou_qdrant_indisponivel_e_503`, `test_qdrant_com_resposta_inesperada_e_503`, cenário "LLM indisponível" | ✅ |
| Rota: 500 sem detalhes internos | `test_erro_inesperado_e_500_sem_detalhes_internos` | ✅ |
| Rota no OpenAPI (cliente TypeScript gerado) | `test_rota_esta_no_openapi` | ✅ |
| Trace por verificação e span por nó | `test_verificacao_avulsa_abre_o_trace_da_alegacao`, `test_observador_registra_a_verificacao_e_cada_etapa` | ✅ |
| Retorno visível no trace (motivos e destino) | `test_validacao_reprovada_leva_os_motivos_e_o_destino_no_metadado` | ✅ |
| Falha do Langfuse não interrompe | `test_falha_do_langfuse_nao_interrompe_a_verificacao` | ✅ |
| Mascaramento RN30 no trace da verificação | `tests/compartilhado/test_observabilidade_langfuse.py` (cliente com `mask`) | ⚠️ a API usa o cliente de `obter_langfuse` (com o `mask`), mas nenhum teste da verificação confere isso |
| Grafo com um nó por agente e a aresta condicional | `test_grafo_tem_um_no_por_agente_e_a_aresta_condicional` | ✅ |
| Domínio e aplicação sem LangGraph | `test_dominio_e_aplicacao_nao_importam_o_langgraph` | ✅ |
| Verificação sem o domínio do Research | `test_independencia_dos_contextos.py` | ✅ |
| Os dois motores dão o mesmo resultado | Fixture `motor` (`laco` e `langgraph`) em `test_verificar_alegacao.py` e nos passos BDD | ✅ |
| Avaliação pelo orquestrador mantém as métricas | `test_avaliacao.py`, `test_cli.py` | ⚠️ `test_retorno_ao_research_dobra_o_limite_ate_20` ainda fala no teto de 20; conferir o nome com o padrão novo, de 10 |
| Contrato dos quatro prompts | `test_prompts_no_langfuse.py -m langfuse` | ⚠️ roda só com as chaves; precisa rodar antes do PR |

## 5. Dados de teste

- **Dublês** (`tests/verificacao/conftest.py`):
  - `fazer_evidencias(*scores)`: evidências fictícias do Guia Alimentar.
  - `LLMRoteirizado`: respostas prontas por prompt, na ordem das chamadas. Uma `str` simula uma saída que não é JSON.
  - Um pesquisador falso que guarda os limites pedidos.
  - Um relógio que avança 1 s por leitura.
- **Alegações:** só fictícias (ex.: "Ovo aumenta o colesterol?"), sem dados pessoais. O mascaramento é testado com dados inventados no formato de e-mail e CPF.
- **Avaliação:** `data/avaliacao/verificacao/casos_v1.json`, com 15 alegações (5 recicladas, 5 parciais e 5 novas).
- **Referência da avaliação:** `resultados_v1_teto10_prompt-v2.json`. São 15 casos com o `qwen2.5:7b`, temperatura 0 e semente 42, no Mac M4: acurácia de 87%, aprovação direta de 73%, aprovação final de 80%, 0,47 retorno em média e 23,7 s de latência média.

## 6. Ambiente

| Item | Valor |
| --- | --- |
| Python | O do `pyproject.toml` (`>=3.11`); o ambiente local usa o 3.14 |
| Dependências | `poetry install`, que inclui o `langgraph (>=1.2.24,<2.0.0)` |
| Testes automáticos | Sem `.env`: nada de Ollama, Qdrant ou Langfuse |
| Integração e evidência | Ollama com o `qwen2.5:7b`, Qdrant com a coleção `evidencias_verificacao_e5` e as chaves do Langfuse no `.env` |

**Bloqueio encontrado:** o ambiente virtual local (`economia-egS4NZvn-py3.14`) ainda não tem o `langgraph`. Hoje, `test_verificar_alegacao.py` e `test_orquestrador_verificacao.py` falham na coleta, e `test_cli.py::test_orquestrador_da_api_usa_o_grafo_e_os_quatro_prompts` falha. Os outros 152 testes de `tests/verificacao` e `tests/api` passam. É preciso rodar `poetry install` antes de executar este plano.

## 7. Integração local (manual)

Roda depois dos testes automáticos, na máquina com o Ollama e o Qdrant.

| # | Passo | Resultado esperado |
| --- | --- | --- |
| I1 | `poetry run uvicorn economia.api.app:app --port 8000` e `curl -X POST localhost:8000/api/v1/verificacoes -H 'Content-Type: application/json' -d '{"alegacao": "Alimentos ultraprocessados devem ser evitados."}'` | 200 com o veredito `reciclada`, `aprovado_pela_validacao: true` e 4 etapas |
| I2 | Repetir a I1 com `"perfil": "consumidor_rapido"` | Mensagem com até 2 frases e uma fonte |
| I3 | Uma alegação que volta na avaliação (ex.: v05, "Comer com regularidade, devagar e em companhia…") | Histórico com mais de um Research ou Analysis e `retornos` maior que 0 |
| I4 | Parar o Ollama e repetir a I1 | 503 em `application/problem+json` |
| I5 | Parar o Qdrant e repetir a I1 | 503 em `application/problem+json` |
| I6 | `poetry run python -m economia.verificacao.cli avaliar --casos data/avaliacao/verificacao/casos_v1.json --saida data/avaliacao/verificacao/resultados_v2_orquestrador.json --llm qwen2.5:7b` | Ver os critérios da seção 9 |
| I7 | Medir o tempo de resposta da I3 atrás do proxy da VM | Sem tempo esgotado no proxy. Se esgotar, aumentar o tempo limite antes da demo |

## 8. Evidência para a #72

- **E1:** um trace `verificacao.alegacao` aprovado direto, com os spans `research`, `analysis`, `validation` e `communication` e as gerações ligadas à versão do prompt.
- **E2:** um trace com retorno, com o span do Validation mostrando os motivos e o destino no metadado, seguido de um novo Research ou Analysis.
- **E3:** prints dos dois traces e o link do Langfuse na seção 10 da [arquitetura](../../docs/semana-4/arquitetura-agentes.md).
- Conferir nos dois traces que a alegação aparece mascarada, quando tiver dados no formato de e-mail ou CPF (RN30).

## 9. Critérios de aprovação

**Para abrir o PR:**

- Todos os testes automáticos passando com `poetry run pytest -m "not langfuse"`, nos dois motores.
- Os itens ❌ da matriz resolvidos (busca sem limiar e histórico sem o texto dos trechos).
- `ruff check` e `ruff format --check` sem apontamentos.
- `scripts/verificar-commits.sh origin/main HEAD` e `scripts/verificar-branch.sh` sem erros.

**Para fechar a #82:**

- O contrato dos prompts passando com `pytest -m langfuse`.
- Integração I1 a I5 conforme o esperado.
- Avaliação I6 próxima da rodada de referência, com o mesmo prompt de análise:
  - a classificação obtida igual à da referência em pelo menos 13 dos 15 casos;
  - a acurácia e a aprovação final no máximo 1 caso (7 pontos) abaixo da referência.

  Diferença maior indica que o orquestrador mudou o comportamento do laço do Paulo, e não o LLM.
- As evidências E1 e E2 registradas.

## 10. Como rodar

```bash
poetry install
```

```bash
poetry run pytest tests/verificacao tests/bdd/test_orquestrador_verificacao.py tests/api/test_verificacoes.py -m "not langfuse"
```

```bash
poetry run pytest tests/contrato/test_prompts_no_langfuse.py -m langfuse
```

```bash
poetry run pytest -m "not langfuse"
```

## 11. Riscos dos testes

- **Os dublês podem esconder diferenças do LLM real:** o `LLMRoteirizado` devolve respostas na ordem das chamadas. Se a ordem das chamadas mudar, os testes falham sem que o comportamento esteja errado. A integração I6 confere o fluxo real.
- **A avaliação não é totalmente determinística:** com temperatura 0 e semente 42, o Ollama costuma repetir as respostas, mas versões diferentes do Ollama ou do modelo mudam o resultado. Registre a versão do Ollama na saída da avaliação.
- **Orquestrador compartilhado na API:** `obter_verificar_alegacao` usa `lru_cache`, então todas as requisições usam a mesma instância. Os testes não cobrem requisições simultâneas. Antes da demo, rodar duas verificações ao mesmo tempo e conferir que os históricos não se misturam.
