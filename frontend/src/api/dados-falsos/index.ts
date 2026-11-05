// Dados falsos tipados pelo mesmo contrato do cliente (esquema.d.ts), ligados por VITE_DADOS_FALSOS=1.
// As respostas vêm de gravações do protótipo (scripts/gravar-dados-falsos.mjs), com dinheiro em
// centavos. Servem para as telas funcionarem e para a comparação visual enquanto o backend do
// grupo não tem as rotas. Não calculam nada: uma cesta pedida com outros dados devolve a gravada.
import type { components } from "../esquema";
import cardapio from "./gravacoes/cardapio.json";
import cesta from "./gravacoes/cesta.json";
import configuracoes from "./gravacoes/configuracoes.json";
import creditos from "./gravacoes/creditos.json";
import llm from "./gravacoes/llm.json";
import opcoes from "./gravacoes/opcoes.json";
import precos from "./gravacoes/precos.json";
import proximos from "./gravacoes/proximos.json";
import regioes from "./gravacoes/regioes.json";

type Esquemas = components["schemas"];

// O "cookie" de renovação e a última cesta do servidor falso ficam na sessão do navegador.
const COOKIE = "economia-falso-renovacao";
const ULTIMA = "economia-falso-ultima-cesta";
const lerSessao = (chave: string) => { try { return sessionStorage.getItem(chave); } catch { return null; } };
const gravarSessao = (chave: string, valor: string | null) => {
  try {
    if (valor === null) sessionStorage.removeItem(chave);
    else sessionStorage.setItem(chave, valor);
  } catch { /* navegação privada */ }
};

const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms));

function json(corpo: unknown, status = 200) {
  return new Response(JSON.stringify(corpo), { status, headers: { "Content-Type": "application/json" } });
}

function problema(status: number, title: string, detail?: string) {
  const corpo: Esquemas["Problema"] = { type: "about:blank", title, status, ...(detail ? { detail } : {}) };
  return new Response(JSON.stringify(corpo), { status, headers: { "Content-Type": "application/problem+json" } });
}

function sessao(email: string, nome?: string): Esquemas["Sessao"] {
  gravarSessao(COOKIE, JSON.stringify({ email, nome: nome ?? email.split("@")[0] }));
  return { token_acesso: `falso.${Date.now()}`, expira_em_s: 900, pessoa: { email, nome: nome ?? email.split("@")[0] } };
}

function mercadosProximos(url: URL): Esquemas["MercadosProximos"] {
  const lat = Number(url.searchParams.get("lat")).toFixed(4), lon = Number(url.searchParams.get("lon")).toFixed(4);
  const raio = Number(url.searchParams.get("raio_km"));
  const gravados = proximos as unknown as Record<string, Esquemas["MercadosProximos"]>;
  const exato = gravados[`${lat},${lon},${raio}`];
  if (exato) return exato;
  // Outros raios: o máximo gravado, cortado no raio pedido.
  const maior = gravados[`${lat},${lon},100`] ?? Object.values(gravados)[0];
  return { ...maior, raio_km: raio, mercados: maior.mercados.filter((m) => m.distancia_km <= raio) };
}

const NOTA_DE_EXEMPLO: Esquemas["LeituraDeNota"] = {
  emitente: "Mercado B (exemplo)", cnpj: "00.000.000/0001-00", data: "2026-10-20",
  itens: [
    { descricao: "ARROZ T1 5KG", quantidade: 1, unidade: "UN", valor_unitario: 2490, valor_total: 2490, preco_embalagem: 2490, produto_id: "arroz-5kg", confianca: "alta" },
    { descricao: "FEIJAO CARIOCA 1KG", quantidade: 2, unidade: "UN", valor_unitario: 799, valor_total: 1598, preco_embalagem: 799, produto_id: "feijao-carioca-1kg", confianca: "alta" },
    { descricao: "BANANA PRATA KG", quantidade: 1.2, unidade: "KG", valor_unitario: 549, valor_total: 659, preco_embalagem: null, produto_id: null, confianca: "revisar" },
  ],
};

const RESPOSTAS_DA_CONVERSA: [RegExp, string, Esquemas["BlocosDaResposta"]][] = [
  [/promoç|promoc/i, "Pelo preço por quilo, essa oferta fica abaixo do menor preço normal dos mercados de exemplo, então vale a pena se você for usar o arroz antes de vencer.",
    { agentes: [{ agente: "Cifrão", acao: "comparou o preço por kg" }, { agente: "Mia", acao: "conferiu a conta" }], ferramentas_usadas: ["avaliar_promocao"], fontes: [], aviso: "Preços de exemplo." }],
  [/banana/i, "Banana muito madura vira vitamina, mingau ou bolo. Também dá para congelar em rodelas e usar depois em receitas doces.",
    { agentes: [{ agente: "Miau-ricio", acao: "buscou na base" }, { agente: "Mia", acao: "conferiu a fonte" }], ferramentas_usadas: ["buscar_conhecimento"], fontes: [{ fonte: "Aproveitamento de alimentos (EconoMIA)" }], aviso: null }],
  [/ultraprocess/i, "Ultraprocessados são formulações industriais feitas com muitos ingredientes de uso industrial, como refrigerantes e salgadinhos de pacote. O Guia Alimentar recomenda evitá-los.",
    { agentes: [{ agente: "Miau-ricio", acao: "buscou na base" }, { agente: "Mia", acao: "conferiu a fonte" }], ferramentas_usadas: ["buscar_conhecimento"], fontes: [{ fonte: "Guia Alimentar para a População Brasileira" }], aviso: null }],
];
const RESPOSTA_PADRAO: [string, Esquemas["BlocosDaResposta"]] = [
  "Com esse orçamento dá para montar uma cesta que cumpre as metas. Abra a tela Cesta para ver a lista completa, com os preços de cada mercado.",
  { agentes: [{ agente: "Miau-ricio", acao: "montou a cesta" }, { agente: "Mia", acao: "conferiu a conta" }], ferramentas_usadas: ["montar_cesta"], fontes: [], aviso: "Preços de exemplo." },
];

