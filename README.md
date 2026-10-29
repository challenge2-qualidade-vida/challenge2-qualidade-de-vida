# EconoMIA 🐈💰

**Inteligência que faz render. Para o seu bolso não miar!**

Challenge 2 — Big Idea: Qualidade de Vida
Residência em IA Brasília (TIC em Trilhas / Mentes em Modo IA em Ação) — Turma 2

> **Big Idea:** empoderar pessoas com IA para compreender melhor, decidir melhor e viver melhor.

## Desafio

Projetar e desenvolver uma solução baseada em IA capaz de apoiar a tomada de decisão em um contexto relacionado à qualidade de vida.

**Essential Question do grupo:**

> **"Tenho R$ X para as compras do mês. Como faço esse dinheiro render sem perder qualidade na alimentação?"**

A EconoMIA é um assistente de IA que ajuda famílias a montar uma cesta de compras **mais econômica e nutricionalmente equilibrada**, considerando preços reais dos mercados próximos, orçamento, tamanho da família e preferências. A partir da cesta, sugere refeições e o aproveitamento dos alimentos, fechando o ciclo **orçamento → cesta → cardápio**.

A IA não decide pelo usuário nem promete o menor gasto possível em todos os casos. Ela organiza as informações, compara as alternativas e explica os critérios para que cada pessoa decida de acordo com sua realidade.

## O problema

- **Os preços variam muito entre mercados** e falta tempo para pesquisar.
- **As informações ficam espalhadas** em encartes, notas fiscais, listas e receitas.
- **Nem toda promoção é economia.** A embalagem pode ser menor, o preço por kg pode ser pior ou o deslocamento pode anular a vantagem.
- **Economizar não pode significar comer pior.** Uma cesta barata pode ficar sem variedade ou com nutrientes insuficientes para o período.
- **Comprar sem planejar as refeições gera desperdício.**
- Os apps que existem resolvem partes isoladas: há comparadores de preço e contadores de calorias (ex.: InOut, BitePal), mas nenhum junta preço, orçamento e nutrição.

**Público:** pessoas e famílias que querem fazer o orçamento da alimentação render, com diferentes rendas, tamanhos de família, preferências alimentares e níveis de familiaridade com tecnologia.

## Funcionalidades

### Núcleo do MVP

1. **Orçamento → cesta priorizada**: o usuário informa R$ X, nº de pessoas, período (semana/mês) e restrições ("não como carne de porco, tenho 3 filhos"). O otimizador monta a cesta respeitando o orçamento e as metas nutricionais e, se não couber, sugere trocas.
2. **Comparação entre mercados próximos**: "cesta mais barata em um só mercado" vs. "dividida em 2 mercados", com a economia de cada opção (às vezes não compensa ir a dois lugares). A comparação usa **preço por kg/L/unidade**, não só o preço da embalagem.
3. **Cardápio a partir da cesta**: refeições possíveis com o que foi comprado.
4. **Explicação da escolha**: "escolhi frango em vez de carne porque cabe no orçamento e mantém a proteína". Toda recomendação mostra o critério e a fonte do preço.

### Diferenciais (se der tempo)

- **"Essa promoção vale a pena?"**: compara o preço por unidade de medida, o histórico e o que já está na lista.
- **Substituições inteligentes**: "feijão carioca subiu 30%, troque por feijão preto ou lentilha, com valor nutricional parecido".
- **"O que tem em casa?" / aproveitamento**: o usuário informa o que sobrou e a IA sugere receitas, priorizando o que precisa ser usado primeiro e o que falta comprar.
- **Histórico de preços**: variações ao longo do tempo, só quando houver dados suficientes (sem afirmar que "terça é sempre o melhor dia").

### Fora do MVP

- **Dieta personalizada para condições de saúde.** Entra no campo do nutricionista e aumenta o risco e a parte de privacidade. O foco é **alimentação equilibrada para a população geral**, e o app deixa isso explícito.
- Foto de cupom fiscal por OCR (erra muito; usamos o QR code, ver abaixo).
- Leitura de encartes promocionais.

## Fonte dos preços

Sem preço real, a cesta inteligente vira ficção. É provavelmente a primeira pergunta da banca.

| Fonte | Como funciona | Quando |
|-------|---------------|--------|
| **Base controlada (MVP)** | Cesta básica do DIEESE de Brasília + cerca de 50 itens coletados à mão pelo grupo em 3 ou 4 mercados próximos | Semana 2 em diante |
| **QR code da NFC-e** | O usuário escaneia o QR code do cupom. A NFC-e já traz produto, preço, data e mercado corretos, sem depender de OCR. Cada compra alimenta a base para todos (colaborativo) | Semana 5 (multimodalidade) |

**Transparência como funcionalidade:** todo preço aparece com origem e data, por exemplo *"R$ 8,49 — Mercado X, 12/10, 3 confirmações"*. O app distingue preço confirmado, histórico, estimado e informado pelo usuário.

## Arquitetura de IA

