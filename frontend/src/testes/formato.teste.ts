import { describe, expect, it } from "vitest";
import { dataBR, km, proximoValorRedondo, reais, semMarkdown } from "../util/formato";

describe("formato", () => {
  it("formata centavos em reais", () => {
    expect(reais(67092)).toBe("R$\u00a0670,92"); // o Intl usa espaço não separável
    expect(reais(1000)).toBe("R$\u00a010,00");
  });
  it("formata data e distância", () => {
    expect(dataBR("2026-10-20")).toBe("20/10/2026");
    expect(km(2.5)).toBe("2,5 km");
  });
  it("tira o Markdown do LLM", () => {
    expect(semMarkdown("## Título\n**forte**\n- item")).toBe("Título\nforte\n• item");
  });
  it("as setas andam em passos redondos e respeitam o mínimo", () => {
    expect(proximoValorRedondo(799.92, 10, 1, 1)).toBe(800);
    expect(proximoValorRedondo(799.92, 10, -1, 1)).toBe(790);
    expect(proximoValorRedondo(800, 10, 1, 1)).toBe(810);
    expect(proximoValorRedondo(5, 10, -1, 1)).toBe(1);
  });
});
