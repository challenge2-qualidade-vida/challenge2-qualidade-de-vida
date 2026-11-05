# Frontend da EconoMIA: regras da pasta

Vale para pessoas e assistentes de IA que mexem em `frontend/`. As regras gerais estão no `AGENTS.md` da raiz da `main`.

## O que é

App React + Vite + TypeScript que consome a API do grupo sob `/api/v1`. Recria o site aprovado de `src/web/` com o **visual idêntico**. A referência é o commit `e149814` da `develop_gui`.

## Termos

Use os termos do [modelo de domínio](../docs/arquitetura/modelo-de-dominio.md) (na `main`) nos nomes de componentes, tipos e variáveis, em português e sem acentos:

| Na tela | No código |
| --- | --- |
| Orçamento | `orcamento` |
| Período | `periodo` |
| Restrição | `restricao` |
| Mercado | `Estabelecimento` (tipo da API) |
| Preço, preço por kg | `preco`, `preco_kg` |
| O que tenho em casa | `ingredientesDisponiveis` (valem só para o pedido, RN13) |
| Nota fiscal, item lido | `NotaFiscal`, `ItemExtraido` |
| Conversa, pedido | `Conversa`, `Pedido` |
| Notificação | `Notificacao` |

"Cesta" e "metas nutricionais" vêm do protótipo e ainda não estão no modelo de domínio.

## Regras

- **Visual:** não mude cores, textos, espaçamentos nem animações. O CSS é o original, em `src/estilos/estilo.css`. Mudança de visual só com pedido do Guilherme.
- **API:** só pelo cliente gerado (`src/api/cliente.ts`). Nada de `fetch` escrito à mão para a API. A única exceção é a leitura do stream SSE da conversa, em `src/api/sse.ts`, porque o openapi-fetch não lê streams.
- **Contrato:** os tipos vêm de `openapi/provisorio.yaml` (`npm run tipos-api`). Não edite `src/api/esquema.d.ts` à mão.
- **Erros:** toda resposta de erro é Problem Details. Use `ProblemaDaApi` e `mensagemDoProblema` (`src/api/problemas.ts`).
- **Dinheiro:** a API manda centavos (inteiro). Formate só na tela, com `reais()` de `src/util/formato.ts`. O frontend não calcula preço nem soma de compra (RN01).
- **Dados no aparelho:** só conveniência leve, como as configurações de busca. Nada de dado pessoal ou sensível no `localStorage`. O token de acesso fica só na memória.
- **Funcionalidades fora do MVP:** atrás de `funcionalidadeLigada()` (`src/funcionalidades.ts`), desligadas por padrão.
- **Efeitos:** a cena 3D, os gatos vivos e as animações ficam em `src/efeitos/`. Eles leem o DOM pelos mesmos ids e classes do site antigo, então não troque ids nem classes.

## Limites

- `src/telas/` pode importar `componentes/`, `estado/`, `api/`, `util/` e `efeitos/`.
- `src/componentes/` não importa `telas/`.
- `src/api/` não importa nada de React.

## Comandos

```bash
npm install
npm run dev:falso       # dados falsos e todas as funcionalidades ligadas
npm run verificar       # checagem de tipos
npm run teste           # testes de unidade (Vitest)
npm run teste:visual    # comparação visual com o site antigo (Playwright)
```
