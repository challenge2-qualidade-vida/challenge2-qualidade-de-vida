// Formatação da tela Verificar (#98). Só formata o que a API devolve: classificação, confiança,
// scores e aprovação vêm prontos do backend (RN01). A tela não usa "verdadeiro" nem "falso".
import type { components } from "../api/esquema";

type Esquemas = components["schemas"];
export type ResultadoDaVerificacao = Esquemas["ResultadoDaVerificacao"];
export type PassoDoAgente = Esquemas["PassoDoAgente"];
export type Classificacao = Esquemas["ClassificacaoDaAlegacao"];
export type Perfil = Esquemas["PerfilDeLeitura"];

/** Mesmo limite da rota da #82 (RequisicaoDaAlegacao). */
export const TAMANHO_MAXIMO_DA_ALEGACAO = 500;

/** Devolve o aviso para a tela, ou null se a alegação pode ir para a API. */
export function problemaDaAlegacao(texto: string): string | null {
  const limpo = texto.trim();
  if (!limpo) return "Escreva a alegação que você quer verificar.";
  if (limpo.length > TAMANHO_MAXIMO_DA_ALEGACAO) return `A alegação pode ter até ${TAMANHO_MAXIMO_DA_ALEGACAO} caracteres.`;
  return null;
}

/** Passos do "Como funciona" da tela. */
export const PASSOS_DA_VERIFICACAO = [
  { emoji: "✍️", titulo: "Escreva o que você ouviu", texto: "Uma frase sobre alimentação, como as que circulam em grupos e redes sociais." },
  { emoji: "🔎", titulo: "Os agentes conferem", texto: "Um busca na base de conhecimento, outro analisa, outro valida. Se algo não fecha, eles refazem." },
  { emoji: "💬", titulo: "Você recebe o veredito", texto: "Quanto a base cobre a frase, com as fontes. Sem fonte, a resposta diz que não foi conclusiva." },
];

/** Alegações de exemplo para quem chega sem uma pergunta pronta. */
export const EXEMPLOS_DE_ALEGACAO = [
  "Alimentos ultraprocessados devem ser evitados",
  "O feijão tem fibra e por isso cura o diabetes",
];

export const PERFIS: { valor: Perfil; rotulo: string }[] = [
  { valor: "consumidor_geral", rotulo: "Explicação completa" },
  { valor: "consumidor_rapido", rotulo: "Resposta rápida" },
];

export const CLASSIFICACOES: Record<Classificacao, { rotulo: string; explicacao: string }> = {
  reciclada: { rotulo: "Reciclada", explicacao: "A base de conhecimento já cobre essa alegação." },
  parcial: { rotulo: "Parcial", explicacao: "A base de conhecimento cobre só parte da alegação." },
  nova: { rotulo: "Nova", explicacao: "A base de conhecimento não cobre essa alegação." },
};

export const AGENTES: Record<PassoDoAgente["agente"], { nome: string; emoji: string }> = {
  research: { nome: "Research", emoji: "🔎" },
  analysis: { nome: "Analysis", emoji: "🧠" },
  validation: { nome: "Validation", emoji: "🛡️" },
  communication: { nome: "Communication", emoji: "💬" },
};

const numero = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
const texto = (v: unknown) => (typeof v === "string" && v ? v : null);
const lista = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const decimal = (v: number, casas = 2) => v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

export const segundos = (s: number) => `${decimal(s, 1)} s`;

/** Destino de um retorno do Validation, já com o nome do agente. */
export function destinoDoRetorno(passo: PassoDoAgente): string | null {
  if (passo.agente !== "validation" || passo.saida.aprovado !== false) return null;
  const destino = texto(passo.saida.retornar_para);
  return destino && destino in AGENTES ? AGENTES[destino as PassoDoAgente["agente"]].nome : null;
}

/** Uma linha que diz o que o agente fez. Lê só os campos do contrato da #82 e ignora o resto. */
export function resumirPasso(passo: PassoDoAgente): string {
  const { saida } = passo;
  switch (passo.agente) {
    case "research": {
      const evidencias = lista(saida.evidencias);
      const scores = evidencias.map((e) => numero((e as { score?: unknown })?.score)).filter((s): s is number => s !== null);
      const limite = numero(passo.entrada?.limite);
      const partes = [`${evidencias.length} trecho${evidencias.length === 1 ? "" : "s"} encontrado${evidencias.length === 1 ? "" : "s"}`];
      // O score maior é o primeiro: o Research devolve os trechos já ordenados.
      if (scores.length) partes.push(`melhor score ${decimal(scores[0])}`);
      if (limite !== null) partes.push(`limite de ${limite}`);
      return partes.join(" · ");
    }
    case "analysis": {
      const classificacao = texto(saida.classificacao) as Classificacao | null;
      const confianca = numero(saida.confianca);
      if (!classificacao) return "Não chegou a uma classificação.";
      const rotulo = CLASSIFICACOES[classificacao]?.rotulo ?? classificacao;
      return `Classificou como ${rotulo.toLowerCase()}` + (confianca !== null ? ` · confiança ${decimal(confianca)}` : "");
    }
    case "validation": {
      if (saida.aprovado === true) return "Aprovou a análise.";
      const motivos = lista(saida.motivos).map(texto).filter(Boolean);
      return "Reprovou a análise" + (motivos.length ? `: ${motivos.join("; ")}` : ".");
    }
    case "communication":
      return saida.aprovado_pela_validacao === false ? "Avisou que a verificação não foi conclusiva." : "Escreveu o veredito.";
  }
}

/** Nomes dos agentes na ordem em que rodaram (Research → Analysis → …). */
export function caminhoDosAgentes(historico: PassoDoAgente[]): string[] {
  return historico.map((p) => AGENTES[p.agente].nome);
}
