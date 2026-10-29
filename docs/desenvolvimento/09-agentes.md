# Tópico 9 — Sistema multiagente

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

Os agentes com os nomes da marca, cada um com uma responsabilidade, coordenados por um orquestrador. Seguimos a recomendação da comparação das propostas: **não** cinco agentes com LLM em fila, o que seria lento e estouraria planos gratuitos, e sim **só onde cada agente agrega**.

| Agente | Papel | Usa LLM? | Ferramentas |
|--------|-------|----------|-------------|
| **Orquestrador** | Decide quem atende a pergunta e junta o resultado | ❌ regras (sem custo, instantâneo) | — |
| **Cifrão** 💰 | Preços, promoções e cesta | ✅ | `montar_cesta`, `consultar_precos`, `avaliar_promocao` |
| **Miau-ricio** 🐈 | Nutrição, aproveitamento, receitas e **cardápio a partir da cesta** | ✅ | RAG (trechos da base) |
| **Mia** 🔎 | Confere a resposta antes de ela chegar ao usuário | ❌ regras (determinística) | — |
| **Recibaldo** 🧾 | Lê o cupom fiscal (NFC-e) | ❌ visão computacional | ver [tópico 10](10-nfce-multimodal.md) |

Todos os agentes com LLM usam **o mesmo modelo gratuito**, cada um com seu prompt e suas ferramentas. Assim não é preciso ter um modelo por agente.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/agentes.py](../../src/economia/agentes.py) | Orquestrador, prompts do Cifrão e do Miau-ricio, verificação da Mia, cardápio |
| [src/economia/assistente.py](../../src/economia/assistente.py) | Agora aceita `prompt_sistema` e uma lista de `ferramentas` por agente, e registra `etapas` |
| [src/economia/api.py](../../src/economia/api.py) | `/api/chat` usa o orquestrador; novo `POST /api/cardapio` |
| [src/web/](../../src/web/) | Botão **Sugerir cardápio** na cesta; etapas dos agentes no chat |
| [tests/test_agentes.py](../../tests/test_agentes.py) | 23 testes |

## Como funciona

```
pergunta
   │
Orquestrador (regras)
   ├─ saúde ("remédio", "pressão alta", "diabetes"...) ─► resposta fixa: procure médico ou nutricionista   (sem LLM)
   ├─ preço / promoção / cesta (interpretar)          ─► Cifrão  ─┐
   ├─ nutrição / receitas / há trecho na base         ─► Miau-ricio ┤
   └─ nada disso                                      ─► "Só consigo ajudar com compras, preços e alimentação."   (sem LLM)
                                                                    │
                                                                   Mia (regras) ─► resposta final + etapas
```

Na tela, cada resposta mostra o caminho percorrido, por exemplo: *Agentes: Orquestrador: encaminhou para Cifrão → Cifrão: respondeu → Mia: verificou a resposta → Mia: acrescentou o aviso de preços de exemplo*.

### Por que o Orquestrador e a Mia não usam LLM

- **Orquestrador:** decidir o caminho com uma chamada de LLM custaria mais 5–15 s em cada pergunta. As regras (`interpretar` + palavras-chave + "há trecho na base?") já acertaram todas as rotas dos testes.
- **Mia:** quem verifica não pode errar do mesmo jeito que quem é verificado. Usar o próprio LLM para conferir o LLM repetiria as alucinações. Regras determinísticas pegam exatamente os erros medidos no tópico 8.

### O que a Mia confere

| Verificação | Regra | O que ela faz |
|-------------|-------|---------------|
| **Valor que não confere** | Todo "R$ x" da resposta precisa estar nos dados das ferramentas ou na pergunta do usuário | Troca a resposta pelo texto calculado (`explicar`, `texto_promocao`...) |
| **Fonte inventada (link)** | Link na resposta que não está na base | **Bloqueia**: "A base da EconoMIA não tem uma fonte confiável sobre isso..." |
| **Fonte inventada (citação)** | Cita [3], mas só 2 trechos foram usados | Bloqueia |
| **Número sem fonte** | Em resposta de conhecimento, número com unidade (mg, g, kcal, %) que não aparece nos trechos | Bloqueia |
| **Aviso de preço de exemplo** | Usou preço de fonte "exemplo" e não avisou | Acrescenta o aviso |
| **Restrição violada** | Resposta cita "frango" para quem é vegetariano, "leite" para quem não tem lactose... | Acrescenta um alerta |

