# Frontend do EconoMIA

React + Vite + TypeScript. Por enquanto, uma tela simples para perguntar ao Miau-ricio (RAG de receitas e alimentação) e ver a resposta com as fontes. Spec: [specs/24-endpoint-rag](../specs/24-endpoint-rag/spec.md).

## Rodar

Pré-requisitos: Node 18 ou mais novo, a API do EconoMIA e, por trás dela, o Qdrant (com a base indexada) e o Ollama.

1. Na raiz do projeto, suba a API:

   ```bash
   poetry run uvicorn economia.api.app:app --port 8000
   ```

2. Nesta pasta, instale as dependências e suba a tela:

   ```bash
   npm install
   npm run dev
   ```

3. Abra http://localhost:5173.

O Vite repassa as chamadas `/api` e `/saude` para `http://127.0.0.1:8000`. Se a API estiver em outra porta, use a variável `ECONOMIA_API`, por exemplo `ECONOMIA_API=http://127.0.0.1:8010 npm run dev`.

## Testes e build

```bash
npm test
npm run build
```

## O que a tela faz

- Envia a pergunta para `POST /api/v1/receitas/perguntas`.
- Mostra a resposta com as citações `[n]` ligadas à lista de fontes, os ingredientes que faltam (quando há receitas) e o tempo de resposta.
- Mostra um aviso quando a base não tem a informação (RN11), quando a pergunta é de preço (RN04) e quando a API está fora do ar.
