// Sessão da pessoa: login com e-mail e senha, token de acesso de 15 minutos e token de
// renovação de 7 dias. O token de acesso fica só na memória; o de renovação vem num cookie
// httpOnly que o JavaScript não lê. Ao abrir o site, a sessão é recuperada pelo cookie.
import createClient from "openapi-fetch";
import type { components, paths } from "../api/esquema";
import { ProblemaDaApi } from "../api/problemas";
import { transporte } from "../api/transporte";

type Sessao = components["schemas"]["Sessao"];
export type Pessoa = Sessao["pessoa"];

// As rotas de login não levam o token, então usam um cliente sem o middleware de autenticação.
const clienteDeLogin = createClient<paths>({ baseUrl: "/api/v1", fetch: transporte });

let tokenDeAcesso: string | null = null;
let pessoa: Pessoa | null = null;
let renovacaoAgendada: ReturnType<typeof setTimeout> | undefined;
let renovando: Promise<boolean> | null = null;
const ouvintes = new Set<() => void>();

const avisar = () => ouvintes.forEach((f) => f());

export function ouvirSessao(ouvinte: () => void) {
  ouvintes.add(ouvinte);
  return () => { ouvintes.delete(ouvinte); };
}

export const pessoaLogada = () => pessoa;
export const tokenAtual = () => tokenDeAcesso;

function abrir(sessao: Sessao) {
  tokenDeAcesso = sessao.token_acesso;
  pessoa = sessao.pessoa;
  clearTimeout(renovacaoAgendada);
  // Renova um minuto antes de vencer, para a pessoa não ver a sessão cair.
  renovacaoAgendada = setTimeout(() => { void renovar(); }, Math.max(sessao.expira_em_s - 60, 30) * 1000);
  avisar();
}

function fechar() {
  tokenDeAcesso = null;
  pessoa = null;
  clearTimeout(renovacaoAgendada);
  avisar();
}

function exigirSessao(r: { data?: Sessao; error?: unknown; response: Response }) {
  if (!r.data) throw new ProblemaDaApi((r.error as components["schemas"]["Problema"]) ?? { status: r.response.status, title: "Erro na API" });
  abrir(r.data);
}

export async function entrar(email: string, senha: string) {
  exigirSessao(await clienteDeLogin.POST("/auth/login", { body: { email, senha } }));
}

export async function cadastrar(nome: string, email: string, senha: string) {
  exigirSessao(await clienteDeLogin.POST("/auth/cadastro", { body: { nome, email, senha } }));
}

/** Pede um novo token de acesso com o cookie de renovação. Chamadas simultâneas esperam a mesma renovação. */
export function renovar(): Promise<boolean> {
  renovando ??= clienteDeLogin.POST("/auth/renovar").then((r) => {
    if (r.data) abrir(r.data);
    else fechar();
    return !!r.data;
  }).catch(() => {
    fechar();
    return false;
  }).finally(() => { renovando = null; });
  return renovando;
}

export async function sair() {
  await clienteDeLogin.POST("/auth/sair", { headers: tokenDeAcesso ? { Authorization: `Bearer ${tokenDeAcesso}` } : {} }).catch(() => {});
  fechar();
}
