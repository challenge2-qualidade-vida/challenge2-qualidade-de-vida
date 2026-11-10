import { describe, expect, it } from "vitest";

import { ErroDaApi, MENSAGEM_FORA_DO_AR, perguntar } from "./api";

function respostaHttp(status: number, corpo: unknown): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("perguntar", () => {
  it("envia a pergunta sem espaços nas pontas e devolve a resposta", async () => {
    const chamadas: [string, RequestInit][] = [];
    const corpo = { texto: "Ok [1].", encontrou: true, fontes: [], ingredientes_disponiveis: [], faltando: [], segundos: 1 };
    const buscar = (async (url: string, init: RequestInit) => {
      chamadas.push([url, init]);
      return respostaHttp(200, corpo);
    }) as typeof fetch;

    expect(await perguntar("  arroz?  ", buscar)).toEqual(corpo);
    expect(chamadas[0][0]).toBe("/api/v1/receitas/perguntas");
    expect(JSON.parse(chamadas[0][1].body as string)).toEqual({ pergunta: "arroz?" });
  });

  it("usa a mensagem da API quando ela está indisponível", async () => {
    const buscar = (async () => respostaHttp(503, { detail: "O Miau-ricio está indisponível agora." })) as typeof fetch;
    await expect(perguntar("arroz?", buscar)).rejects.toThrow("O Miau-ricio está indisponível agora.");
  });

  it("explica a pergunta inválida", async () => {
    const buscar = (async () => respostaHttp(422, { detail: [] })) as typeof fetch;
    await expect(perguntar("", buscar)).rejects.toThrow(/até 500 caracteres/);
  });

  it("avisa quando não consegue falar com a API", async () => {
    const buscar = (async () => {
      throw new TypeError("Failed to fetch");
    }) as typeof fetch;
    const erro = await perguntar("arroz?", buscar).catch((e) => e);
    expect(erro).toBeInstanceOf(ErroDaApi);
    expect(erro.message).toBe(MENSAGEM_FORA_DO_AR);
  });
});
