// Cenários de specs/95-envio-de-documentos/cenarios.feature.
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { conferirEnvioFalso, documentoFalso } from "../api/dados-falsos/documentos";
import { ResultadoDoEnvio } from "../telas/Documento";
import { avisoDaEtapa, problemaDoEnvio, type ResultadoDoDocumento } from "../util/documentos";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const MB = 1024 * 1024;
const arquivo = (nome: string, tipo: string, bytes: number) => new File([new Uint8Array(bytes)], nome, { type: tipo });

/** O que a rota falsa faz com os campos do multipart (o Request do Node não lê o FormData do jsdom). */
function enviar(pergunta: string | null, doc: File | null) {
  const conferido = conferirEnvioFalso(pergunta, doc);
  if (!("tipo" in conferido)) return { status: conferido.status, detail: conferido.detail, resultado: null };
  return { status: 200, detail: null, resultado: documentoFalso(pergunta ?? "", conferido.tipo) };
}

let raiz: ReturnType<typeof createRoot> | null = null;
function mostrar(resultado: ResultadoDoDocumento) {
  const lugar = document.createElement("div");
  document.body.append(lugar);
  raiz = createRoot(lugar);
  act(() => raiz!.render(createElement(ResultadoDoEnvio, { resultado })));
  return lugar;
}
afterEach(() => { if (raiz) act(() => raiz!.unmount()); raiz = null; document.body.innerHTML = ""; });

describe("Enviar uma imagem com pergunta", () => {
  it("manda a pergunta e o arquivo no mesmo envio e recebe a resposta e os itens", () => {
    const resposta = enviar("Quanto gastei com hortifrúti?", arquivo("nota.jpg", "image/jpeg", 2 * MB));
    expect(resposta.status).toBe(200);
    const resultado = resposta.resultado!;
    expect(resultado.tipo).toBe("imagem");
    expect(resultado.etapa).toBe("extraido");
    expect(resultado.resposta).toMatch(/hortifrúti/);
    const lugar = mostrar(resultado);
    expect(lugar.querySelector("#resposta-documento")?.textContent).toMatch(/R\$\s?14,70/);
    expect(lugar.querySelector("#itens-documento")?.textContent).toMatch(/R\$\s?24,90/);
  });
});

describe("Enviar um PDF com pergunta", () => {
  it("lê o PDF e responde", () => {
    const resultado = enviar("Qual foi o item mais caro?", arquivo("nota.pdf", "application/pdf", MB)).resultado!;
    expect(resultado.tipo).toBe("pdf");
    expect(resultado.resposta).toMatch(/mais caro/);
  });
});

describe("Item com confiança baixa aparece para conferir", () => {
  it("destaca só os itens que a API marcou", () => {
    const lugar = mostrar(documentoFalso("Quanto gastei?", "imagem"));
    const marcados = [...lugar.querySelectorAll('tr[data-revisar="true"]')];
    expect(marcados).toHaveLength(1);
    expect(marcados[0].textContent).toMatch(/BANANA PRATA KG.*conferir/);
    expect(lugar.querySelectorAll('tr[data-revisar="false"]')[0].textContent).not.toMatch(/conferir/);
  });
});

describe("Estado do processamento", () => {
  it("na etapa encaminhado, não diz que a extração foi concluída", () => {
    const resultado: ResultadoDoDocumento = { documento_id: "doc-1", tipo: "imagem", etapa: "encaminhado", resposta: null, itens: null };
    expect(avisoDaEtapa(resultado)).toMatch(/encaminhado para leitura/);
    const lugar = mostrar(resultado);
    expect(lugar.querySelector('[data-etapa="encaminhado"]')?.getAttribute("data-alcancada")).toBe("true");
    expect(lugar.querySelector('[data-etapa="extraido"]')?.getAttribute("data-alcancada")).toBe("false");
    expect(lugar.querySelector("#resposta-documento")).toBeNull();
    expect(lugar.querySelector("#itens-documento")).toBeNull();
  });
});

describe("Erros conferidos antes do envio", () => {
  const nota = { name: "nota.jpg", size: 2 * MB, type: "image/jpeg" };
  it.each([
    ["a pergunta vazia", "  ", nota, "Escreva uma pergunta sobre o documento."],
    ["nenhum arquivo escolhido", "Quanto gastei?", null, "Escolha uma imagem ou um PDF."],
    ["um arquivo planilha.xlsx", "Quanto gastei?", { name: "planilha.xlsx", size: 1000, type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }, "Envie uma imagem (JPEG, PNG ou WebP) ou um PDF."],
    ["um arquivo vazio", "Quanto gastei?", { ...nota, size: 0 }, "O arquivo está vazio."],
    ["uma imagem de 11 MB", "Quanto gastei?", { ...nota, size: 11 * MB }, "O arquivo pode ter até 10 MB."],
  ])("%s", (_situacao, pergunta, doc, aviso) => {
    expect(problemaDoEnvio(pergunta, doc)).toBe(aviso);
  });
  it("aceita imagem ou PDF de até 10 MB, mesmo sem o tipo informado pelo navegador", () => {
    expect(problemaDoEnvio("Quanto gastei?", nota)).toBeNull();
    expect(problemaDoEnvio("Quanto gastei?", { name: "nota.PDF", size: 10 * MB, type: "" })).toBeNull();
  });
});

describe("Erro da API", () => {
  it("responde 415 com a mensagem de formato não suportado", () => {
    const resposta = enviar("Quanto gastei?", arquivo("planilha.xlsx", "application/vnd.ms-excel", 1000));
    expect(resposta.status).toBe(415);
    expect(resposta.detail).toMatch(/Formato não suportado/);
  });
  it("recusa arquivo acima de 10 MB com 413", () => {
    const resposta = enviar("Quanto gastei?", arquivo("grande.png", "image/png", 10 * MB + 1));
    expect(resposta.status).toBe(413);
  });
});

describe("Tela desligada por padrão", () => {
  afterEach(() => { vi.unstubAllEnvs(); vi.resetModules(); });
  const ligada = async (valor: string) => {
    vi.stubEnv("VITE_FUNCIONALIDADES", valor);
    vi.resetModules();
    const { funcionalidadeLigada } = await import("../funcionalidades");
    return funcionalidadeLigada("documentos");
  };
  it("fica desligada sem a flag e com \"todas\", e liga pelo nome", async () => {
    expect(await ligada("")).toBe(false);
    expect(await ligada("todas")).toBe(false);
    expect(await ligada("todas,documentos")).toBe(true);
  });
});
