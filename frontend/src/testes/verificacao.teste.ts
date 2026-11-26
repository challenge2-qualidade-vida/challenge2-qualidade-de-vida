// Cenários de specs/98-interface-demo-verificacao/cenarios.feature.
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { verificacaoFalsa } from "../api/dados-falsos/verificacao";
import { VereditoDaVerificacao } from "../telas/Verificar";
import { caminhoDosAgentes, destinoDoRetorno, problemaDaAlegacao, resumirPasso, type ResultadoDaVerificacao } from "../util/verificacao";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const frases = (texto: string) => texto.split(/(?<=[.!?])\s+/).filter(Boolean);

describe("Veredito aprovado direto", () => {
  const resultado = verificacaoFalsa("Alimentos ultraprocessados devem ser evitados", "consumidor_geral");
  it("mostra a classificação reciclada e a fonte do Guia Alimentar", () => {
    expect(resultado.veredito.classificacao).toBe("reciclada");
    expect(resultado.veredito.fontes.map((f) => f.titulo)).toContain("Guia Alimentar para a População Brasileira");
  });
  it("passa por Research, Analysis, Validation e Communication, sem retorno", () => {
    expect(caminhoDosAgentes(resultado.historico)).toEqual(["Research", "Analysis", "Validation", "Communication"]);
    expect(resultado.retornos).toBe(0);
    expect(resultado.historico.map(destinoDoRetorno).filter(Boolean)).toEqual([]);
  });
});

describe("Retorno do Validation aparece no caminho", () => {
  const resultado = verificacaoFalsa("O feijão tem fibra e por isso cura o diabetes", "consumidor_geral");
  it("mostra a validação reprovada com retorno ao Research", () => {
    const reprovada = resultado.historico.findIndex((p) => destinoDoRetorno(p) !== null);
    expect(reprovada).toBeGreaterThan(-1);
    expect(destinoDoRetorno(resultado.historico[reprovada])).toBe("Research");
    expect(resumirPasso(resultado.historico[reprovada])).toMatch(/^Reprovou a análise: /);
    expect(caminhoDosAgentes(resultado.historico.slice(reprovada + 1)).slice(0, 3)).toEqual(["Research", "Analysis", "Validation"]);
    expect(resultado.retornos).toBe(1);
  });
});

describe("Perfil rápido", () => {
  it("devolve a mensagem com no máximo 2 frases", () => {
    for (const alegacao of ["Alimentos ultraprocessados devem ser evitados", "O feijão cura o diabetes"]) {
      expect(frases(verificacaoFalsa(alegacao, "consumidor_rapido").veredito.mensagem).length).toBeLessThanOrEqual(2);
    }
  });
});

describe("Verificação não conclusiva", () => {
  let raiz: ReturnType<typeof createRoot> | null = null;
  afterEach(() => { act(() => raiz?.unmount()); document.body.innerHTML = ""; });

  function mostrar(resultado: ResultadoDaVerificacao) {
    const lugar = document.createElement("div");
    document.body.append(lugar);
    raiz = createRoot(lugar);
    act(() => raiz!.render(createElement(VereditoDaVerificacao, { resultado })));
    return lugar;
  }

  it("mostra o aviso quando a validação não aprovou", () => {
    const base = verificacaoFalsa("Alimentos ultraprocessados devem ser evitados");
    const lugar = mostrar({ ...base, veredito: { ...base.veredito, classificacao: null, aprovado_pela_validacao: false } });
    expect(lugar.querySelector("#aviso-nao-conclusivo")?.textContent).toMatch(/não conclusiva/);
    expect(lugar.querySelector("#classificacao")).toBeNull();
  });
  it("não mostra o aviso quando a validação aprovou", () => {
    const lugar = mostrar(verificacaoFalsa("Alimentos ultraprocessados devem ser evitados"));
    expect(lugar.querySelector("#aviso-nao-conclusivo")).toBeNull();
    expect(lugar.querySelector("#classificacao")?.textContent).toBe("Reciclada");
    expect(lugar.textContent).not.toMatch(/verdadeir|fals[oa]/i);
  });
});

describe("Alegação vazia", () => {
  it("pede para escrever a alegação (e a tela não chama a API)", () => {
    expect(problemaDaAlegacao("")).toBe("Escreva a alegação que você quer verificar.");
    expect(problemaDaAlegacao("   ")).toBe("Escreva a alegação que você quer verificar.");
    expect(problemaDaAlegacao("a".repeat(501))).toMatch(/500 caracteres/);
    expect(problemaDaAlegacao("Ovo aumenta o colesterol?")).toBeNull();
  });
});

describe("Resumo de cada agente", () => {
  it("lê só os campos do contrato da #82", () => {
    const [research, analysis, validation, communication] = verificacaoFalsa("Alimentos ultraprocessados devem ser evitados").historico;
    expect(resumirPasso(research)).toBe("5 trechos encontrados · melhor score 0,86 · limite de 5");
    expect(resumirPasso(analysis)).toBe("Classificou como reciclada · confiança 0,91");
    expect(resumirPasso(validation)).toBe("Aprovou a análise.");
    expect(resumirPasso(communication)).toBe("Escreveu o veredito.");
  });
  it("não quebra com saídas incompletas", () => {
    expect(resumirPasso({ agente: "research", entrada: {}, saida: {}, segundos: 0 })).toBe("0 trechos encontrados");
    expect(resumirPasso({ agente: "analysis", entrada: {}, saida: { classificacao: null }, segundos: 0 })).toBe("Não chegou a uma classificação.");
  });
});

describe("Tela desligada por padrão", () => {
  afterEach(() => { vi.unstubAllEnvs(); vi.resetModules(); });
  const ligada = async (valor: string) => {
    vi.stubEnv("VITE_FUNCIONALIDADES", valor);
    vi.resetModules();
    const { funcionalidadeLigada } = await import("../funcionalidades");
    return funcionalidadeLigada("verificacao");
  };
  it("fica desligada sem a flag e com \"todas\"", async () => {
    expect(await ligada("")).toBe(false);
    expect(await ligada("todas")).toBe(false);
  });
  it("liga pelo nome", async () => {
    expect(await ligada("todas,verificacao")).toBe(true);
  });
});
