# Tópico 18 — Cardápio seguro a partir da cesta

**Status:** ✅ concluído em 03/11/2026

## O problema encontrado

Ao testar o app de ponta a ponta, o cardápio feito pelo LLM sugeriu **"Jantar: Feijão carioca cru"** e usou repolho e tomate, que não estavam na cesta. A Mia não percebeu, porque só conferia valores, fontes e restrições. É o risco de alucinação descrito no README, num ponto que pode prejudicar a saúde: feijão cru não deve ser consumido.

## A decisão

O cardápio segue o mesmo princípio dos preços: **quem decide é o código, não o LLM**.

| Antes | Agora |
|-------|-------|
| O LLM escrevia o cardápio livremente | Cada refeição vem de uma receita cadastrada |
| Podia citar alimento fora da cesta | Só entra receita cujos ingredientes obrigatórios estão na cesta |
| 15 a 20 s com o LLM local | Cerca de 0,2 s no site, com ou sem LLM |
| Só texto | Cartões por dia e por refeição, com foto, ingredientes e preparo |

Também testamos manter o LLM só para um comentário sobre o cardápio. Ele levava 17 s e dizia frases sem utilidade, como "basta trocar a ordem dos alimentos". Por isso foi retirado. O LLM continua no chat, onde entende pedidos em linguagem natural.

## Como funciona

- [data/receitas/receitas.json](../../data/receitas/receitas.json): receitas de café da manhã, almoço e jantar. Cada ingrediente aponta para um alimento da base. O campo `requer` lista as vagas obrigatórias (basta ter uma das opções) e `opcional` entra só se estiver na cesta.
- [src/economia/cardapio.py](../../src/economia/cardapio.py): `montar_cardapio` escolhe as refeições. Evita repetir prato, prioriza alimentos ainda não usados e usa primeiro o que estraga mais rápido (`uso_em_dias`).
- A **Mia** confere o texto final com `problemas_cardapio`: não pode citar alimento cru nem alimento fora da cesta.
- `POST /api/cardapio` recebe `alimentos` (ids ou nomes), `restricoes` e `dias` (1 a 7; padrão 3). A tela oferece 3 ou 7 dias.

No chat, o prompt do Miau-ricio agora avisa que os valores da TACO citam alimentos crus só para medir nutrientes, e que nunca se deve sugerir comê-los assim.

## Outra correção: arquivo antigo no navegador

No teste, o Chrome continuou usando o `app.js` antigo depois da atualização, porque o servidor não dizia por quanto tempo guardar o arquivo. Agora o site responde com `Cache-Control: no-cache`: o navegador pode guardar, mas confere antes se o arquivo mudou.

## Como foi testado

- `tests/test_cardapio.py`: toda cesta gerada pelo otimizador (5 perfis de restrição × 2 tamanhos) precisa ter almoço e jantar nos 7 dias, sem alimento fora da cesta. A Mia confere cada texto.
- Cada receita é testada com a combinação mínima de ingredientes. Esse teste revelou nomes enganosos (ex.: "Macarrão com feijão" feito com lentilha), que foram corrigidos.
- No navegador: cesta de R$ 800 para 4 pessoas → cardápio de 3 dias em 203 ms, sem erros no console.

## Limitações

- As receitas foram escritas para este projeto e precisam da revisão do grupo.
- Cestas sem pão, aveia ou leite podem repetir a fruta no café da manhã, porque o otimizador não planeja cada refeição.
- O cardápio não confere se a quantidade comprada rende todas as porções. O otimizador garante as metas da cesta inteira, não de cada refeição.
