# Tópico 4 — API (backend)

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

Uma API HTTP com **FastAPI** que expõe o otimizador e a comparação para o site. O mesmo servidor também entrega os arquivos do site (tópico 5), então basta **um comando** para rodar tudo.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/api.py](../../src/economia/api.py) | Endpoints e validação da entrada |
| [tests/test_api.py](../../tests/test_api.py) | 9 testes |

## Como rodar

```bash
source .venv/bin/activate
uvicorn economia.api:app --app-dir src --reload
```

- API: <http://localhost:8000/api/saude>
- **Documentação interativa (Swagger):** <http://localhost:8000/docs>. O FastAPI gera essa página sozinho, e dá para testar cada endpoint pelo navegador.

`--app-dir src` diz ao Uvicorn onde está o pacote `economia`. `--reload` reinicia o servidor quando um arquivo muda (só para desenvolvimento).

## Endpoints

| Método | Caminho | Para quê |
|--------|---------|----------|
| GET | `/api/saude` | Verifica se o servidor está no ar |
| GET | `/api/opcoes` | Mercados, restrições e períodos para montar o formulário |
| GET | `/api/precos` | Tabela de preços por produto e mercado, com preço por kg, data e fonte |
| POST | `/api/cesta` | Monta o plano: cesta recomendada, 1 × 2 mercados e explicação |

### `POST /api/cesta`

**Entrada:**

```json
{
  "orcamento": 800,
  "pessoas": 4,
  "periodo": "mes",
  "restricoes": ["sem_porco"],
  "custo_deslocamento": 10
}
```

| Campo | Regra |
|-------|-------|
| `orcamento` | opcional, maior que 0 (vazio = sem limite) |
| `pessoas` | obrigatório, de 1 a 20 |
| `periodo` | `semana`, `quinzena` ou `mes` |
| `restricoes` | lista com `sem_porco`, `sem_carne_vermelha`, `vegetariano`, `sem_lactose`, `sem_gluten`, `sem_ovo` |
| `custo_deslocamento` | opcional, ≥ 0 |

Entrada inválida devolve **HTTP 422** com a mensagem do erro, sem chegar ao otimizador.

**Saída** (resposta real para a entrada acima, resumida):

```json
{
  "recomendacao": "dois",
  "cesta_recomendada": {
    "mercados": ["B", "C"],
    "custo_total": 602.66,
    "custo_por_mercado": {"B": 332.68, "C": 269.98},
    "itens": [{"produto_id": "acucar-1kg", "produto": "Açúcar cristal — 1 kg", "alimento": "Açúcar cristal",
               "grupo": "acucar", "mercado_id": "B", "mercado": "Mercado B", "quantidade": 1,
               "preco_unitario": 4.79, "subtotal": 4.79, "preco_kg": 4.79,
               "data_preco": "2026-10-20", "fonte_preco": "exemplo"}, "..."],
    "obtido": {"kcal": 240268.6, "proteina_g": 6244.0, "fibra_g": 4475.0, "flv_g": 48000.0},
    "metas":  {"kcal": 240000,   "proteina_g": 6000,   "fibra_g": 3000,   "flv_g": 48000},
    "custo_por_1000_kcal": 2.51,
    "custo_por_g_proteina": 0.097
  },
  "um_mercado": {"...": "mesma estrutura"},
  "dois_mercados": {"...": "mesma estrutura"},
  "economia_bruta_dois": 29.06,
  "economia_liquida_dois": 19.06,
  "custo_por_mercado": {"A": 664.16, "B": 639.15, "C": 631.72},
  "minimo_necessario": null,
  "explicacao": ["Cesta para 4 pessoas por 1 mês.", "..."],
  "aviso_dados": "DADOS DE EXEMPLO. ..."
}
```

Quando o orçamento não dá, `recomendacao` e as cestas vêm `null` e `minimo_necessario` traz quanto seria preciso.

## Como funciona por dentro

1. Ao iniciar, a API carrega as bases **uma vez** (`base = carregar()`).
2. O **Pydantic** (que vem com o FastAPI) valida o corpo do pedido pelo modelo `PedidoCesta`.
3. `montar_resposta()` converte para o `Pedido` do otimizador, chama `planejar()` e `explicar()` e transforma as `dataclass` em JSON com `asdict`.
4. Por último, `app.mount("/", StaticFiles(...))` serve a pasta `src/web/` como site. Ela fica por último para não "engolir" as rotas `/api/...`.

## Testes

```bash
pytest tests/test_api.py -v
```

Usam o `TestClient` do FastAPI, que chama a API sem subir servidor. Conferem: saúde; opções com os 3 mercados e as restrições; preço por kg na tabela; plano completo dentro do orçamento e com explicação; orçamento insuficiente com o mínimo necessário; e 4 casos de entrada inválida (0 pessoas, período inexistente, orçamento negativo, restrição desconhecida) devolvendo 422.

**Resultado em 29/10/2026:** 37 testes passando no projeto. Aparece um aviso de depreciação do Starlette sobre o `httpx` no cliente de testes; não afeta o app.
