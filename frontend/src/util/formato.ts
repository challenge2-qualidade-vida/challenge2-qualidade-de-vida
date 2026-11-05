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
