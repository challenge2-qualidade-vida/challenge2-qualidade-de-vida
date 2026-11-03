# Tópico 23 — Layout responsivo

**Status:** ✅ concluído em 03/11/2026

O site era uma coluna de celular de 520 px, centralizada mesmo em telas grandes. Agora o layout acompanha a largura da tela, só com CSS, sem biblioteca.

| Largura | Layout |
|---------|--------|
| Até 359 px | Celular pequeno: ações e resumos em uma coluna, sem a pílula do LLM no topo |
| 360 a 719 px | Celular: como antes, com a navegação embaixo |
| 720 a 1023 px | Tablet: até 880 px de largura, personagens em 4 colunas, resumo em 3 e cardápio em duas colunas |
| A partir de 880 px | As 4 ações ficam na mesma linha |
| 1024 a 1279 px | Computador: navegação na lateral, formulário da cesta fixo à esquerda e resultado à direita |
| A partir de 1280 px | Metas e explicação lado a lado, e resumo em 3 colunas |

Regras em [estilo.css](../../src/web/estilo.css), na seção "Telas maiores".

## Como foi testado

Um script no navegador abriu o site em janelas internas de 320, 360, 390, 720, 768, 880, 1024, 1279 e 1440 px. Em cada largura, montou a cesta e o cardápio, percorreu Início, Cesta, Perto, Mia, Cupom, Configurações e Preços e procurou qualquer elemento fora da tela.

**Resultado:** sem rolagem horizontal da página nas 9 larguras. A primeira rodada achou estouros a 320 px e a 1024 px, que foram corrigidos. Tabelas e sugestões do chat no celular rolam de lado de propósito, dentro do próprio bloco.

## Limitações

- O teste usou janelas internas no Chrome do computador, não aparelhos reais. Vale conferir em um celular e em um tablet.
- A largura mede só o que passa da tela: sobreposições e aparência foram conferidas a olho, em capturas de 768 e 1440 px.
- Uma extensão de modo escuro no navegador pode mudar as cores do site. Para ver as cores reais, desligue-a para este endereço.
