# Tópico 6 — Base de conhecimento e RAG

**Status:** ✅ concluído em 29/10/2026 (parte de recuperação; a geração entra no tópico 7)

## O que foi feito

A **base de conhecimento** que fundamenta as respostas da EconoMIA e o **mecanismo de busca** que encontra o trecho certo para cada pergunta. É o "R" (*retrieval*, recuperação) do RAG. O "G" (*generation*, geração) acontece quando esses trechos vão para o LLM, no tópico 7.

| Arquivo | Conteúdo |
|---------|----------|
| [data/base-conhecimento/guia-alimentar-principios.md](../../data/base-conhecimento/guia-alimentar-principios.md) | Regra de ouro, classificação dos alimentos, 10 passos |
| [data/base-conhecimento/guia-alimentar-grupos.md](../../data/base-conhecimento/guia-alimentar-grupos.md) | Grupos de alimentos, arroz com feijão, como montar refeições |
| [data/base-conhecimento/compras-e-economia.md](../../data/base-conhecimento/compras-e-economia.md) | Preço por kg, "essa promoção vale a pena?", 1 × 2 mercados, substituições |
| [data/base-conhecimento/aproveitamento-e-receitas.md](../../data/base-conhecimento/aproveitamento-e-receitas.md) | Ordem de uso dos alimentos, sobras, 5 receitas com itens da cesta |
| [data/base-conhecimento/FONTES.md](../../data/base-conhecimento/FONTES.md) | Lista de fontes, com link e justificativa |
| [src/economia/rag.py](../../src/economia/rag.py) | Leitura dos documentos, índice TF-IDF e busca |
| [tests/test_rag.py](../../tests/test_rag.py) | 13 testes |

> ⚠️ Os textos do Guia Alimentar são **resumos escritos pelo grupo**, não cópia do documento. Antes da entrega, alguém precisa conferir cada seção com o PDF original (link em FONTES.md). As receitas são do grupo e também precisam de revisão.

## O que é RAG, no nosso caso

```
pergunta do usuário ──► busca na base (TF-IDF) ──► 3 trechos mais parecidos ──► LLM responde usando os trechos e cita a fonte
                                                    └─ nenhum trecho? ──► "a base não tem essa informação"
```

**O que o RAG NÃO faz:** informar preço atual. Preço vem **só** da base estruturada (`precos.json`) e do otimizador. Um documento recuperado por semelhança de texto pode estar desatualizado, então nunca é usado como fonte de preço. Essa regra está no documento da EconoMIA (seção 5.2) e é seguida no tópico 7.

## Como funciona

### 1. Os documentos viram trechos

- Cada arquivo `.md` da pasta tem um título (`# ...`), uma linha `> Fonte: ...` e seções (`## ...`).
- **Cada seção vira um trecho** com id, título, texto e fonte. Seções curtas e com um assunto só deixam a busca mais precisa.
- Cada um dos 28 alimentos da TACO (de `alimentos.json`) também vira um trecho, por exemplo: *"Feijão carioca (cru): por 100 g tem 329 kcal, 20 g de proteína e 18.4 g de fibra. Grupo: feijões."*
- Total atual: **56 trechos**.

Para **adicionar conhecimento**, basta criar um `.md` novo na pasta seguindo o mesmo formato e registrar em `FONTES.md`. Não precisa mudar código.

### 2. Índice TF-IDF

O **TF-IDF** dá peso a cada palavra: alto se ela aparece muito no trecho (TF) e é rara no resto da base (IDF). A pergunta e os trechos viram vetores, e a busca escolhe os trechos com maior **similaridade do cosseno**.

Antes de indexar, o texto passa por `tokenizar()`:

- tudo em minúsculas e **sem acento** ("promoção" = "promocao");
- tira palavras sem conteúdo (*stopwords*: "de", "que", "para"...);
- trata o plural simples ("frutas" → "fruta");
- usa palavras isoladas e pares de palavras ("preço quilo").

### 3. Limiar de "não sei"

Se nenhum trecho tem similaridade ≥ **0,12** (`SIMILARIDADE_MINIMA`), a busca devolve lista vazia. É assim que o sistema **reconhece quando a base não tem a informação**, um dos critérios do experimento do tópico 8.

O limiar foi calibrado com perguntas fora do tema:

| Pergunta | Maior similaridade | Resultado |
|----------|--------------------|-----------|
| quem ganhou a copa do mundo de futebol | 0,00 | nada (correto) |
| como pagar boleto | 0,00 | nada (correto) |
| previsão do tempo amanhã | 0,115 | nada, mas **perto do limiar**: a palavra "tempo" aparece no 10º passo do Guia |
| essa promoção vale a pena? | bem acima | trecho certo |

**Ponto de atenção:** perguntas fora do tema com palavras comuns da base podem passar do limiar. No tópico 7, o LLM recebe a instrução de dizer que não sabe quando o trecho não responde à pergunta, o que serve de segunda barreira.

## Por que TF-IDF e não embeddings + ChromaDB?

O plano inicial falava em *sentence-transformers* + *ChromaDB*. Mudamos para TF-IDF porque:

| | TF-IDF (scikit-learn) | Embeddings (sentence-transformers) |
|---|---|---|
| Custo | grátis | grátis |
| Instalação | ~10 MB | `torch` (centenas de MB) + download do modelo |
| Velocidade | instantâneo | mais lento sem GPU |
| Resultado | o mesmo sempre (determinístico) | o mesmo sempre |
| Entende sinônimos | ❌ ("barato" ≠ "econômico") | ✅ |
| Base de 56 trechos | suficiente | sobra |

Para uma base pequena, com vocabulário controlado e escrita pelo próprio grupo, o TF-IDF resolve, e é mais leve para publicar no plano gratuito (tópico 12). Se o experimento do tópico 8 mostrar falhas por sinônimos, a troca para embeddings afeta só `BaseConhecimento`: o resto do código não muda.

## Como usar

```python
from economia.dados import carregar
from economia.rag import BaseConhecimento, contexto_para_llm

bc = BaseConhecimento(carregar())
resultados = bc.buscar("essa promoção vale a pena?", k=3)
print(contexto_para_llm(resultados))   # texto numerado [1], [2]... com as fontes, pronto para o LLM
```

Pela API: `GET /api/conhecimento?pergunta=essa promoção vale a pena?` (dá para testar em <http://localhost:8000/docs>).

## Testes

```bash
pytest tests/test_rag.py -v
```

Conferem que: a base tem trechos de todos os documentos e da TACO, todos com fonte; **8 perguntas típicas** encontram o trecho certo entre os 3 primeiros (promoção, ultraprocessados, regra de ouro, preço por kg, proteína do feijão, banana madura, receita de lentilha, dois mercados); pergunta fora do tema não retorna nada; os resultados vêm ordenados; o tokenizador tira acentos, stopwords e plural; e o contexto para o LLM vem numerado e com fonte. Mais um teste na API confere o endpoint `/api/conhecimento`.

**Resultado em 29/10/2026:** 51 testes passando no projeto.
