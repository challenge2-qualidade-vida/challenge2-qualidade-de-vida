// Cliente da API gerado do OpenAPI (openapi-typescript + openapi-fetch). Todas as telas usam este cliente.
// O middleware põe o token de acesso, renova a sessão quando a API responde 401 e repete a chamada uma vez.
import createClient, { type Middleware } from "openapi-fetch";
import { renovar, tokenAtual } from "../autenticacao/sessao";
import type { paths } from "./esquema";
import { lerProblema, ProblemaDaApi, type Problema } from "./problemas";
import { transporte } from "./transporte";

const copias = new WeakMap<Request, Request>();

const comToken = (pedido: Request) => {
  const token = tokenAtual();
  if (token) pedido.headers.set("Authorization", `Bearer ${token}`);
  return pedido;
};

const autenticacao: Middleware = {
  onRequest({ request }) {
    const pedido = comToken(request);
    // Guarda uma cópia antes de o corpo ser lido, para poder repetir depois de renovar.
    copias.set(pedido, pedido.clone());
    return pedido;
  },
  async onResponse({ request, response }) {
    if (response.status !== 401 || new URL(request.url).pathname.includes("/auth/")) return response;
    const copia = copias.get(request);
    if (!copia || !(await renovar())) return response;
    return transporte(comToken(copia));
  },
};

export const api = createClient<paths>({ baseUrl: "/api/v1", fetch: transporte });
api.use(autenticacao);

/** Devolve os dados da resposta ou lança o erro como ProblemaDaApi. */
export async function exigir<T>(resultado: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await resultado;
  if (response.ok && data !== undefined) return data;
  if (error && typeof (error as Problema).title === "string") throw new ProblemaDaApi({ ...(error as Problema), status: response.status });
  throw await lerProblema(response);
}
