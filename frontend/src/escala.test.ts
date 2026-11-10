import { describe, expect, it } from "vitest";

import { decimal, larguraDaBarra, plural } from "./escala";

describe("larguraDaBarra", () => {
  it("leva o score para a escala de 0,75 a 1", () => {
    expect(larguraDaBarra(0.75)).toBe(0);
    expect(larguraDaBarra(0.875)).toBe(50);
    expect(larguraDaBarra(1)).toBe(100);
  });

  it("limita fora da escala", () => {
    expect(larguraDaBarra(0.5)).toBe(0);
    expect(larguraDaBarra(1.2)).toBe(100);
  });
});

describe("formatação", () => {
  it("usa vírgula decimal", () => {
    expect(decimal(0.8671)).toBe("0,867");
    expect(decimal(2.34, 1)).toBe("2,3");
  });

  it("concorda o plural", () => {
    expect(plural(1, "citado", "citados")).toBe("1 citado");
    expect(plural(0, "citado", "citados")).toBe("0 citados");
  });
});
