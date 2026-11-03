# Tópico 20 — App instalável, última cesta e proteção contra abuso

**Status:** ✅ concluído em 03/11/2026

| O que | Como | Arquivo |
|-------|------|---------|
| **Instalar no celular (PWA)** | Manifesto e ícones; o navegador oferece "Adicionar à tela inicial" (exige HTTPS fora do `localhost`) | [manifest.webmanifest](../../src/web/manifest.webmanifest) |
| **Abrir sem internet** | Service worker: sempre tenta a rede primeiro e só usa a cópia guardada se não houver conexão | [sw.js](../../src/web/sw.js) |
| **Última cesta** | Guardada no `localStorage`; o Início continua preenchido ao reabrir. Depois de um dia, a Mia avisa que os preços podem ter mudado | [app.js](../../src/web/app.js) |
| **Apagar meus dados** | Botão nas Configurações limpa tudo o que o app guardou no aparelho | [index.html](../../src/web/index.html) |
| **Limite por IP** | 20 mensagens de chat, 40 cestas, 10 consultas ao mapa e 10 envios de cupom por minuto, para cada rota; acima disso, erro 429 com mensagem em português | [limites.py](../../src/economia/limites.py) |
| **Testes automáticos no GitHub** | Roda o `pytest` a cada envio, de graça | [testes.yml](../../.github/workflows/testes.yml) |

## Privacidade (LGPD)

- O cache do service worker só guarda os arquivos do site e as rotas públicas `/api/opcoes`, `/api/precos` e `/api/creditos`. **Posição, chat e cestas nunca entram nele.**
- A última cesta fica só no aparelho, nunca no servidor.
- O limite por IP fica em memória: nada é gravado em disco.

## Correções feitas junto

- Se não houver cesta possível sem orçamento informado, a mensagem não mostra mais "Com R$ NaN".
- Sem solução, o bloco de cardápio some, em vez de continuar mostrando a cesta anterior.

## Como foi testado

No navegador: service worker ativo, cache sem rotas pessoais e cesta de R$ 345,86 restaurada depois de recarregar, com a tela no topo do Início. No servidor real: 20 mensagens aceitas e a 21ª recusada com 429.

## Limitações

- **Sem internet**, o app abre e mostra a última cesta e os preços vistos por último, mas montar cesta e conversar exigem conexão.
- O limite fica em memória: zera se o servidor reiniciar e vale por processo. Para o tamanho do projeto, basta.
- O funcionamento sem internet foi conferido pelo conteúdo do cache, sem desligar a rede na prática. Vale testar uma vez no celular depois de publicar.
- O workflow do GitHub só roda depois do próximo envio (`git push`).
