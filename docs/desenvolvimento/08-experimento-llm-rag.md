# Tópico 8 — Experimento LLM × LLM + RAG

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

O experimento previsto para a semana 3 no documento da EconoMIA (seção 5.4): **as mesmas perguntas, com os mesmos critérios e com gabarito**, respondidas por três abordagens. O objetivo era decidir **com dados** a arquitetura final, e não presumir que uma tecnologia é melhor.

| Arquivo | Conteúdo |
|---------|----------|
| [data/experimento/perguntas.json](../../data/experimento/perguntas.json) | 17 perguntas e o gabarito de cada uma |
| [src/economia/avaliacao.py](../../src/economia/avaliacao.py) | Critérios automáticos de correção |
| [experimentos/llm_x_rag.py](../../experimentos/llm_x_rag.py) | Script que roda o experimento e gera o relatório |
| [docs/semana-3/resultados-llm-x-rag.md](../semana-3/resultados-llm-x-rag.md) | **Relatório gerado**, com todas as respostas |
| [docs/semana-3/resultados-llm-x-rag.csv](../semana-3/resultados-llm-x-rag.csv) | Os mesmos dados em planilha, para revisão humana |
| [tests/test_avaliacao.py](../../tests/test_avaliacao.py) | 6 testes dos critérios |

## Desenho do experimento

### As abordagens

| | Abordagem | O que recebe |
|---|---|---|
| **A** | LLM sem RAG | Prompt de regras + ferramentas de preço e cesta. **Sem** a base de conhecimento |
| **B** | LLM + RAG | O mesmo que A **mais** os 3 trechos mais relevantes da base, junto com a pergunta |
| **C** | Sem LLM (linha de base) | Regras (`interpretar`) + ferramentas + trechos da base, sem modelo de linguagem |

**A e B usam o mesmo modelo** (`qwen2.5:7b` no Ollama, gratuito e local), com **temperatura 0**. A única diferença entre os dois é o RAG, então qualquer diferença no resultado vem dele.

### As perguntas (17)

| Categoria | Qtd. | Exemplos | Resposta certa |
|-----------|------|----------|----------------|
| conhecimento | 10 | regra de ouro, ultraprocessados, arroz com feijão, proteína da lentilha (TACO), embalagem maior compensa? | conter os termos do gabarito |
| ferramenta | 3 | "Arroz 5 kg por R$ 24,90 é boa promoção?", "Quanto custa o feijão preto?", cesta de R$ 700 | valor certo **e** chamar a ferramenta certa |
| ausente | 2 | vitamina C da acerola, "melhor dia para comprar no Mercado A" | **reconhecer** que a base não tem a informação |
| fora do tema | 1 | "Quem ganhou a Copa de 2002?" | recusar |
| saúde | 1 | "Qual remédio tomar para pressão alta?" | recusar e indicar profissional |

### Os critérios (todos automáticos)

| Critério | Como é medido |
|----------|---------------|
| **Correção** | A resposta tem pelo menos um termo de **cada** grupo do gabarito (sem acento, minúsculas). Para as perguntas de recusa: a resposta tem um sinal de recusa ("não tem", "só consigo ajudar", "procure um profissional"...) |
| **Fundamentação** | Nas perguntas de conhecimento: cita um marcador [n] **e** há fontes reais da base por trás |
| **Tratamento de incerteza** | Nas perguntas "ausente", "fora do tema" e "saúde": recusou em vez de inventar |
| **Ferramenta certa** | Nas perguntas de preço e cesta: chamou a ferramenta esperada |
| **Latência** | Tempo da pergunta até a resposta |
| **Custo** | Tokens de entrada + saída (R$ 0, porque o modelo é local) |

Os critérios são **simples de propósito**: qualquer pessoa consegue refazer a conta. A desvantagem é que eles não entendem sinônimos. Por isso o relatório traz **todas as respostas**, para conferência humana.

## Resultados

Rodado em 29/10/2026, `ollama/qwen2.5:7b`. Relatório completo em [resultados-llm-x-rag.md](../semana-3/resultados-llm-x-rag.md).

| Critério | A — LLM sem RAG | **B — LLM + RAG** | C — sem LLM |
|---|---|---|---|
| Correção | 59% | **94%** | 76% |
| Fundamentação (cita a base) | 0% | **80%** | 90% |
| Tratamento de incerteza | 75% | 75% | 50% |
| Usou a ferramenta certa | 100% | 100% | 100% |
| Latência média | 10,4 s | 16,4 s | 0,0 s |
| Tokens por pergunta | 1.312 | 1.742 | 0 |
| Custo | R$ 0,00 | R$ 0,00 | R$ 0,00 |

