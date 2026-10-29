# Tópico 3 — Comparação entre mercados e explicação

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

Responde à pergunta *"compensa ir a dois mercados?"* e explica a escolha em frases simples.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/planejador.py](../../src/economia/planejador.py) | `planejar()`: compara 1 mercado × 2 mercados e decide |
| [src/economia/explicacao.py](../../src/economia/explicacao.py) | `explicar()`: transforma o plano em frases; formata R$ e datas |
| [tests/test_planejador.py](../../tests/test_planejador.py) | 8 testes |

## Como funciona

`planejar(base, pedido, custo_deslocamento)` usa o otimizador do tópico 2 várias vezes:

1. **Um mercado:** monta a cesta em cada mercado sozinho (A, B, C) e fica com a mais barata.
2. **Dois mercados:** monta a cesta para cada par (A+B, A+C, B+C). Só conta a solução que usa **de fato** os dois mercados. Se a melhor solução do par compra tudo num só lugar, ela é igual ao caso de um mercado.
3. **Decisão:** recomenda dois mercados só se `custo em 2 mercados + deslocamento < custo em 1 mercado`. O custo de deslocamento (passagem, gasolina, tempo) é informado pelo usuário.
4. **Sem solução:** se o orçamento não permite cumprir as metas em nenhum caso, roda o otimizador sem o limite de orçamento e devolve o **mínimo necessário**: o menor custo entre um mercado só e dois mercados mais o deslocamento. Assim o usuário sabe quanto falta, em vez de receber só um "não dá".

**Ajustes feitos no tópico 11** (as métricas mostraram os problemas):

- Na opção de dois mercados, o **deslocamento sai do mesmo orçamento**. Antes, a comida cabia no orçamento, mas comida + deslocamento passava dele em 13% das cestas.
- O mínimo necessário era calculado juntando os 3 mercados sem deslocamento, e podia sair **menor** que o orçamento informado. Agora é o mínimo de verdade.

```
             ┌─ só A ─┐
pedido ──►   ├─ só B ─┼──► mais barata (1 mercado) ──┐
             └─ só C ─┘                              ├──► compara (+ deslocamento) ──► recomendação
             ┌─ A+B ──┐                              │
             ├─ A+C ──┼──► mais barata (2 mercados) ─┘
             └─ B+C ──┘
```

Com 3 mercados são 6 otimizações, que levam cerca de 0,35 s no total.

### Explicação sem LLM

`explicar()` gera as frases **direto dos números calculados**. Não há LLM nesta etapa, então não há como inventar um preço. Exemplo real (4 pessoas, 1 mês, R$ 800, R$ 10 de deslocamento), com as regras atuais:

> Cesta para 4 pessoas por 1 mês.
> A cesta mais barata em um só mercado é no Mercado C: R$ 708,31.
> Dividindo entre Mercado B e Mercado C, sai por R$ 670,92 (R$ 37,39 a menos). Com R$ 10,00 de deslocamento, a economia real é de R$ 27,39: compensa ir aos dois.
> Sobram R$ 119,08 do seu orçamento de R$ 800,00.
> A proteína vem principalmente de macarrão de trigo (26%) e feijão carioca (23%), as opções com menor custo por grama de proteína nos preços disponíveis.
> Custo por 1.000 kcal: R$ 2,79. Custo por grama de proteína: R$ 0,11.
> Preços de 20/10/2026 (fonte: exemplo). Atenção: são preços de exemplo, não preços reais.
> As metas consideram todas as pessoas como adultos (2.000 kcal por dia). É uma orientação para alimentação equilibrada da população geral e não substitui um nutricionista.

Cada frase atende a um ponto do README: **explicação da escolha**, **transparência de preço** (data e fonte), **métrica de custo por 1.000 kcal / por grama de proteína** e o aviso de que o app **não é dieta personalizada**.

No tópico 7, o LLM pode reescrever essas frases de forma mais conversada, mas os fatos continuam vindo daqui.

## Limitações conhecidas

- O custo de deslocamento é um valor único informado pelo usuário. Calcular pela distância real (mapa) fica para depois, se der tempo.
- Com muitos mercados, o número de pares cresce rápido (10 mercados = 45 pares). Para o MVP com 3 ou 4 mercados não é problema.

## Testes

```bash
pytest tests/test_planejador.py -v
```

Conferem que: a opção de um mercado é a mais barata entre os mercados; a de dois mercados usa dois mercados e nunca é mais cara; deslocamento alto leva a recomendar um mercado só; sem deslocamento, recomenda dois quando é mais barato; com orçamento insuficiente, informa o mínimo; a explicação cita o mercado, a sobra do orçamento, o aviso de preço de exemplo e o aviso de nutricionista; e a formatação de R$ e de datas.

**Resultado em 29/10/2026:** 28 testes passando no projeto.
