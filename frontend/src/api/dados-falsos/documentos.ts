// Dados falsos da rota POST /documentos (proposta da #95 para a #92), para a demo da semana 5.
// Nota fictícia, escrita à mão, com valores em centavos. Não lê o arquivo: devolve sempre a
// mesma nota, com a resposta escolhida pela pergunta.
import type { components } from "../esquema";

type Esquemas = components["schemas"];

const TAMANHO_MAXIMO = 10 * 1024 * 1024;
const TIPOS: Record<string, "imagem" | "pdf"> = { "image/jpeg": "imagem", "image/png": "imagem", "image/webp": "imagem", "application/pdf": "pdf" };

const ITENS: Esquemas["ItemDoDocumento"][] = [
  { descricao: "ARROZ T1 5KG", quantidade: 1, unidade: "UN", valor_total: 2490, confianca: 0.97, revisar: false },
  { descricao: "FEIJAO CARIOCA 1KG", quantidade: 2, unidade: "UN", valor_total: 1598, confianca: 0.95, revisar: false },
  { descricao: "BANANA PRATA KG", quantidade: 1.2, unidade: "KG", valor_total: 659, confianca: 0.78, revisar: true },
  { descricao: "TOMATE ITALIANO KG", quantidade: 0.8, unidade: "KG", valor_total: 512, confianca: 0.9, revisar: false },
  { descricao: "ALFACE CRESPA UN", quantidade: 1, unidade: "UN", valor_total: 299, confianca: 0.88, revisar: false },
];

const RESPOSTAS: [RegExp, string][] = [
  [/hortifr|fruta|verdura|legume/i, "Com hortifrúti foram R$ 14,70: banana, tomate e alface. Confira a banana: a leitura do peso ficou com baixa confiança."],
  [/caro|maior/i, "O item mais caro da nota é o arroz tipo 1 de 5 kg, por R$ 24,90."],
];
const RESPOSTA_PADRAO = "A nota tem 5 itens, com arroz, feijão e hortifrúti. Um item ficou marcado para você conferir.";

export function documentoFalso(pergunta: string, tipo: "imagem" | "pdf"): Esquemas["ResultadoDoDocumento"] {
  const resposta = RESPOSTAS.find(([padrao]) => padrao.test(pergunta))?.[1] ?? RESPOSTA_PADRAO;
  return { documento_id: `doc-falso-${Date.now()}`, tipo, etapa: "extraido", resposta, itens: ITENS };
}

/** Mesmas recusas da #92, em Problem Details. Devolve o status e a mensagem, ou o tipo aceito. */
export function conferirEnvioFalso(pergunta: unknown, arquivo: unknown): { status: number; title: string; detail: string } | { tipo: "imagem" | "pdf" } {
  if (typeof pergunta !== "string" || !pergunta.trim()) return { status: 400, title: "Pergunta ausente", detail: "A pergunta é obrigatória." };
  if (!(arquivo instanceof Blob)) return { status: 400, title: "Arquivo ausente", detail: "O arquivo é obrigatório." };
  const tipo = TIPOS[arquivo.type];
  if (!tipo) return { status: 415, title: "Formato não suportado", detail: "Formato não suportado. Envie uma imagem ou um PDF." };
  if (arquivo.size === 0) return { status: 400, title: "Arquivo vazio", detail: "O arquivo está vazio." };
  if (arquivo.size > TAMANHO_MAXIMO) return { status: 413, title: "Arquivo grande demais", detail: "O tamanho máximo permitido é 10 MB." };
  return { tipo };
}
