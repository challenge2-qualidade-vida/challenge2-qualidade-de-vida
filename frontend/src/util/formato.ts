// Formatação só para a tela. A API manda dinheiro em centavos (inteiro).

const MOEDA = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

/** Centavos → "R$ 1.234,56". */
export const reais = (centavos: number) => MOEDA.format(centavos / 100);

/** "2026-10-20" → "20/10/2026". */
export const dataBR = (iso: string) => iso.split("-").reverse().join("/");

/** 2.5 → "2,5 km". */
export const km = (v: number) => `${String(v).replace(".", ",")} km`;

/** O LLM às vezes responde em Markdown; a tela mostra texto simples. */
export const semMarkdown = (t: string) =>
  t.replace(/^#{1,6}\s*/gm, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/^\s*[-*]\s+/gm, "• ");

/** Próximo valor das setas em reais: passos redondos, nunca abaixo do mínimo (de 799,92 vai a 800 ou 790). */
export function proximoValorRedondo(atual: number, passo: number, sentido: 1 | -1, minimo: number) {
  const proximo = sentido > 0
    ? Math.floor(atual / passo + 1e-9) * passo + passo
    : Math.ceil(atual / passo - 1e-9) * passo - passo;
  return Math.max(minimo, proximo);
}
