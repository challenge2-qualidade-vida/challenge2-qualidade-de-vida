# Spec: perguntas sobre receitas e alimentação (RAG)

| Campo | Valor |
| --- | --- |
| Issue | #15 (épico), implementação em #16 a #24 |
| Status | Rascunho |
| Contexto delimitado | Receitas e nutrição |
| Agente | Miau-ricio |

## Problema

Comprar alimentos sem pensar nas refeições leva a desperdício e a gastos desnecessários. A pessoa não sabe o que cozinhar com o que já tem em casa nem como aproveitar sobras e alimentos perto do vencimento.

## Comportamento esperado

A pessoa faz uma pergunta em linguagem natural sobre receitas, alimentação saudável ou aproveitamento de alimentos. O sistema busca trechos relevantes na base de conhecimento e responde com base neles, citando as fontes. Perguntas sobre calorias e nutrientes são respondidas com a tabela TACO.

## Termos do domínio

`Receita`, `Ingrediente`, `Despensa`, `InformacaoNutricional`, `Fonte`, `Trecho`.

## Regras de negócio

- **RN04:** a base de receitas não é fonte de preço atual.
- **RN10:** respostas citam a fonte.
- **RN11:** sem informação na base, a resposta diz que não encontrou.
- **RN12:** calorias e nutrientes vêm da tabela TACO.
- **RN13:** receitas priorizam ingredientes da despensa informada.

## Entradas e saídas

- **Entrada:** pergunta em texto e, opcionalmente, a lista de ingredientes da despensa.
- **Saída:** resposta em texto, lista de fontes citadas (título, instituição, ano) e indicação de quando a base não tinha a informação.

O formato exato da API é definido em #33 e #24.

## Fora do escopo

- Preços e comparação entre mercados (contexto Preços).
- Planejamento da lista de compras (contexto Planejamento).
- Leitura de imagens.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- Escolhas técnicas do RAG (#13).
- Documentos da base de conhecimento (#16, #17) e tabela TACO (#22).
- Esqueleto da aplicação (#35).

## Riscos e limitações

- A qualidade das respostas depende da cobertura da base de conhecimento.
- A recuperação pode trazer trechos parecidos, mas de outro alimento. O Recall@k é medido no conjunto de perguntas de teste (#23).
- O sistema não substitui orientação de nutricionista.
