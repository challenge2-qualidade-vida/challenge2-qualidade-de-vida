// Tela Documento (#95): checagens antes do envio e textos do processamento.
// A tela só evita um envio que a API recusaria. Quem valida de verdade é a API (#92), e quem
// decide o que vai para revisão também (RN09, campo `revisar`).
import type { components } from "../api/esquema";

type Esquemas = components["schemas"];
export type ResultadoDoDocumento = Esquemas["ResultadoDoDocumento"];
export type EtapaDoDocumento = Esquemas["EtapaDoDocumento"];
export type ItemDoDocumento = Esquemas["ItemDoDocumento"];

/** Mesmo limite da #92. */
export const TAMANHO_MAXIMO_DO_ARQUIVO = 10 * 1024 * 1024;

const TIPOS_ACEITOS: Record<string, "imagem" | "pdf"> = {
  "image/jpeg": "imagem",
  "image/png": "imagem",
  "image/webp": "imagem",
  "application/pdf": "pdf",
};
const EXTENSOES_ACEITAS: Record<string, "imagem" | "pdf"> = { jpg: "imagem", jpeg: "imagem", png: "imagem", webp: "imagem", pdf: "pdf" };

/** Valor do atributo `accept` do campo de arquivo. */
export const ACEITA = [...Object.keys(TIPOS_ACEITOS), ".pdf"].join(",");

/** Só o que a tela precisa do arquivo: dá para testar sem um File de verdade. */
export interface ArquivoEscolhido { name: string; size: number; type: string }

/** Imagem ou PDF, pelo tipo informado pelo navegador ou, sem ele, pela extensão. */
export function tipoDoArquivo(arquivo: ArquivoEscolhido): "imagem" | "pdf" | null {
  if (arquivo.type) return TIPOS_ACEITOS[arquivo.type] ?? null;
  const extensao = arquivo.name.split(".").pop()?.toLowerCase() ?? "";
  return EXTENSOES_ACEITAS[extensao] ?? null;
}

/** Devolve o aviso para a tela, ou null se o envio pode ir para a API. */
export function problemaDoEnvio(pergunta: string, arquivo: ArquivoEscolhido | null): string | null {
  if (!pergunta.trim()) return "Escreva uma pergunta sobre o documento.";
  if (!arquivo) return "Escolha uma imagem ou um PDF.";
  if (!tipoDoArquivo(arquivo)) return "Envie uma imagem (JPEG, PNG ou WebP) ou um PDF.";
  if (arquivo.size === 0) return "O arquivo está vazio.";
  if (arquivo.size > TAMANHO_MAXIMO_DO_ARQUIVO) return "O arquivo pode ter até 10 MB.";
  return null;
}

/** Tamanho para mostrar ao lado do nome do arquivo. */
export function tamanhoDoArquivo(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`;
}

/** Passos do "Como funciona" da tela. */
export const PASSOS_DO_DOCUMENTO = [
  { emoji: "📸", titulo: "Envie a nota", texto: "Foto do cupom do mercado ou o PDF da NFC-e, até 10 MB." },
  { emoji: "❓", titulo: "Faça uma pergunta", texto: "Por exemplo: quanto gastei com hortifrúti? Qual foi o item mais caro?" },
  { emoji: "🐱", titulo: "O Recibaldo lê e responde", texto: "Ele lista os itens da nota e marca com ⚠️ o que você deve conferir." },
];

export const ETAPAS: { etapa: EtapaDoDocumento; texto: string }[] = [
  { etapa: "recebido", texto: "Documento recebido" },
  { etapa: "validado", texto: "Formato e tamanho conferidos" },
  { etapa: "encaminhado", texto: "Encaminhado para leitura" },
  { etapa: "extraido", texto: "Leitura concluída" },
];

/** Etapas já alcançadas, na ordem. A tela só marca o que a API disse que aconteceu. */
export function etapasAlcancadas(atual: EtapaDoDocumento): EtapaDoDocumento[] {
  const fim = ETAPAS.findIndex((e) => e.etapa === atual);
  return ETAPAS.slice(0, fim + 1).map((e) => e.etapa);
}

/** Aviso quando a API ainda não terminou a leitura: nunca diz que a extração foi concluída. */
export function avisoDaEtapa(resultado: ResultadoDoDocumento): string | null {
  if (resultado.etapa === "extraido") return null;
  if (resultado.etapa === "encaminhado") return "O documento foi encaminhado para leitura. A resposta aparece quando a leitura terminar.";
  return "O documento foi recebido, mas a leitura ainda não começou.";
}

export const quantidade = (item: ItemDoDocumento) =>
  `${item.quantidade.toLocaleString("pt-BR", { maximumFractionDigits: 3 })} ${item.unidade}`;
