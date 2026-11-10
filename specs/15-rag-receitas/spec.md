# Spec: receitas e perguntas sobre alimentação (RAG)

| Campo | Valor |
| --- | --- |
| Issue | #15 (épico), implementação em #16 a #24 |
| Status | Rascunho |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema

Comprar alimentos sem pensar nas refeições leva a desperdício e a gastos desnecessários. A pessoa não sabe o que cozinhar com o que já tem, como aproveitar sobras, como conservar os alimentos nem como avaliar o que compra.

## Comportamento esperado

A pessoa faz uma pergunta em linguagem natural de dois tipos:

1. **Sugestão de receita.** A pessoa diz os ingredientes que tem ou pede para o sistema analisar as notas recentes. O sistema sugere receitas da base que usam os ingredientes disponíveis, diz o que falta em cada uma e permite mandar os ingredientes que faltam para a lista de compras. Receitas que violam uma restrição do perfil ficam de fora, e o sistema avisa. Quando a base não tem receitas para aqueles ingredientes, o sistema busca novas receitas na fonte e avisa a pessoa quando a busca termina.
2. **Pergunta sobre alimentação.** Aproveitamento e conservação de alimentos, alimentação saudável (Guia Alimentar) e consumo (preço unitário, como avaliar promoções). O sistema busca trechos relevantes na base de conhecimento e responde com base neles, citando as fontes.

O sistema não pede à pessoa nada que possa obter sozinho, nem mantém uma despensa (princípio de usabilidade do modelo de domínio).

## Termos do domínio

`Alimento`, `Receita`, `Ingrediente`, `IngredientesDisponiveis`, `BuscaDeReceitas`, `Fonte`, `Trecho`, `Restricao`, `ListaDeCompras`, `NotaFiscal`.

Eventos: `BuscaDeReceitasSolicitada`, `BuscaDeReceitasConcluida`.

## Regras de negócio

- **RN04:** a base de conhecimento não é fonte de preço atual.
- **RN10:** respostas baseadas na base de conhecimento citam a fonte.
- **RN11:** sem informação na base, a resposta diz que não encontrou, sem inventar.
- **RN13:** receitas priorizam os ingredientes disponíveis e, entre elas, as que não exigem comprar nada. Se a pessoa pedir receitas só com os itens que informou, nenhuma receita usa outro ingrediente.
- **RN21:** não há despensa. Os itens das notas recentes viram ingredientes disponíveis só quando a pessoa pede, e ela pode tirar ou acrescentar itens.
- **RN26 (a definir, fora da versão 1):** sem receitas na base, o sistema avisa, dispara a busca de receitas e notifica a pessoa quando termina. Sem resultado, explica que não encontrou e pede desculpas.
- **RN27:** restrições do perfil filtram as receitas. O sistema informa quantas ficaram de fora e por qual restrição, e a pessoa pode vê-las mesmo assim, com o ingrediente restrito destacado.
- **RN28:** uma receita pode faltar até 2 ingredientes, ou ter os que faltam substituíveis por outros disponíveis. A sugestão diz o que falta e quais substituições foram consideradas. Receitas completas vêm primeiro.
- **RN29:** os ingredientes que faltam vão para a lista de compras com uma única ação.

Específica desta funcionalidade: a correspondência entre os ingredientes disponíveis e os ingredientes da receita é feita pelo `Alimento` de cada um, por função determinística. O LLM interpreta a pergunta e redige a resposta, mas não decide se uma receita serve (RN01).

## Entradas e saídas

- **Entrada:**
  - pergunta em texto;
  - ingredientes informados pela pessoa (opcional);
  - pedido para usar as notas recentes (opcional);
  - pedido para usar só os itens informados (opcional);
  - pedido para mostrar receitas ocultadas por restrição (opcional);
  - restrições do perfil, lidas da conta da pessoa.
