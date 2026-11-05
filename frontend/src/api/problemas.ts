// Erros da API no formato Problem Details (RFC 9457), tratados num só lugar.
import type { components } from "./esquema";

export type Problema = components["schemas"]["Problema"];

export class ProblemaDaApi extends Error {
  readonly problema: Problema;

  constructor(problema: Problema) {
    super(problema.detail ?? problema.title);
    this.name = "ProblemaDaApi";
    this.problema = problema;
  }

  get status() {
    return this.problema.status;
  }
}

/** Lê o corpo de uma resposta de erro. Se não vier em Problem Details, monta um com o status. */
export async function lerProblema(resposta: Response): Promise<ProblemaDaApi> {
  try {
    const corpo = await resposta.clone().json();
    if (corpo && typeof corpo.title === "string") return new ProblemaDaApi({ status: resposta.status, ...corpo });
  } catch {
    /* corpo vazio ou não JSON */
  }
  return new ProblemaDaApi({ status: resposta.status, title: resposta.statusText || "Erro na API" });
}

/** Texto para a tela, igual ao do site antigo: o detalhe, ou o título, do problema. */
export function mensagemDoProblema(erro: unknown): string {
  if (erro instanceof ProblemaDaApi) return erro.problema.detail ?? erro.problema.title;
  if (erro instanceof TypeError) return "Não foi possível falar com a API.";
  return erro instanceof Error ? erro.message : String(erro);
}