As três verificações de fonte nasceram do experimento: na pergunta sobre a acerola, o LLM com RAG inventou *"Guia Alimentar da Economia"* com um link falso do gov.br.

### Cardápio a partir da cesta (funcionalidade 3 do MVP)

Depois de montar a cesta, o botão **Sugerir cardápio** envia a lista de alimentos ao Miau-ricio. Ele recebe as receitas da base que combinam com esses alimentos e monta 3 dias de almoço e jantar **usando só o que está na lista**. A Mia confere as restrições. Sem LLM, o app lista as receitas da base que usam alimentos da cesta.

Isso fecha o ciclo **orçamento → cesta → cardápio** do README.

## Resultado no experimento (abordagem D)

O experimento do [tópico 8](08-experimento-llm-rag.md) foi rodado de novo com a abordagem **D — agentes**, com o mesmo modelo e as mesmas 17 perguntas:

| Critério | A — LLM sem RAG | B — LLM + RAG | C — sem LLM | **D — agentes** |
|---|---|---|---|---|
| Correção | 59% | 94% | 82% | **94%** |
| Fundamentação | 0% | 80% | 100% | **100%** |
| Tratamento de incerteza | 75% | 75% | 50% | 75% |
| Latência média | 10,4 s | 16,4 s | 0,0 s | **14,2 s** |
| Tokens por pergunta | 1.312 | 1.742 | 0 | **1.150** |

(O C subiu de 76% para 82% com a correção do `interpretar` feita neste tópico.)

**O que mudou de B para D nos casos críticos:**

| Pergunta | B — LLM + RAG | D — agentes |
|----------|---------------|-------------|
| Vitamina C da acerola (não está na base) | ❌ inventou "238 mg" e um link falso do gov.br | ✅ Mia bloqueou: "a base não tem uma fonte confiável sobre isso" |
| Remédio para pressão alta | ✅ recusou (mas dependia do LLM obedecer) | ✅ resposta fixa, sem chamar o LLM |
| Copa de 2002 | ✅ recusou (idem) | ✅ recusa fixa, em **0 s** |
| "Melhor dia para comprar no Mercado A" | ✅ | ❌ pelo critério automático, mas a resposta **não inventou** um dia: disse que depende do planejamento. É um falso negativo do critério de palavras-chave |

D empata com B na correção, mas **remove a alucinação mais grave** (fonte falsa com cara de oficial), garante as recusas sem depender do LLM e gasta **34% menos tokens**, porque perguntas fora do tema e de saúde não chamam o modelo.

## Limitações conhecidas

- A Mia confere números e fontes, **não o sentido** da frase. Uma afirmação errada, sem número e citando um trecho real, passa.
- O roteamento por palavras-chave pode mandar uma pergunta para o agente errado se ela misturar assuntos ("quanto custa uma refeição saudável?"). O agente ainda responde, só que com as ferramentas de outro.
- O cardápio leva cerca de 40 s com o `qwen2.5:7b` local. O modelo às vezes responde em Markdown (`###`, `**`), então o site remove essas marcações antes de mostrar.
- O cardápio depende do LLM seguir a regra "só alimentos da lista". A Mia confere as restrições, mas não se apareceu um ingrediente que não foi comprado.

## Testes

```bash
pytest tests/test_agentes.py -v
```

Conferem: a Mia aceita valores das ferramentas e da pergunta, pega valor inventado, cobra o aviso de preço de exemplo, pega restrição violada, bloqueia link inventado e número que não está nos trechos, e não cobra citação em resposta de preço; o roteamento de 6 perguntas típicas; fora do tema e saúde **não chamam o LLM**; o Cifrão recebe só as ferramentas de preço; a Mia troca uma resposta com valor inventado; o Miau-ricio recebe os trechos e nenhuma ferramenta; o modo sem LLM continua passando pela Mia; "dois mercados" sem preço não é promoção; e o cardápio com e sem LLM.

**Resultado em 29/10/2026:** 127 testes passando no projeto.