- **Saída:**
  - resposta em texto;
  - receitas sugeridas, cada uma com título, fonte com link, ingredientes que faltam e substituições consideradas;
  - quantidade de receitas ocultadas e a restrição que as ocultou;
  - fontes citadas (título, instituição ou site, ano);
  - indicação de que a base não tinha a informação;
  - quando houver busca de receitas, a confirmação de que ela começou e, depois, a notificação de que terminou.

O formato exato da API é definido em #33 e #24.

## Fora do escopo

- Preços e comparação entre mercados (contexto Preços).
- Montagem e ajuste da lista de compras (contexto Planejamento). Esta spec só envia os ingredientes que faltam.
- Leitura das notas fiscais (contexto Leitura de documentos). Esta spec só usa itens de notas já revisadas.
- Despensa salva e priorização por validade dos alimentos (cortadas pela equipe).
- Informação nutricional e calorias pela TACO (fora do MVP, ver o modelo de domínio).

## Pontos em aberto

Estão na seção "Receitas: a definir" do [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md):

- quais ingredientes básicos (sal, água, óleo) contam como sempre disponíveis;
- de onde vêm as substituições da RN28;
- quantos dias contam como "notas recentes".

## Versão 1 (entrega da semana 2)

O que entra na primeira versão (épico #15, sub-issues #16 a #21):

- Base de conhecimento curada: receitas do afrodite.json e de uma amostra do RecipeNLG, o Guia Alimentar para a População Brasileira (Ministério da Saúde, 2014) e textos de conservação e aproveitamento, todos listados em `data/base-conhecimento/FONTES.md`.
- Divisão em trechos: uma receita é um trecho; os textos de orientação são divididos por seção e por parágrafo.
- Embeddings comparados entre dois modelos, gravados no Qdrant.
- Recuperação dos trechos mais parecidos com a pergunta, com limiar de similaridade: abaixo dele, a resposta diz que não encontrou (RN11).
- Resposta redigida pelo LLM só com os trechos recuperados, com as fontes montadas pelo código a partir dos trechos usados (RN10).
- Pergunta sobre preço atual respondida com o aviso da RN04.
- Entre receitas com similaridade quase igual, vem primeiro a que tem menos ingredientes faltando. O LLM só interpreta os ingredientes da pergunta, e a contagem é determinística (RN01).
- Demonstração pela linha de comando e por um notebook. O endpoint da API fica para a #24.

Fica para depois: a correspondência completa por `Alimento` e as substituições (RN28), as restrições do perfil (RN27), as notas recentes (RN21), a lista de compras (RN29) e a busca sob demanda (RN26).

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- Escolhas técnicas do RAG (#13).
- Documentos da base de conhecimento (#16, #17): aproveitamento e conservação, Guia Alimentar e consumo. O `FONTES.md` ainda não lista nenhum.
- Base inicial de receitas a partir do afrodite.json e de uma amostra do RecipeNLG (seção "Fonte de receitas" do modelo de domínio), e conjunto de perguntas com gabarito para avaliação (#23).
- Catálogo de alimentos (`Alimento`), compartilhado com Preços e Planejamento.
- Esqueleto da aplicação (#35).
- RN21 depende da leitura de notas fiscais (Recibaldo). RN29 depende da lista de compras (Planejamento). RN26 depende de um meio de notificar a pessoa (Conversa).

## Riscos e limitações

- **Fonte de receitas:** o afrodite.json não declara licença nem o site de origem, e as receitas dele não têm link, então a citação aponta o dataset. O RecipeNLG está em inglês e é de uso não comercial. Ver a seção "Fonte de receitas" do modelo de domínio.
- A qualidade das respostas depende da cobertura da base de conhecimento e da base de receitas.
- A recuperação pode trazer trechos parecidos, mas de outro alimento. O Recall@k é medido no conjunto de perguntas com gabarito (#23).
- A busca de receitas sob demanda (RN26) está **a definir**: com datasets estáticos, não há onde buscar receitas novas. Enquanto isso, vale a RN11.
- Ver receitas ocultadas por restrição é escolha da pessoa. O sistema destaca o ingrediente restrito, mas não substitui orientação médica ou de nutricionista.
