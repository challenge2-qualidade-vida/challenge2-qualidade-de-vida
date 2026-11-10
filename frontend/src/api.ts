// Cliente da API do Miau-ricio (specs/24-endpoint-rag/spec.md).

export type Fonte = {
  numero: number;
  titulo: string;
  descricao: string;
  url: string | null;
  licenca: string | null;
  tipo: "receita" | "conhecimento";
};

export type IngredientesQueFaltam = {
  receita: string;
  ingredientes: string[];
};

export type Resposta = {
  texto: string;
  encontrou: boolean;
  fontes: Fonte[];
  ingredientes_disponiveis: string[];
  faltando: IngredientesQueFaltam[];
  segundos: number;
};

export const MENSAGEM_FORA_DO_AR =
  "Não foi possível falar com o Miau-ricio. Confira se a API está no ar e tente de novo.";

export class ErroDaApi extends Error {}

/** Envia a pergunta e devolve a resposta com as fontes. Erros viram uma mensagem para a pessoa. */
export async function perguntar(
  pergunta: string,
  buscar: typeof fetch = fetch,
): Promise<Resposta> {
  let resposta: Response;
  try {
    resposta = await buscar("/api/v1/receitas/perguntas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta: pergunta.trim() }),
    });
  } catch {
    throw new ErroDaApi(MENSAGEM_FORA_DO_AR);
  }
  if (resposta.ok) {
    return (await resposta.json()) as Resposta;
  }
  if (resposta.status === 422) {
    throw new ErroDaApi("Escreva uma pergunta de até 500 caracteres.");
  }
  const corpo = await resposta.json().catch(() => null);
  const detalhe = corpo && typeof corpo.detail === "string" ? corpo.detail : null;
  throw new ErroDaApi(detalhe ?? MENSAGEM_FORA_DO_AR);
}
