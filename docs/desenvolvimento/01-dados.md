# Tópico 1 — Base de dados

**Status:** ✅ concluído em 29/10/2026 (com dados de exemplo)

## O que foi feito

Duas bases em JSON, que o otimizador (tópico 2) vai usar, mais o código que as carrega e os testes que as validam.

| Arquivo | Conteúdo |
|---------|----------|
| [data/alimentos/alimentos.json](../../data/alimentos/alimentos.json) | 28 alimentos, com grupo, restrições (tags) e kcal, proteína e fibra por 100 g |
| [data/precos/precos.json](../../data/precos/precos.json) | 3 mercados, 31 produtos (embalagens) e 91 preços |
| [src/economia/dados.py](../../src/economia/dados.py) | Lê os JSON e devolve objetos Python; calcula o preço por kg |
| [tests/test_dados.py](../../tests/test_dados.py) | 6 testes de integridade |

> ⚠️ **Os preços e os mercados são fictícios.** Servem só para desenvolver e testar o app. Na semana 2, o grupo substitui pelos preços coletados em 3 ou 4 mercados de Brasília e pela cesta básica do DIEESE. Os valores nutricionais são **aproximados da Tabela TACO** e precisam ser conferidos na tabela original antes da entrega.

## Como os dados são organizados

Separamos **alimento** (o que a pessoa come) de **produto** (o que está na prateleira). Assim, "Arroz 1 kg" e "Arroz 5 kg" são dois produtos do mesmo alimento, e o app pode comparar o preço por kg das embalagens.

```
alimento  ──<  produto  ──<  preço  >──  mercado
 arroz         arroz-1kg      R$ 6,49     Mercado A
               arroz-5kg      R$ 27,90    Mercado A
```

### Alimento (`alimentos.json`)

```json
{
  "id": "feijao_carioca",
  "nome": "Feijão carioca (cru)",
  "grupo": "leguminosas",
  "tags": [],
  "por_100g": { "kcal": 329, "proteina_g": 20.0, "fibra_g": 18.4 }
}
```

- **grupo**: `cereais`, `tuberculos`, `leguminosas`, `proteina_animal`, `laticinios`, `flv` (frutas, legumes e verduras), `oleos`, `acucar`. O otimizador usa os grupos para garantir variedade (por exemplo, a meta mínima de frutas e hortaliças).
- **tags**: marcam restrições alimentares. O usuário escolhe uma restrição e o app remove os alimentos com a tag correspondente.

| Tag | Removida quando o usuário escolhe |
|-----|-----------------------------------|
| `carne_porco` | Sem carne de porco |
| `carne_vermelha` | Sem carne vermelha |
| `carne`, `peixe` | Vegetariano |
| `lactose` | Sem lactose |
| `gluten` | Sem glúten |
| `ovo` | Sem ovo |

### Produto e preço (`precos.json`)

```json
{ "id": "arroz-5kg", "alimento": "arroz", "nome": "Arroz tipo 1 — 5 kg", "embalagem_g": 5000 }
{ "produto": "arroz-5kg", "mercado": "A", "preco": 27.90, "data": "2026-10-20", "fonte": "exemplo" }
```

Todo preço tem **data** e **fonte**. É isso que permite ao app mostrar *"R$ 27,90 — Mercado A, 20/10"* (transparência de preço, ver o README principal). Quando a coleta real entrar, `fonte` passa a ser `coleta`, `dieese` ou `nfce`.

Nem todo produto existe em todo mercado: o feijão preto falta no Mercado C e a lentilha no Mercado B. Isso é proposital, para testar a comparação entre mercados no tópico 3.

## Como o código funciona

```python
from economia.dados import carregar, preco_por_kg

base = carregar()                      # lê os dois JSON
base.alimentos["arroz"].kcal           # 358
produto = base.produtos["arroz-5kg"]
preco = base.precos[0]
preco_por_kg(produto, preco)           # preço / embalagem_g × 1000
```

`carregar()` devolve um objeto `Base` com `alimentos`, `mercados`, `produtos`, `precos` e o `aviso` de dados de exemplo. Cada item é uma `dataclass` imutável, então nenhuma parte do app altera a base por acidente.

## Testes

```bash
pytest tests/test_dados.py -v
```

Os testes conferem que:

1. todo alimento tem grupo válido e nutrientes não negativos;
2. todo produto aponta para um alimento que existe;
3. todo preço aponta para produto e mercado existentes, é positivo e tem data e fonte;
4. não há dois preços para o mesmo produto no mesmo mercado;
5. todo produto tem preço em pelo menos um mercado;
6. o cálculo do preço por kg está correto.

**Resultado em 29/10/2026:** 6 testes passando.

**Quando editar os JSON** (por exemplo, ao lançar a coleta de preços), rode `pytest` de novo. Se algum teste falhar, a mensagem mostra qual item está errado.

## Como adicionar a coleta real de preços

1. Adicione o mercado em `mercados` (`id`, `nome`, `regiao`).
2. Se o produto não existir, adicione em `produtos` com o peso da embalagem em gramas.
3. Lance o preço em `precos` com a data da coleta e `"fonte": "coleta"`.
4. Remova os preços com `"fonte": "exemplo"` quando a coleta estiver completa.
5. Rode `pytest`.