**Correção por categoria:**

| Categoria | A | B | C |
|---|---|---|---|
| conhecimento (10) | 40% | **100%** | 80% |
| ferramenta (3) | 100% | 100% | 100% |
| ausente (2) | 50% | 50% | 50% |
| fora do tema (1) | 100% | 100% | 100% |
| saúde (1) | 100% | 100% | 0% |

## O que os números mostram

**1. O RAG é o que faz a diferença no conhecimento: 40% → 100%.** Sem a base, o LLM:

- **inventou fontes**: citou "[1] Instituto Brasileiro de Análise de Sistemas (IBAS)" e "[1] INCT-Açaí", que não existem na base;
- **errou números**: disse que a lentilha tem "9 a 10 g de proteína por 100 g", quando a TACO dá **23,2 g**;
- **recusou o que devia responder**: disse "só consigo ajudar com compras" para a pergunta sobre calorias do arroz.

**2. Para preços e cesta, o RAG não muda nada (100% nos dois).** Os números vêm das ferramentas, e isso confirma a decisão de **nunca deixar preço no RAG nem no LLM**.

**3. Mesmo com RAG, o LLM ainda alucina quando a base não tem a resposta.** Na pergunta sobre a acerola (que não está na base), a abordagem B respondeu "238 mg de vitamina C, de acordo com o **Guia Alimentar da Economia** [1]" e inventou um link do gov.br. É o caso mais grave do experimento: **uma fonte falsa com aparência oficial**. O RAG reduz a alucinação, mas não a elimina.

**4. O modo sem LLM é rápido e fundamenta bem, mas entende pouco.** Confundiu "quando *vale a pena* ir a dois mercados" com uma pergunta de promoção, devolveu trechos sem relação para a pergunta de remédio e não reconhece perguntas sobre algo que a base não tem.

**5. O custo do RAG é pequeno:** cerca de 6 s e 430 tokens a mais por pergunta, sem custo em dinheiro.

## Decisão de arquitetura

> **Adotamos a abordagem B (LLM + RAG) como base, com três proteções adicionais no tópico 9**, cada uma motivada por uma falha medida aqui:

| Falha observada | Proteção (tópico 9) |
|-----------------|---------------------|
| Fonte inventada com link falso (B, acerola) | **Mia** confere as citações: link que não está na base ou número [n] que não existe → a resposta é trocada por "a base não tem essa informação" |
| Remédio para pressão alta (C) | **Orquestrador** responde perguntas de saúde com uma mensagem fixa, recomendando um profissional, **sem** chamar o LLM |
| "Vale a pena ir a dois mercados" lido como promoção (C) | `interpretar` só considera promoção quando há um preço na frase |

O modo C continua como **reserva** para quando o LLM está fora do ar: é instantâneo, gratuito e sempre fundamenta.

## Limitações do experimento

- **17 perguntas** é pouco para conclusões estatísticas. Os resultados mostram tendências claras (40% × 100% no conhecimento), mas o grupo deve ampliar o conjunto.
- **Uma rodada por abordagem.** A temperatura 0 reduz a variação, mas não a elimina.
- **Correção por palavras-chave** pode errar nos dois sentidos: aceitar uma resposta que tem o termo mas está errada, ou recusar uma resposta certa escrita com sinônimos. Revisar o CSV manualmente é o próximo passo.
- **Um modelo só** (7B, local). Modelos maiores (Groq, Gemini) podem ter resultados diferentes. Para comparar, basta rodar o script com `LLM_PROVEDOR=groq`.

## Como rodar de novo

```bash
ollama serve                                     # se o Ollama não estiver rodando
.venv/bin/python experimentos/llm_x_rag.py       # ~10 min com qwen2.5:7b

# com outro modelo
LLM_MODELO=qwen2.5:3b .venv/bin/python experimentos/llm_x_rag.py
```

Para **adicionar perguntas**, edite `data/experimento/perguntas.json`. Cada pergunta tem `id`, `categoria`, `pergunta` e então `deve_conter` (lista de grupos de termos), ou `deve_recusar: true`, e opcionalmente `ferramenta`.

## Testes

```bash
pytest tests/test_avaliacao.py -v
```

Conferem que as perguntas do JSON são válidas, a regra "um termo de cada grupo", a detecção de recusa, a detecção de citação (marcador **e** fonte) e a avaliação de perguntas de recusa e de ferramenta.
