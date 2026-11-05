// Conversa com resposta em streaming SSE. A mensagem vai num POST, e o EventSource do navegador
// só faz GET, então o stream é lido com fetch. É a única chamada à API fora do cliente gerado,
// porque o openapi-fetch não lê streams; o caminho e os tipos vêm do mesmo contrato.
import { renovar, tokenAtual } from "../autenticacao/sessao";
import type { components, paths } from "./esquema";
import { lerProblema, ProblemaDaApi } from "./problemas";
import { transporte } from "./transporte";

export type BlocosDaResposta = components["schemas"]["BlocosDaResposta"];
export type EventoDaConversa =
  | { tipo: "texto"; texto: string }
  | { tipo: "blocos"; blocos: BlocosDaResposta }
  | { tipo: "tarefa"; id: string }
  | { tipo: "erro"; problema: ProblemaDaApi }
  | { tipo: "fim" };

type CaminhoDasMensagens = keyof paths & "/conversas/{id}/mensagens";
const CAMINHO: CaminhoDasMensagens = "/conversas/{id}/mensagens";

/** Lê "event:" e "data:" do stream e entrega um evento por vez. */
export async function* lerEventos(resposta: Response): AsyncGenerator<EventoDaConversa> {
  if (!resposta.body) return;
  const leitor = resposta.body.pipeThrough(new TextDecoderStream()).getReader();
  let resto = "";
  for (;;) {
    const { value, done } = await leitor.read();
    if (done) break;
    resto += value;
    const partes = resto.split("\n\n");
    resto = partes.pop() ?? "";
    for (const parte of partes) {
      let nome = "message", dados = "";
      for (const linha of parte.split("\n")) {
        if (linha.startsWith("event:")) nome = linha.slice(6).trim();
        else if (linha.startsWith("data:")) dados += (dados ? "\n" : "") + linha.slice(5).replace(/^ /, "");
      }
      if (nome === "texto") yield { tipo: "texto", texto: dados };
      else if (nome === "blocos") yield { tipo: "blocos", blocos: JSON.parse(dados) };
      else if (nome === "tarefa") yield { tipo: "tarefa", id: JSON.parse(dados).id };
      else if (nome === "erro") yield { tipo: "erro", problema: new ProblemaDaApi(JSON.parse(dados)) };
      else if (nome === "fim") yield { tipo: "fim" };
    }
  }
}

export async function enviarPedido(conversa: string, texto: string): Promise<AsyncGenerator<EventoDaConversa>> {
  const pedir = () => transporte(`/api/v1${CAMINHO.replace("{id}", encodeURIComponent(conversa))}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream", ...(tokenAtual() ? { Authorization: `Bearer ${tokenAtual()}` } : {}) },
    body: JSON.stringify({ texto }),
  });
  let resposta = await pedir();
  if (resposta.status === 401 && (await renovar())) resposta = await pedir();
  if (!resposta.ok) throw await lerProblema(resposta);
  return lerEventos(resposta);
}
