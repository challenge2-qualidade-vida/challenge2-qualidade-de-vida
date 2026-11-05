# Frontend da EconoMIA (React + Vite + TypeScript)

Recriação do site de `src/web/` com o **visual idêntico** e por dentro do jeito do grupo. A referência é o commit `e149814` da `develop_gui`. As regras da pasta estão em [AGENTS.md](AGENTS.md), e a spec em [specs/sem-issue-frontend-react](../specs/sem-issue-frontend-react/spec.md).

## Onde ficou o protótipo

Em 05/11/2026 a `develop_gui` foi alinhada com a `main`: ficou igual a ela, mais esta pasta e a spec. O protótipo antigo (site de `src/web/`, backend em módulos soltos, testes, experimentos e a documentação passo a passo em `docs/desenvolvimento/`) saiu da branch porque não segue a arquitetura nem o processo do grupo. Ele continua no histórico, no commit `16438ea` (tag local `prototipo-develop-gui`), e serve de consulta para as specs. Para abri-lo ao lado, sem mexer na branch:

```bash
git worktree add ../economia-prototipo 16438ea
```

## Rodar

```bash
cd frontend
npm install
npm run dev:falso    # http://localhost:5173, com dados falsos e todas as funcionalidades
```

Com os dados falsos, qualquer e-mail e senha entram (por exemplo `teste@exemplo.test` e `senha-de-teste`). Nada é enviado a um servidor.

Para usar a API de verdade, rode o backend em `localhost:8001` e `npm run dev`. O Vite repassa `/api/v1` para ele (`vite.config.ts`).

| Variável | Para quê |
| --- | --- |
| `VITE_DADOS_FALSOS=1` | Usa os dados falsos tipados (`src/api/dados-falsos`) em vez da API |
| `VITE_FUNCIONALIDADES` | `todas` ou lista separada por vírgula. Vazio = só o MVP |

## Funcionalidades fora do MVP (flags desligadas por padrão)

| Flag | O que aparece com ela | Funcionalidade do escopo |
| --- | --- | --- |
| `promocao` | Atalho "Essa promoção vale?" no Início e a sugestão da promoção na conversa | F6 |
| `deslocamento` | "Mais opções" com o custo do 2º mercado na Cesta, o custo por km nas Configurações e o texto "+ R$ de deslocamento" | F7 |
| `nutricao` | Anéis de Energia, Proteína, Fibra e Frutas no Início e o cartão "Metas nutricionais" na Cesta | F14 |
| `perto` | Tela Perto de mim, atalho "Achar ofertas perto de mim", aba Perto, e raio, ponto de partida e ordenação nas Configurações | F5 bloqueado, F7 |
| `precos` | Tela Tabela de preços e o botão "Ver tabela de preços" | F8 |

"O que já tenho em casa" continua ligado: os ingredientes valem só para aquele pedido (RN13).

## Contratos que faltam combinar com o backend

O contrato provisório é [`openapi/provisorio.yaml`](openapi/provisorio.yaml). Todos os valores em dinheiro estão em centavos.

| Rota provisória | Situação no contrato do grupo (`fluxos-e-contratos.md`) |
| --- | --- |
| `POST /auth/cadastro`, `/auth/login`, `/auth/renovar`, `/auth/sair` | Rotas previstas; faltam os campos, o nome e as regras do cookie de renovação (`httpOnly`, `SameSite`, caminho) e se o cadastro já abre a sessão |
| `GET /opcoes`, `/creditos`, `/configuracoes`, `/regioes`, `/llm` | Não previstas. Dados de referência das telas |
| `GET /precos` | Não prevista; a tabela é fora do MVP |
| `POST /cestas`, `GET /cestas/ultima` | O grupo prevê `PlanoDeCompras` e `ListaDeCompras` em `/listas`. A tela usa a cesta otimizada com 1 ou 2 mercados e metas |
| `POST /cardapios` | Não prevista; o grupo prevê receitas pelo Miau-ricio com RAG, pela conversa |
| `GET /mercados/proximos`, `/mercados/mapa` | Não previstas; fora do MVP |
| `POST /notas`, `POST /notas/revisao` | O grupo prevê leitura assíncrona (`202` e notificação), `GET /notas/{id}`, `POST /notas/{id}/revisao` e o termo de consentimento (`POST /consentimento`), que ainda não têm tela |
| `POST /conversas`, `POST /conversas/{id}/mensagens` (SSE) | Previstas. Falta o conteúdo do evento `blocos`; o provisório usa `agentes`, `ferramentas_usadas`, `fontes`, `aviso` e `dados` |
| `GET /notificacoes`, `POST /notificacoes/{id}/lida` | Previstas; faltam os campos e os tipos de notificação |

## Testes

```bash
npm run verificar                                         # tipos
npm run teste                                             # unidade (Vitest)
npx playwright test --project=antigo --update-snapshots   # referência: site antigo em :8000 (rodar o protótipo do commit 16438ea)
npx playwright test --project=novo                        # compara o novo (:5173, com npm run dev:falso)
```

As capturas de referência (`testes/visual/capturas/`, cerca de 12 MB) não vão para o git: são geradas do site antigo a cada comparação.

## Dívidas conhecidas

- `src/efeitos/cena3d.ts` está com `// @ts-nocheck`: a cena foi portada sem mudar o efeito, e falta tipar os objetos do Three.js.
- Os textos de Configurações ainda dizem que "a EconoMIA não tem login" e que os dados ficam "só neste aparelho". Foram mantidos porque o visual precisava ficar idêntico.
- Os dados falsos não calculam: qualquer pedido de cesta devolve a cesta gravada.
