import { describe, expect, it } from "vitest";

import { paragrafos, separarCitacoes } from "./citacoes";

describe("separarCitacoes", () => {
  it("separa o texto e as citações que têm fonte", () => {
    expect(separarCitacoes("Guarde na geladeira [1] por 5 dias [2].", new Set([1, 2]))).toEqual([
      { tipo: "texto", valor: "Guarde na geladeira " },
      { tipo: "citacao", numero: 1 },
      { tipo: "texto", valor: " por 5 dias " },
      { tipo: "citacao", numero: 2 },
      { tipo: "texto", valor: "." },
    ]);
  });

  it("mantém como texto um número sem fonte", () => {
    expect(separarCitacoes("Veja [9].", new Set([1]))).toEqual([{ tipo: "texto", valor: "Veja [9]." }]);
  });

  it("aceita citação no começo do texto", () => {
    expect(separarCitacoes("[1] Use o forno.", new Set([1]))).toEqual([
      { tipo: "citacao", numero: 1 },
      { tipo: "texto", valor: " Use o forno." },
    ]);
  });
});

describe("paragrafos", () => {
  it("separa por linha em branco e descarta vazios", () => {
    expect(paragrafos("Primeiro.\n\nSegundo\ncom quebra.\n\n\n")).toEqual([
      "Primeiro.",
      "Segundo\ncom quebra.",
    ]);
  });
});
