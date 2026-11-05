import { describe, expect, it } from "vitest";
import { lerProblema, mensagemDoProblema, ProblemaDaApi } from "../api/problemas";
import { lerEventos } from "../api/sse";

describe("Problem Details", () => {
  it("lê o corpo application/problem+json", async () => {
    const resposta = new Response(JSON.stringify({ title: "Orçamento inválido", status: 422, detail: "O orçamento precisa ser maior que zero." }), { status: 422, headers: { "Content-Type": "application/problem+json" } });
    const erro = await lerProblema(resposta);
    expect(erro).toBeInstanceOf(ProblemaDaApi);
    expect(erro.status).toBe(422);
    expect(mensagemDoProblema(erro)).toBe("O orçamento precisa ser maior que zero.");
  });
  it("monta um problema quando o corpo não segue o formato", async () => {
    const erro = await lerProblema(new Response("falhou", { status: 502, statusText: "Bad Gateway" }));
    expect(mensagemDoProblema(erro)).toBe("Bad Gateway");
  });
});

describe("SSE da conversa", () => {
  it("entrega os eventos texto, blocos e fim, mesmo quebrados entre pedaços", async () => {
    const pedacos = ["event: texto\ndata: Olá, \n\nevent: tex", "to\ndata: tudo bem?\n\nevent: blocos\ndata: {\"aviso\":null}\n\n", "event: fim\ndata: {}\n\n"];
    const corpo = new ReadableStream<Uint8Array>({ start(c) { pedacos.forEach((p) => c.enqueue(new TextEncoder().encode(p))); c.close(); } });
    const eventos = [];
    for await (const e of lerEventos(new Response(corpo))) eventos.push(e);
    expect(eventos).toEqual([
      { tipo: "texto", texto: "Olá, " },
      { tipo: "texto", texto: "tudo bem?" },
      { tipo: "blocos", blocos: { aviso: null } },
      { tipo: "fim" },
    ]);
  });
});
