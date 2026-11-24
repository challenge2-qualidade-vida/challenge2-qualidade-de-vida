// Identificador anônimo da pessoa e identificador da conversa (specs/29-observabilidade-langfuse).
// São UUID v4 aleatórios, sem dado pessoal (RN30). A API os repassa ao Langfuse como pessoa
// (user_id) e sessão (session_id). Quando existir login, a pessoa passa a ser o id da conta.

const CHAVE_DO_IDENTIFICADOR = "economia.identificador-anonimo";
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

type Armazenamento = Pick<Storage, "getItem" | "setItem">;

function armazenamentoDoNavegador(): Armazenamento | null {
  try {
    return window.localStorage;
  } catch {
    return null; // janela anônima ou dados do site bloqueados
  }
}

/** Identificador anônimo guardado no navegador, criado na primeira visita. */
export function identificadorAnonimo(
  armazenamento: Armazenamento | null = armazenamentoDoNavegador(),
  gerar: () => string = () => crypto.randomUUID(),
): string {
  try {
    const guardado = armazenamento?.getItem(CHAVE_DO_IDENTIFICADOR);
    if (guardado && UUID_V4.test(guardado)) {
      return guardado;
    }
    const novo = gerar();
    armazenamento?.setItem(CHAVE_DO_IDENTIFICADOR, novo);
    return novo;
  } catch {
    return gerar(); // sem armazenamento, vale só para esta página
  }
}

// uma conversa por carregamento da página
let conversaAtual: string | null = null;

/** Identificador da conversa em andamento. `nova` começa outra conversa. */
export function identificadorDaConversa(
  nova = false,
  gerar: () => string = () => crypto.randomUUID(),
): string {
  if (nova || conversaAtual === null) {
    conversaAtual = gerar();
  }
  return conversaAtual;
}

/** Cabeçalhos que ligam a pergunta à pessoa e à conversa no Langfuse. */
export function cabecalhosDeIdentificacao(): Record<string, string> {
  return {
    "X-Identificador-Anonimo": identificadorAnonimo(),
    "X-Conversa": identificadorDaConversa(),
  };
}
