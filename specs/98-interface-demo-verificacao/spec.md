# Spec: interface da demo da verificação de alegações

| Campo | Valor |
| --- | --- |
| Issue | #98 (Refs #72) |
| Status | Em revisão |
| Contexto delimitado | Verificação |
| Agente | Research, Analysis, Validation e Communication (fluxo da #82) |

## Problema

A entrega da semana 4 pede a **demonstração de um fluxo completo**, com os agentes colaborando. O fluxo (Research → Analysis → Validation → Communication, com o retorno do Validation) roda no backend, mas não há onde ver uma alegação entrar, o que cada agente fez e o veredito sair. O roteiro da demo (prints da interface) e a avaliação dependem dessa tela.

## Comportamento esperado

Uma tela **Verificar** no frontend da `develop_gui` (decisão do Pedro Lucas, 24/11/2026):

1. A pessoa escreve uma alegação sobre alimentação e escolhe o perfil de leitura: **Explicação completa** (`consumidor_geral`) ou **Resposta rápida** (`consumidor_rapido`).
2. A tela chama `POST /api/v1/verificacoes` (rota da #82) e mostra:
   - **o veredito:** classificação (reciclada, parcial ou nova), mensagem, fontes e se foi aprovado pela validação;
   - **o caminho dos agentes:** cada passo do `historico`, na ordem, com o agente, o tempo e um resumo da saída. Um retorno do Validation aparece como uma volta ao Research ou ao Analysis, com os motivos.
3. Quando a verificação não foi conclusiva (`aprovado_pela_validacao` falso), o veredito traz o aviso em destaque.
4. Erros da API aparecem como Problem Details, com a mensagem da API.

A tela fica atrás da flag **`verificacao`**. Ela não entra em `VITE_FUNCIONALIDADES=todas`, porque a comparação visual com o site antigo usa `todas` e o site antigo não tem essa tela. Para a demo: `npm run dev:demo`.

## Termos do domínio

Do [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md), propostos na #72 (épico da semana 4): alegação (`Alegacao`), evidência recuperada (`EvidenciaRecuperada`), classificação da alegação (`ClassificacaoDaAlegacao`), análise da alegação (`AnaliseDaAlegacao`), resultado da validação (`ResultadoDaValidacao`), veredito (`Veredito`) e perfil de leitura (`PerfilDeLeitura`).

## Regras de negócio

- **RN01:** a tela não calcula nada. Classificação, confiança, scores e aprovação vêm da API; a tela só formata.
- **RN10:** as fontes mostradas são as do `Veredito`, montadas pelo código do backend.
- **RN11:** veredito não aprovado aparece como "verificação não conclusiva", sem esconder o aviso.
- A classificação mede o quanto a base cobre a alegação. A tela não usa as palavras "verdadeiro" nem "falso".

## Entradas e saídas

Contrato provisório em `frontend/openapi/provisorio.yaml`, conferido com a rota do PR #88 (#82) em 26/11/2026. O Research devolve só os ids dos trechos e os scores, sem o texto, e a mensagem fica só no `veredito`. A alegação tem de 1 a 500 caracteres (422 fora disso):

`POST /verificacoes` com `{"alegacao": "...", "perfil": "consumidor_geral"}` → `ResultadoDaVerificacao`:

```json
{
  "veredito": {
    "classificacao": "parcial",
    "mensagem": "...",
    "fontes": [{ "titulo": "Guia Alimentar para a População Brasileira", "instituicao": "Ministério da Saúde", "ano": 2014, "url": null }],
    "aprovado_pela_validacao": true
  },
  "retornos": 0,
  "historico": [
    { "agente": "research", "entrada": { "limite": 5 }, "saida": { "evidencias": [{ "trecho": "id", "score": 0.86 }] }, "segundos": 0.8 },
    { "agente": "analysis", "entrada": { "motivos": [] }, "saida": { "classificacao": "parcial", "justificativa": "...", "citacoes": [], "confianca": 0.87 }, "segundos": 4.1 },
    { "agente": "validation", "entrada": {}, "saida": { "aprovado": true, "motivos": [], "retornar_para": null }, "segundos": 2.3 },
    { "agente": "communication", "entrada": { "perfil": "consumidor_geral" }, "saida": { "classificacao": "parcial", "aprovado_pela_validacao": true }, "segundos": 1.9 }
  ]
}
```

Com `VITE_DADOS_FALSOS=1`, os dados falsos devolvem dois exemplos fictícios: um aprovado direto e um com retorno ao Research (quando a alegação fala de "cura"). O perfil rápido devolve a mensagem curta.

## Fora do escopo

- O orquestrador e a rota de verdade (#82, Pedro Lucas).
- Juntar este frontend com a tela do Miau-ricio da `main`.
- Guardar o histórico de verificações.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature), cobertos pelos testes do Vitest em `frontend/src/testes/verificacao.teste.ts`.

## Dependências

- **#82:** a rota `POST /api/v1/verificacoes` e o formato do `historico`. Até ela existir, a tela usa os dados falsos.
- **#83:** o `Veredito` do Communication Agent.

## Riscos e limitações

- O formato de `historico[].saida` segue o PR #88, ainda em revisão. A tela lê só esses campos e ignora o resto; se o formato mudar no merge, muda só o resumo de cada passo (`src/util/verificacao.ts`).
- Os exemplos dos dados falsos são fictícios e servem só para a demo e os prints.