**Princípio:** o LLM entende e explica, as contas ficam com código determinístico. Assim a IA não "alucina" preço nem calorias.

```
Usuário (linguagem natural)
        │
        ▼
   LLM com ferramentas (tool use) ──────► RAG: Guia Alimentar + Tabela TACO + receitas
        │
        ├──► buscar_precos()      → base estruturada de preços (DIEESE, coleta, NFC-e)
        ├──► otimizar_cesta()     → otimizador (programação linear / heurística)
        ├──► comparar_mercados()  → 1 mercado vs. 2 mercados
        └──► verificar()          → confere orçamento, nutrientes e restrições
        │
        ▼
Resposta explicada, com fontes e limitações
```

| Componente | Papel |
|------------|-------|
| **Otimizador** (programação linear ou heurística) | Minimiza o custo respeitando orçamento, nutrientes mínimos e variedade. Determinístico e auditável. |
| **Base de preços** (estruturada) | Fonte única de preços atuais. Preço **nunca** vem do RAG nem do LLM. |
| **LLM + RAG** | Base: *Guia Alimentar para a População Brasileira* (Ministério da Saúde), **Tabela TACO** (Unicamp), receitas e orientações de conservação de alimentos. Explica escolhas, gera cardápios e entende pedidos em linguagem natural. |
| **Verificação** | Funções que conferem se a cesta respeita orçamento, metas nutricionais e restrições antes da resposta ir ao usuário. |

### Experimento LLM × LLM + RAG (semana 3)

Mesmas perguntas, mesmos critérios, com gabarito preparado pelo grupo:

- **A — LLM sozinho** vs. **B — LLM + RAG**
- Perguntas sobre produtos, nutrição, receitas, comparação de preços, orçamento e informações **ausentes** da base.
- Métricas: correção factual, fundamentação nas fontes, relevância, tratamento de incerteza, latência e custo por pergunta.
- Resultado esperado: decidir com dados em quais tarefas o RAG vale a pena e quando uma chamada simples ao LLM basta.

### Multiagentes (semana 4)

Começamos com **um LLM que usa ferramentas**. Cinco agentes mais um orquestrador desde o início ficariam lentos e passariam do limite do plano gratuito da API. Na semana 4, separamos em agentes apenas o que se mostrar necessário, mantendo os nomes da marca:

| Agente | Papel | Prioridade |
|--------|-------|------------|
| **Orquestrador** | Coordena as tarefas e monta a resposta final | MVP |
| **Cifrão** | Preços, comparação entre mercados, "essa promoção vale a pena?" | MVP |
| **Miau-ricio** | Nutrição, cardápio e aproveitamento de alimentos (via RAG) | MVP |
| **Mia** | Verifica cálculos, orçamento, metas nutricionais e se as limitações foram comunicadas | MVP |
| **Recibaldo** | Lê o QR code da NFC-e e cadastra os preços | Semana 5 |

Todos usam o mesmo LLM, com instruções e ferramentas diferentes. O planejamento da lista fica com o orquestrador + otimizador, sem agente próprio.

## Riscos

| Risco | Por que importa | Como reduzir |
|-------|-----------------|--------------|
| Preços desatualizados | A cesta parece barata, mas custa mais no mercado | Mostrar data e fonte de cada preço; atualizar via NFC-e colaborativa |
| Recomendações nutricionais inadequadas | Pode ignorar alergias, restrições ou necessidades individuais | Regras nutricionais de fontes oficiais (Guia Alimentar, TACO); verificação pela Mia; aviso de que não substitui nutricionista |
| Alucinação do LLM | Inventar preço, caloria ou receita | Preço e cálculo só em código determinístico; RAG com citação de fonte; resposta "não sei" quando a base não cobre |
| Otimização enganosa | Menor preço total, mas pouca variedade ou quantidade insuficiente | Avaliar custo, quantidade, variedade e adequação nutricional em conjunto |
| Viés socioeconômico ou regional | Recomendar alimentos indisponíveis ou caros em certas regiões | Considerar localização, disponibilidade, cultura alimentar e orçamento |
| Privacidade (LGPD) | Orçamento, hábitos alimentares e saúde são dados sensíveis | Coletar o mínimo necessário, não armazenar CPF da NFC-e, proteger e limitar acessos |
| Dependência de fornecedores | Dados incompletos podem favorecer produtos ou lojas sem justificativa | Comparar fontes, explicitar critérios e sempre oferecer alternativas |

## Métricas

> ⭐ **Métrica principal: economia sem perda de qualidade.** Não adianta economizar 20% se a cesta ficar nutricionalmente inadequada ou não alimentar a família pelo período.

