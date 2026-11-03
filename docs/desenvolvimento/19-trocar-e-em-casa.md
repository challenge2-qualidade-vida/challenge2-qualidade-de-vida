# Tópico 19 — Trocar item e "o que tenho em casa"

**Status:** ✅ concluído em 03/11/2026

São dois diferenciais do README, feitos pelo otimizador, sem LLM. Assim, a resposta continua calculada e cumprindo as metas.

## Trocar um item

Cada item da lista tem o botão **🔄 Trocar**. O app refaz a cesta sem aquele alimento, e o otimizador escolhe a opção mais barata que ainda cumpre todas as metas. O alimento fica em **Fora desta cesta**, e tocar nele o devolve.

## O que tenho em casa

Em **🏠 O que já tenho em casa**, a pessoa informa o alimento e os quilos. O otimizador:

- desconta esses nutrientes das metas, inclusive frutas e hortaliças e a meta de proteína animal;
- não cobra nada por eles;
- ignora o que não respeita as restrições escolhidas (frango em casa não conta numa cesta vegetariana);
- calcula o custo por 1.000 kcal só sobre o que foi comprado.

Os alimentos de casa também entram no cardápio. Se o que há em casa já cumprir as metas, o app avisa que não é preciso comprar nada.

## API

`POST /api/cesta` ganhou dois campos opcionais:

```json
{ "pessoas": 4, "sem_alimentos": ["feijao_carioca"], "em_casa": [{ "alimento": "arroz", "gramas": 5000 }] }
```

Alimento que não existe na base devolve erro 422. `GET /api/opcoes` agora lista os alimentos.

## Resultado no navegador (preços de exemplo, 4 pessoas, 1 mês, R$ 800)

| Ação | Custo da cesta |
|------|---------------|
| Cesta original | R$ 670,92 |
| Trocar o feijão carioca | R$ 674,42 |
| Trocar o feijão e informar 5 kg de arroz em casa | R$ 633,97 |

## Limitações

- O que está em casa é informado a cada uso e não é conferido.
- Os limites de variedade valem para o que é comprado, sem somar o que há em casa.
- O **histórico de preços** continua de fora: só faz sentido com coletas reais ao longo do tempo, como o próprio README alerta.
