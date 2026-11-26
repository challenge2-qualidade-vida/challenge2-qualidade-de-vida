// "Como funciona" e exemplos de primeiro uso (ajuda no contexto, sem tour).
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { verificacaoFalsa } from "../api/dados-falsos/verificacao";
import { ComoFunciona } from "../componentes/ComoFunciona";
import { EXEMPLOS_DE_ALEGACAO, PASSOS_DA_VERIFICACAO, problemaDaAlegacao } from "../util/verificacao";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// O jsdom do projeto não traz localStorage: um armazenamento em memória basta para o teste.
const guardado = new Map<string, string>();
beforeEach(() => {
  guardado.clear();
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => guardado.get(k) ?? null,
    setItem: (k: string, v: string) => { guardado.set(k, v); },
  });
});

let raiz: ReturnType<typeof createRoot> | null = null;
function mostrar(chave: string) {
  const lugar = document.createElement("div");
  document.body.append(lugar);
  raiz = createRoot(lugar);
  act(() => raiz!.render(createElement(ComoFunciona, { chave, passos: PASSOS_DA_VERIFICACAO })));
  return lugar;
}
afterEach(() => { if (raiz) act(() => raiz!.unmount()); raiz = null; document.body.innerHTML = ""; vi.unstubAllGlobals(); });

describe("Como funciona", () => {
  it("abre na primeira visita com os passos numerados", () => {
    const caixa = mostrar("verificar").querySelector("details")!;
    expect(caixa.open).toBe(true);
    expect(caixa.querySelectorAll("li")).toHaveLength(3);
    expect(caixa.textContent).toMatch(/1\. Escreva o que você ouviu/);
  });
  it("lembra quando a pessoa oculta", () => {
    const caixa = mostrar("verificar").querySelector("details")!;
    act(() => { caixa.open = false; caixa.dispatchEvent(new Event("toggle")); });
    expect(localStorage.getItem("economia-como-funciona-verificar")).toBe("fechada");
    act(() => raiz!.unmount()); raiz = null;
    expect(mostrar("verificar").querySelector("details")!.open).toBe(false);
  });
});

describe("Exemplos de primeiro uso da tela Verificar", () => {
  it("são alegações válidas que os dados falsos respondem (um aprovado direto e um com retorno)", () => {
    for (const exemplo of EXEMPLOS_DE_ALEGACAO) expect(problemaDaAlegacao(exemplo)).toBeNull();
    expect(EXEMPLOS_DE_ALEGACAO.map((e) => verificacaoFalsa(e).retornos)).toEqual([0, 1]);
  });
});