/** Resposta em SSE, em pedaços, para a tela mostrar o texto chegando aos poucos. */
function streamDaConversa(texto: string): Response {
  const [resposta, blocos] = RESPOSTAS_DA_CONVERSA.find(([padrao]) => padrao.test(texto))?.slice(1) as [string, Esquemas["BlocosDaResposta"]] ?? RESPOSTA_PADRAO;
  const codificador = new TextEncoder();
  const corpo = new ReadableStream<Uint8Array>({
    async start(controle) {
      for (const pedaco of resposta.match(/\S+\s*/g) ?? []) {
        await esperar(25);
        controle.enqueue(codificador.encode(`event: texto\ndata: ${pedaco}\n\n`));
      }
      controle.enqueue(codificador.encode(`event: blocos\ndata: ${JSON.stringify(blocos)}\n\n`));
      controle.enqueue(codificador.encode("event: fim\ndata: {}\n\n"));
      controle.close();
    },
  });
  return new Response(corpo, { headers: { "Content-Type": "text/event-stream" } });
}

export async function responderComDadosFalsos(pedido: Request): Promise<Response> {
  const url = new URL(pedido.url, location.origin);
  const caminho = url.pathname.replace(/^\/api\/v1/, "");
  const rota = `${pedido.method} ${caminho}`;
  await esperar(rota === "POST /cestas" ? 350 : 60);

  // Login e renovação não pedem token.
  if (rota === "POST /auth/login" || rota === "POST /auth/cadastro") {
    const corpo = await pedido.json();
    if (!corpo.email || !corpo.senha) return problema(422, "Dados incompletos", "Informe o e-mail e a senha.");
    if (rota === "POST /auth/cadastro" && corpo.senha.length < 8) return problema(422, "Senha curta", "A senha precisa ter pelo menos 8 caracteres.");
    return json(sessao(corpo.email, corpo.nome), rota === "POST /auth/cadastro" ? 201 : 200);
  }
  if (rota === "POST /auth/renovar") {
    const cookie = lerSessao(COOKIE);
    if (!cookie) return problema(401, "Sessão encerrada");
    const { email, nome } = JSON.parse(cookie);
    return json(sessao(email, nome));
  }
  if (rota === "POST /auth/sair") {
    gravarSessao(COOKIE, null);
    return new Response(null, { status: 204 });
  }
  if (!pedido.headers.get("Authorization")?.startsWith("Bearer ")) return problema(401, "Entre na sua conta");

  switch (rota) {
    case "GET /opcoes": return json(opcoes satisfies Esquemas["Opcoes"]);
    case "GET /precos": return json(precos as Esquemas["TabelaDePrecos"]);
    case "GET /creditos": return json(creditos as Esquemas["CreditoDeFoto"][]);
    case "GET /configuracoes": return json(configuracoes satisfies Esquemas["LimitesDeConfiguracao"]);
    case "GET /regioes": return json(regioes satisfies Esquemas["Regiao"][]);
    case "GET /llm": return json(llm satisfies Esquemas["EstadoDoLlm"]);
    case "POST /cestas": {
      const pedidoDeCesta: Esquemas["PedidoDeCesta"] = await pedido.json();
      const ultima: Esquemas["UltimaCesta"] = { plano: cesta as Esquemas["PlanoDeCesta"], pedido: pedidoDeCesta, quando: new Date().toISOString() };
      gravarSessao(ULTIMA, JSON.stringify(ultima));
      return json(ultima.plano);
    }
    case "GET /cestas/ultima": {
      const ultima = lerSessao(ULTIMA);
      return ultima ? json(JSON.parse(ultima)) : problema(404, "Nenhuma cesta montada ainda");
    }
    case "POST /cardapios": return json(cardapio as Esquemas["RespostaDeCardapio"]);
    case "GET /mercados/proximos": return json(mercadosProximos(url));
    case "GET /mercados/mapa": return json({
      fonte: "OpenStreetMap (dados falsos)",
      supermercados: [
        { nome: "Mercado A", distancia_km: 0.4, tem_precos: true },
        { nome: "Supermercado da Quadra (exemplo)", distancia_km: 1.2, tem_precos: false },
      ],
    } satisfies Esquemas["SupermercadosDoMapa"]);
    case "POST /notas": return json(NOTA_DE_EXEMPLO);
    case "POST /notas/revisao": {
      const revisao: Esquemas["RevisaoDeNota"] = await pedido.json();
      return json({ salvos: revisao.itens.length });
    }
    case "POST /conversas": return json({ id: `conversa-${Date.now()}` }, 201);
    case "GET /notificacoes": return json([] satisfies Esquemas["Notificacao"][]);
  }
  if (pedido.method === "POST" && /^\/conversas\/[^/]+\/mensagens$/.test(caminho)) {
    const { texto } = await pedido.json();
    return streamDaConversa(texto);
  }
  if (pedido.method === "POST" && /^\/notificacoes\/[^/]+\/lida$/.test(caminho)) return new Response(null, { status: 204 });
  return problema(404, "Rota não existe nos dados falsos", rota);
}