| # | Métrica | Como medir |
|---|---------|-----------|
| 1 | **Economia média por cesta** | Diferença % entre a cesta recomendada e a cesta básica DIEESE Brasília, com quantidades e período comparáveis |
| 2 | **Aderência ao orçamento** | % de cestas cujo custo fica dentro do limite informado |
| 3 | **Adequação nutricional** | % de cestas que cumprem as metas nutricionais definidas (Guia Alimentar / TACO), incluindo variedade e restrições |
| 4 | **Custo por 1.000 kcal e por grama de proteína** | "Economia sem perda de qualidade" em um número só |
| 5 | **Precisão de preço** | % de itens cujo preço no app bate com a gôndola (±5%), verificado pelo grupo em uma amostra |
| 6 | **Qualidade dos dados** | % de preços válidos, atualizados e verificáveis; taxa de produtos indisponíveis |
| 7 | **Qualidade das respostas (LLM × RAG)** | Correção, fundamentação, tratamento de incerteza, latência e custo (experimento da semana 3) |
| 8 | **Utilidade percebida** | % de usuários de teste que consideram as recomendações úteis e conseguem montar a cesta |

## Equipe

| Nome | GitHub | Papel |
|------|--------|-------|
| Guilherme Barros | @dida0982 | Backend e IA/RAG |
| Isabel Azar | @iAiBel | |
| | | |
| | | |

## Restrições do desafio

| Restrição | Como a EconoMIA atende |
|-----------|------------------------|
| Entender o problema antes da solução | Seção [O problema](#o-problema) e [docs/semana-1](docs/semana-1) |
| Justificar decisões técnicas | Experimento LLM × RAG e registro em [docs/decisoes.md](docs/decisoes.md) |
| Explicitar riscos e limitações | Seção [Riscos](#riscos); o app mostra fonte, data e limitações em cada resposta |
| Validar com métricas objetivas | Seção [Métricas](#métricas), com referência DIEESE e verificação em gôndola |
| Utilizar evidências confiáveis | Guia Alimentar, Tabela TACO, DIEESE e NFC-e, registrados em [FONTES.md](data/base-conhecimento/FONTES.md) |

## Roadmap

| Semana | Foco | Entregável da EconoMIA | Pasta |
|--------|------|------------------------|-------|
| 1 | Problema, stakeholders, riscos e métricas | Definições do projeto (este README + definições) | [docs/semana-1](docs/semana-1) |
| 2 | Base de conhecimento e recuperação | RAG com Guia Alimentar + TACO; base de preços DIEESE + coleta em 3–4 mercados | [docs/semana-2](docs/semana-2) |
| 3 | Comparação LLM × RAG | Experimento com gabarito e decisão de arquitetura documentada | [docs/semana-3](docs/semana-3) |
| 4 | Sistema multiagentes | Otimizador de cesta + Orquestrador, Cifrão, Miau-ricio e Mia | [docs/semana-4](docs/semana-4) |
| 5 | Multimodalidade | Recibaldo: leitura do QR code da NFC-e alimentando a base de preços | [docs/semana-5](docs/semana-5) |
| 6 | Integração completa | Aplicação funcional: orçamento → cesta → comparação → cardápio | [docs/semana-6](docs/semana-6) |
| 7 | Testes e refinamento | Avaliação com as métricas, relatório final e apresentação | [docs/semana-7](docs/semana-7) |

> ⚠️ **Cuidado com o escopo:** "tudo que tem a ver com alimentação" não cabe em 7 semanas. A prioridade é o fluxo central (orçamento → cesta → cardápio) bem feito. Diferenciais só entram depois dele.

## Estrutura do repositório

```
docs/                    documentação e entregáveis de cada semana
  semana-1/              definições do projeto (problema, stakeholders, riscos, métricas)
  decisoes.md            decisões técnicas e justificativas
  challenge2_resumo.xlsx resumo do desafio
data/base-conhecimento/  Guia Alimentar, TACO e demais fontes do RAG (ver FONTES.md)
src/                     código da aplicação (otimizador, RAG, agentes, interface)
notebooks/               experimentos e análises (ex.: LLM × RAG)
tests/                   testes e avaliação com métricas
```

## Referências

- Documento do grupo: *Challenge 2 – grupo 3 (EconoMIA)*
- Plano *Cesta Inteligente — Plano do Challenge 2* (Notion)
- [Guia Alimentar para a População Brasileira](https://www.gov.br/saude/pt-br/assuntos/saude-brasil/publicacoes-para-promocao-a-saude/guia_alimentar_populacao_brasileira_2ed.pdf) — Ministério da Saúde
- [Tabela TACO](https://nepa.unicamp.br/publicacoes/tabela-taco-pdf/) — NEPA/Unicamp
- [Cesta Básica de Alimentos](https://www.dieese.org.br/cesta/) — DIEESE
- Apps de referência (concorrentes): InOut e BitePal (contadores de calorias)

## Desenvolvimento

O passo a passo do que foi construído, como foi feito e como rodar está em [docs/desenvolvimento/](docs/desenvolvimento/README.md). O projeto avança um tópico por vez, na branch `develop_gui`, usando só ferramentas gratuitas.

```bash
git checkout develop_gui
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Como trabalhar no repositório

Veja [CONTRIBUTING.md](CONTRIBUTING.md).
