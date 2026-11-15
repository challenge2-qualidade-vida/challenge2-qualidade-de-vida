import { describe, expect, it } from "vitest";

import { identificadorAnonimo, identificadorDaConversa } from "./identificadores";

const A = "3f2b8c1e-9a4d-4e6f-8b2a-1c3d5e7f9a0b";
const B = "7a1c2d3e-4f5a-4b6c-9d7e-8f9a0b1c2d3e";

function memoria(inicial: Record<string, string> = {}) {
  const dados = { ...inicial };
  return {
    dados,
    getItem: (chave: string) => dados[chave] ?? null,
    setItem: (chave: string, valor: string) => {
      dados[chave] = valor;
    },
  };
}

describe("identificadorAnonimo", () => {
  it("cria na primeira visita e reaproveita nas seguintes", () => {
    const armazenamento = memoria();
    expect(identificadorAnonimo(armazenamento, () => A)).toBe(A);
    expect(identificadorAnonimo(armazenamento, () => B)).toBe(A);
  });

  it("troca um valor guardado fora do formato", () => {
    const armazenamento = memoria({ "economia.identificador-anonimo": "maria@exemplo.com" });
    expect(identificadorAnonimo(armazenamento, () => A)).toBe(A);
  });

  it("funciona sem armazenamento", () => {
    expect(identificadorAnonimo(null, () => A)).toBe(A);
    const quebrado = {
      getItem: () => {
        throw new Error("bloqueado");
      },
      setItem: () => {},
    };
    expect(identificadorAnonimo(quebrado, () => B)).toBe(B);
  });
});

describe("identificadorDaConversa", () => {
  it("mantém a mesma conversa até pedir uma nova", () => {
    const primeira = identificadorDaConversa(true, () => A);
    expect(identificadorDaConversa(false, () => B)).toBe(primeira);
    expect(identificadorDaConversa(true, () => B)).toBe(B);
  });
});
