// EconoMIA — lógica do site. Conversa com a API em /api/...

const reais = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const dataBR = (iso) => iso.split("-").reverse().join("/");
const $ = (seletor) => document.querySelector(seletor);
// O LLM às vezes responde em Markdown; a tela mostra texto simples.
const semMarkdown = (t) => t.replace(/^#{1,6}\s*/gm, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/^\s*[-*]\s+/gm, "• ");

const NOMES_METAS = {
  kcal: ["Energia", "kcal"],
  proteina_g: ["Proteína", "g"],
  fibra_g: ["Fibra", "g"],
  flv_g: ["Frutas e hortaliças", "g"],
};
const NOMES_GRUPOS = {
  cereais: "Cereais e pães", tuberculos: "Raízes e tubérculos", leguminosas: "Feijões",
  proteina_animal: "Carnes e ovos", laticinios: "Leite e queijos", flv: "Frutas e hortaliças",
  oleos: "Óleos", acucar: "Açúcar",
};

let mercados = {};

// Estado lido pela cena 3D e pelas animações (cena3d.js e animacoes.js).
window.economia = { aba: "inicio", cesta: null };

// Foto do alimento (Wikimedia Commons, licença livre; créditos nas Configurações).
function fotoAlimento(id, classe = "foto-alimento") {
  const img = el("img", { src: `img/alimentos/${id}.webp`, alt: "", class: classe, loading: "lazy", width: "240", height: "240" });
  img.addEventListener("error", () => img.replaceWith(el("span", { class: `${classe} sem-foto`, "aria-hidden": "true" }, "🛒")));
  return img;
}
let cestaAtual = null;

function el(tag, attrs = {}, ...filhos) {
  const no = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") no.className = v;
    else no.setAttribute(k, v);
  }
  for (const f of filhos) no.append(f);
  return no;
}

async function api(caminho, opcoes) {
  const r = await fetch(caminho, opcoes);
  const corpo = await r.json();
  if (!r.ok) throw new Error(typeof corpo.detail === "string" ? corpo.detail : "Verifique os campos do formulário.");
  return corpo;
}

// ---------- Navegação ----------
function irParaAba(nome) {
  const trocar = () => mostrarAba(nome);
  if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(trocar);
  else trocar();
}

function mostrarAba(nome) {
  window.economia.aba = nome;
  document.dispatchEvent(new CustomEvent("economia:aba", { detail: { aba: nome } }));
  document.querySelectorAll(".aba").forEach((b) => {
    const ativa = b.dataset.aba === nome;
    b.classList.toggle("ativa", ativa);
    b.setAttribute("aria-selected", ativa);
  });
  document.querySelectorAll(".painel").forEach((p) => (p.hidden = p.id !== `aba-${nome}`));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll(".aba").forEach((b) => b.addEventListener("click", () => irParaAba(b.dataset.aba)));
document.querySelectorAll("[data-ir]").forEach((b) => b.addEventListener("click", () => irParaAba(b.dataset.ir)));
document.querySelectorAll("[data-pergunta]").forEach((b) => b.addEventListener("click", () => {
  irParaAba("chat");
  const campo = $("#form-chat").mensagem;
  campo.value = b.dataset.pergunta;
  campo.focus();
}));

// Contador de pessoas (− / +)
// Setas dos valores em R$: andam em passos redondos, e a partir de 799,92 vão a 800 ou 790.
document.querySelectorAll(".moeda-seta").forEach((b) => b.addEventListener("click", () => {
  const campo = b.closest(".moeda").querySelector("input");
  const passo = Number(b.dataset.passo), tamanho = Math.abs(passo), atual = Number(campo.value) || 0;
  const proximo = passo > 0 ? Math.floor(atual / tamanho + 1e-9) * tamanho + tamanho : Math.ceil(atual / tamanho - 1e-9) * tamanho - tamanho;
  campo.value = Math.max(Number(campo.min) || 0, proximo);
  campo.dispatchEvent(new Event("input", { bubbles: true }));
  campo.dispatchEvent(new Event("change", { bubbles: true }));
}));

document.querySelectorAll(".contador-botao").forEach((b) => b.addEventListener("click", () => {
  const campo = $("#form-cesta").pessoas;
  campo.value = Math.min(20, Math.max(1, Number(campo.value || 1) + Number(b.dataset.passo)));
}));

// ---------- Mascote e dica do dia ----------
const DICAS = [
  ["Compare o preço por quilo, não o da embalagem: o pacote maior nem sempre compensa.", "Critérios da EconoMIA"],
  ["Arroz com feijão é uma combinação completa: as proteínas dos dois se complementam.", "Guia Alimentar para a População Brasileira"],
  ["Prefira legumes, verduras e frutas da estação e cultivados localmente.", "Guia Alimentar para a População Brasileira"],
  ["Ovos são acessíveis e relativamente baratos, e podem substituir a carne em várias refeições.", "Guia Alimentar para a População Brasileira"],
  ["Banana muito madura vira vitamina, mingau ou bolo. Não precisa ir para o lixo!", "Aproveitamento de alimentos (EconoMIA)"],
  ["Planeje as refeições antes de ir ao mercado: faça a lista e defina o orçamento antes de sair.", "Critérios da EconoMIA"],
  ["Prefira alimentos in natura ou minimamente processados aos ultraprocessados.", "Guia Alimentar: a regra de ouro"],
];

function mostrarDica() {
  const [texto, fonte] = DICAS[new Date().getDate() % DICAS.length];
  $("#dica-texto").textContent = texto;
  $("#dica-fonte").textContent = "Fonte: " + fonte;
}

function falarMascote(rosto, frase) {
  $("#mascote").textContent = rosto;
  $("#balao").textContent = frase;
}

function anel(pct, cor) {
  const a = el("div", { class: "anel", style: `--pct:${Math.min(Math.max(pct, 0), 100)};--cor:${cor}` });
  return a;
}

// Última cesta (tópico 20): guardada só neste aparelho, para o Início continuar preenchido.
const CHAVE_CESTA = "economia-ultima-cesta";

function guardarUltimaCesta(plano, pedido) {
  try {
    localStorage.setItem(CHAVE_CESTA, JSON.stringify({ plano, pedido, quando: new Date().toISOString() }));
  } catch { /* navegação privada: o app segue funcionando sem guardar */ }
}

function restaurarUltimaCesta() {
  try {
    const salvo = JSON.parse(localStorage.getItem(CHAVE_CESTA));
    // Preço muda: mostrar uma cesta antiga como se fosse atual enganaria.
    if (!salvo?.plano?.recomendacao || !salvo.plano.cesta_recomendada.mercados.every((m) => mercados[m])) return;
    mostrarPlano(salvo.plano, { em_casa: [], ...salvo.pedido }, false);
    atualizarInicio(salvo.plano, salvo.pedido);
    const dias = Math.floor((Date.now() - new Date(salvo.quando)) / 86400000);
    if (dias >= 1) falarMascote("📅", `Sua última cesta é de ${new Date(salvo.quando).toLocaleDateString("pt-BR")}. Os preços podem ter mudado: monte de novo para conferir.`);
  } catch { /* dado guardado inválido: começa do zero */ }
}

function atualizarInicio(plano, pedido) {
  if (!plano.recomendacao) {
    falarMascote("😿", pedido.orcamento && plano.minimo_necessario
      ? `Com ${reais(pedido.orcamento)} não dá para cumprir as metas. Precisaria de ${reais(plano.minimo_necessario)}. Vamos tentar um período menor?`
      : "Com essas escolhas não dá para cumprir as metas. Vamos rever as restrições ou os alimentos que saíram da cesta?");
    $("#inicio-resumo").hidden = true;
    return;
  }
  const cesta = plano.cesta_recomendada;
  const gasto = cesta.custo_total + (plano.recomendacao === "dois" ? plano.custo_deslocamento : 0);
  if (pedido.orcamento) {
    const sobra = pedido.orcamento - gasto;
    falarMascote("🎉", `Sua cesta coube no orçamento! Sobraram ${reais(sobra)} e todas as metas nutricionais foram cumpridas.`);
    const pct = Math.round((gasto / pedido.orcamento) * 100);
    const area = $("#anel-orcamento");
    area.style.setProperty("--pct", Math.min(pct, 100));
    area.style.setProperty("--cor", "var(--marca)");
    $("#anel-orcamento-valor").textContent = `${pct}%`;
    $("#inicio-legenda").replaceChildren(
      el("b", {}, reais(gasto)), `de ${reais(pedido.orcamento)} · ${nomesMercados(cesta.mercados)}`,
    );
  } else {
    falarMascote("✨", `Sua cesta custa ${reais(gasto)} e cumpre todas as metas nutricionais.`);
    $("#anel-orcamento").style.setProperty("--pct", 100);
    $("#anel-orcamento-valor").textContent = reais(gasto);
    $("#inicio-legenda").replaceChildren(el("b", {}, "Sem limite"), nomesMercados(cesta.mercados));
  }
  $("#inicio-metas").replaceChildren(...aneisMetas(cesta));
  $("#inicio-resumo").hidden = false;
}

// ---------- Início ----------
async function iniciar() {
  const opcoes = await api("/api/opcoes");
  mercados = Object.fromEntries(opcoes.mercados.map((m) => [m.id, m]));

  if (opcoes.aviso_dados) {
    const aviso = $("#aviso-dados");
    aviso.textContent = "⚠️ Preços de exemplo: os mercados e valores ainda são fictícios.";
    aviso.title = opcoes.aviso_dados;
    aviso.hidden = false;
  }

  nomesAlimentos = Object.fromEntries(opcoes.alimentos.map((a) => [a.id, a.nome]));
  $("#em-casa-alimento").replaceChildren(...opcoes.alimentos.map((a) => el("option", { value: a.id }, a.nome)));

  const lista = $("#lista-restricoes");
  for (const r of opcoes.restricoes) {
    lista.append(el("label", { class: "chip" }, el("input", { type: "checkbox", name: "restricoes", value: r.id }), r.nome));
  }

  restaurarUltimaCesta();
  mostrarDica();
  carregarPrecos();
  carregarStatusLLM();
  aplicarConfig();
  await carregarLimites();
  carregarCreditos();
  carregarRegioes();
}

// ---------- Cesta ----------
// Alimentos que o usuário tirou da cesta e o que já tem em casa (tópico 19).
const semAlimentos = new Map();
const emCasa = new Map();
let nomesAlimentos = {};

function chipRemovivel(texto, rotulo, aoRemover) {
  const b = el("button", { type: "button", class: "chip chip-remover", "aria-label": rotulo }, `${texto} ✕`);
  b.addEventListener("click", aoRemover);
  return b;
}

function mostrarAjustesCesta() {
  $("#sem-alimentos-area").hidden = semAlimentos.size === 0;
  $("#sem-alimentos-lista").replaceChildren(...[...semAlimentos].map(([id, nome]) =>
    chipRemovivel(nome, `Devolver ${nome} à cesta`, () => {
      semAlimentos.delete(id);
      mostrarAjustesCesta();
      $("#form-cesta").requestSubmit();
    })));
  $("#em-casa-lista").replaceChildren(...[...emCasa].map(([id, kg]) =>
    chipRemovivel(`${String(kg).replace(".", ",")} kg de ${nomesAlimentos[id]}`, `Remover ${nomesAlimentos[id]} de casa`, () => {
      emCasa.delete(id);
      mostrarAjustesCesta();
    })));
}

$("#em-casa-adicionar").addEventListener("click", () => {
  const kg = Number($("#em-casa-kg").value);
  if (!(kg > 0 && kg <= 200)) return;
  const id = $("#em-casa-alimento").value;
  emCasa.set(id, kg);
  mostrarAjustesCesta();
});

function trocarAlimento(id, nome) {
  semAlimentos.set(id, nome);
  mostrarAjustesCesta();
  $("#form-cesta").requestSubmit();
  $("#form-cesta").scrollIntoView({ behavior: "smooth", block: "end" });
}

$("#form-cesta").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = new FormData(evento.target);
  const orcamento = form.get("orcamento");
  const pedido = {
    orcamento: orcamento ? Number(orcamento) : null,
    pessoas: Number(form.get("pessoas")),
    periodo: form.get("periodo"),
    restricoes: form.getAll("restricoes"),
    custo_deslocamento: Number(form.get("custo_deslocamento") || 0),
  };
  if (mercadosPerto) pedido.mercados = mercadosPerto.ids;
  pedido.sem_alimentos = [...semAlimentos.keys()];
  pedido.em_casa = [...emCasa.entries()].map(([alimento, kg]) => ({ alimento, gramas: Math.round(kg * 1000) }));

  const botao = evento.target.querySelector("button[type=submit]");
  botao.disabled = true;
  $("#carregando").hidden = false;
  $("#erro").hidden = true;
  $("#resultado").hidden = true;
  try {
    const plano = await api("/api/cesta", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pedido),
    });
    mostrarPlano(plano, pedido);
    atualizarInicio(plano, pedido);
    guardarUltimaCesta(plano, pedido);
  } catch (e) {
    $("#erro").textContent = "Não foi possível montar a cesta: " + e.message;
    $("#erro").hidden = false;
  } finally {
    botao.disabled = false;
    $("#carregando").hidden = true;
  }
});

function nomesMercados(ids) {
  return ids.map((id) => mercados[id]?.nome ?? id).join(" + ");
}

function cartaoOpcao(titulo, cesta, recomendada, extra) {
  const c = el("div", { class: "cartao opcao" + (recomendada ? " recomendada" : "") });
  if (recomendada) c.append(el("span", { class: "selo" }, "Recomendada"));
  c.append(el("div", { class: "titulo" }, titulo));
  if (!cesta) {
    c.append(el("div", { class: "valor" }, "—"), el("div", { class: "detalhe" }, "Sem opção dentro do orçamento"));
    return c;
  }
  c.append(
    el("div", { class: "valor" }, reais(cesta.custo_total)),
    el("div", { class: "detalhe" }, nomesMercados(cesta.mercados) + (extra ? ` · ${extra}` : "")),
  );
  return c;
}

function mostrarPlano(plano, pedido, rolar = true) {
  const resumo = $("#resumo");
  resumo.replaceChildren();
  $("#explicacao").replaceChildren(...plano.explicacao.map((f) => el("li", {}, f)));

  const areaCardapio = $("#botao-cardapio").closest(".cartao");
  areaCardapio.hidden = !plano.recomendacao;
  if (!plano.recomendacao) {
    avisarCesta([], false, false);
    resumo.append(cartaoOpcao("Orçamento informado", null, false));
    $("#metas").replaceChildren();
    $("#itens").replaceChildren();
    cestaAtual = null;
    $("#resultado").hidden = false;
    return;
  }

  resumo.append(cartaoOpcao("Em um só mercado", plano.um_mercado, plano.recomendacao === "um"));
  const extra = plano.dois_mercados && pedido.custo_deslocamento > 0
    ? `+ ${reais(pedido.custo_deslocamento)} de deslocamento`
    : "";
  resumo.append(cartaoOpcao("Dividindo em dois mercados", plano.dois_mercados, plano.recomendacao === "dois", extra));

  const cesta = plano.cesta_recomendada;
  resumo.append(
    el("div", { class: "cartao opcao largura-toda" },
      el("div", { class: "titulo" }, "Custo por 1.000 kcal"),
      el("div", { class: "valor" }, reais(cesta.custo_por_1000_kcal)),
      el("div", { class: "detalhe" }, `${reais(cesta.custo_por_g_proteina)} por grama de proteína`),
    ),
  );

  mostrarMetas(cesta);
  mostrarItens(cesta);
  const casa = pedido.em_casa.map((i) => i.alimento).filter((id) => !cesta.itens.some((x) => x.alimento_id === id));
  cestaAtual = { alimentos: [...new Set([...cesta.itens.map((i) => i.alimento_id), ...casa])], restricoes: pedido.restricoes };
  const unicos = [...new Map([...cesta.itens.map((i) => [i.alimento_id, i.alimento.split(" (")[0]]), ...casa.map((id) => [id, nomesAlimentos[id]])]).entries()];
  $("#ingredientes-cesta").replaceChildren(...unicos.map(([id, nome]) => el("span", { class: "ingrediente" }, fotoAlimento(id, "foto-ingrediente"), nome)));
  $("#cardapio").replaceChildren();
  $("#resultado").hidden = false;
  if (rolar) $("#resultado").scrollIntoView({ behavior: "smooth", block: "start" });
  const coube = !pedido.orcamento || plano.cesta_recomendada.dentro_do_orcamento;
  avisarCesta(plano.cesta_recomendada.itens.flatMap((i) => Array(Math.min(i.quantidade, 2)).fill(i.alimento_id)), rolar, coube);
}

function avisarCesta(itens, animar, coube) {
  window.economia.cesta = { itens, coube };
  document.dispatchEvent(new CustomEvent("economia:cesta", { detail: { itens, animar, coube } }));
}

const CORES_METAS = { kcal: "var(--marca)", proteina_g: "var(--roxo)", fibra_g: "var(--azul)", flv_g: "var(--verde)" };

function aneisMetas(cesta) {
  return Object.entries(NOMES_METAS).map(([chave, [nome]]) => {
    const pct = Math.round((cesta.obtido[chave] / cesta.metas[chave]) * 100);
    const a = anel(pct, CORES_METAS[chave]);
    a.append(el("div", { class: "anel-centro" }, el("b", {}, `${pct}%`)));
    return el("div", { class: "mini-anel" }, a, el("span", {}, nome));
  });
}

function mostrarMetas(cesta) {
  $("#metas").replaceChildren(...aneisMetas(cesta));
}

const EMOJI_GRUPOS = {
  cereais: "🍚", tuberculos: "🥔", leguminosas: "🫘", proteina_animal: "🍗",
  laticinios: "🥛", flv: "🥕", oleos: "🫒", acucar: "🍬",
};

function mostrarItens(cesta) {
  const area = $("#itens");
  area.replaceChildren();
  for (const id of cesta.mercados) {
    const itens = cesta.itens.filter((i) => i.mercado_id === id);
    area.append(el("h3", { class: "mercado-titulo" }, el("span", {}, `🏪 ${mercados[id].nome}`), el("span", {}, reais(cesta.custo_por_mercado[id]))));
    area.append(el("ul", { class: "itens-lista" }, ...itens.map((i) => el("li", { class: "item" },
      fotoAlimento(i.alimento_id, "item-foto"),
      el("span", {},
        el("span", { class: "item-nome" }, i.produto),
        el("span", { class: "item-detalhe" }, `${i.quantidade} × ${reais(i.preco_unitario)} · ${reais(i.preco_kg)}/kg`),
        el("span", { class: "item-detalhe" }, `Preço de ${dataBR(i.data_preco)} · fonte: ${i.fonte_preco}`),
        botaoTrocar(i),
      ),
      el("span", { class: "item-valor" }, reais(i.subtotal), el("small", {}, NOMES_GRUPOS[i.grupo] ?? i.grupo)),
    ))));
  }
}

function botaoTrocar(item) {
  const nome = item.alimento.split(" (")[0];
  const b = el("button", { type: "button", class: "item-trocar", "aria-label": `Trocar ${nome} por outra opção` }, "🔄 Trocar");
  b.addEventListener("click", () => trocarAlimento(item.alimento_id, nome));
  return b;
}

function textoEtapas(etapas) {
  return (etapas ?? []).map((e) => `${e.agente}: ${e.acao}`).join(" → ");
}

function blocosCardapio(r) {
  const plano = r.dados?.cardapio;
  if (!plano) return [semMarkdown(r.resposta)];
  const blocos = [];
  plano.dias.forEach((refeicoes, n) => {
    blocos.push(el("section", { class: "cardapio-dia" },
      el("h4", {}, `Dia ${n + 1}`),
      ...refeicoes.map((x) => el("div", { class: "cardapio-refeicao" },
        el("span", { class: "cardapio-tipo" }, x.titulo),
        el("strong", {}, r.dados.nomes_receitas[x.receita]),
        el("span", { class: "cardapio-fotos" }, ...x.alimentos.slice(0, 5).map((a) => fotoAlimento(a, "foto-ingrediente"))),
        el("span", { class: "item-detalhe" }, x.ingredientes.join(", ")),
        el("span", { class: "cardapio-preparo" }, x.preparo),
      )),
    ));
  });
  if (plano.nao_usados.length) blocos.push(el("p", { class: "nota" }, `Ficaram para os outros dias: ${plano.nao_usados.join(", ")}.`));
  return blocos;
}

$("#botao-cardapio").addEventListener("click", async (evento) => {
  if (!cestaAtual) return;
  const botao = evento.target;
  const area = $("#cardapio");
  botao.disabled = true;
  area.replaceChildren("Montando o cardápio…");
  try {
    const r = await api("/api/cardapio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...cestaAtual, dias: Number($("#cardapio-dias").value) }),
    });
    area.replaceChildren(...blocosCardapio(r), el("span", { class: "meta-msg" }, textoEtapas(r.etapas)));
  } catch (e) {
    area.replaceChildren("Não foi possível montar o cardápio: " + e.message);
  } finally {
    botao.disabled = false;
  }
});

// ---------- Configurações ----------
// Preferências do usuário, guardadas só neste navegador (localStorage).
// A localização (GPS) nunca é guardada; só a região padrão, se a pessoa escolher.
const CHAVE_CONFIG = "economia.config";
const CONFIG_PADRAO = { raio_km: 10, custo_por_km: 0.65, ordem: "custo_beneficio", tema: "auto", regiao: "" };
const LIMITES = { raio_min: 1, raio_max: 100 };
let config = carregarConfig();

function carregarConfig() {
  try {
    return { ...CONFIG_PADRAO, ...JSON.parse(localStorage.getItem(CHAVE_CONFIG) || "{}") };
  } catch {
    return { ...CONFIG_PADRAO };
  }
}

function salvarConfig(mudancas) {
  config = { ...config, ...mudancas };
  try {
    localStorage.setItem(CHAVE_CONFIG, JSON.stringify(config));
  } catch {
    /* navegação privada: vale só nesta sessão */
  }
  aplicarConfig();
}

const km = (v) => `${String(v).replace(".", ",")} km`;

function aplicarConfig() {
  if (config.tema === "auto") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = config.tema;

  const raio = $("#cfg-raio");
  raio.value = config.raio_km;
  raio.style.setProperty("--progresso", `${((config.raio_km - raio.min) / (raio.max - raio.min)) * 100}%`);
  $("#cfg-raio-valor").textContent = config.raio_km;
  document.querySelectorAll("#cfg-raio-atalhos .chip").forEach((c) => c.classList.toggle("ativo", Number(c.dataset.km) === config.raio_km));
  $("#raio-atual").textContent = km(config.raio_km);

  const custo = $("#cfg-custo-km");
  custo.value = config.custo_por_km;
  custo.style.setProperty("--progresso", `${((config.custo_por_km - custo.min) / (custo.max - custo.min)) * 100}%`);
  $("#cfg-custo-valor").textContent = reais(config.custo_por_km);

  document.querySelectorAll('input[name="cfg-ordem"], input[name="ordem-perto"]').forEach((i) => (i.checked = i.value === config.ordem));
  document.querySelectorAll('input[name="cfg-tema"]').forEach((i) => (i.checked = i.value === config.tema));
  $("#cfg-regiao").value = config.regiao;
  desenharRadar();
}

async function carregarCreditos() {
  try {
    const lista = await api("/api/creditos");
    $("#lista-creditos").replaceChildren(...lista.map((c) => el("li", {},
      fotoAlimento(c.alimento_id, "foto-mini"),
      el("span", {},
        el("b", {}, c.alimento.split(" (")[0]),
        el("small", {}, el("a", { href: c.pagina, target: "_blank", rel: "noopener" }, c.titulo), ` · ${c.autor} · `,
          c.licenca_url ? el("a", { href: c.licenca_url, target: "_blank", rel: "noopener" }, c.licenca) : c.licenca),
      ),
    )));
  } catch {
    $("#lista-creditos").replaceChildren("Não foi possível carregar os créditos.");
  }
}

async function carregarLimites() {
  try {
    const c = await api("/api/configuracoes");
    LIMITES.raio_min = c.raio_km.minimo;
    LIMITES.raio_max = c.raio_km.maximo;
    $("#cfg-raio").min = c.raio_km.minimo;
    $("#cfg-raio").max = c.raio_km.maximo;
  } catch {
    /* usa os limites padrão */
  }
}

// Raio: o radar redesenha enquanto arrasta; a busca roda quando solta.
$("#cfg-raio").addEventListener("input", (e) => {
  config.raio_km = Number(e.target.value);
  aplicarConfig();
});
$("#cfg-raio").addEventListener("change", (e) => {
  salvarConfig({ raio_km: Number(e.target.value) });
  rebuscar();
});
document.querySelectorAll("#cfg-raio-atalhos .chip").forEach((c) => c.addEventListener("click", () => {
  salvarConfig({ raio_km: Number(c.dataset.km) });
  rebuscar();
}));
$("#cfg-custo-km").addEventListener("input", (e) => {
  config.custo_por_km = Number(e.target.value);
  aplicarConfig();
});
$("#cfg-custo-km").addEventListener("change", (e) => {
  salvarConfig({ custo_por_km: Number(e.target.value) });
  rebuscar();
});
document.querySelectorAll('input[name="cfg-ordem"], input[name="ordem-perto"]').forEach((i) => i.addEventListener("change", () => {
  salvarConfig({ ordem: i.value });
  if (ultimoPerto) mostrarMercados(ultimoPerto);
}));
document.querySelectorAll('input[name="cfg-tema"]').forEach((i) => i.addEventListener("change", () => salvarConfig({ tema: i.value })));
$("#cfg-regiao").addEventListener("change", (e) => {
  salvarConfig({ regiao: e.target.value });
  carregarRadar();
});
$("#cfg-apagar").addEventListener("click", () => {
  try {
    localStorage.clear();
  } catch { /* nada guardado */ }
  location.reload();
});

$("#cfg-restaurar").addEventListener("click", () => {
  config = { ...CONFIG_PADRAO };
  salvarConfig({});
  carregarRadar();
  rebuscar();
});

// ---------- Radar (prévia do raio) ----------
let todosMercados = null;   // mercados com distância e direção a partir do ponto de partida (até 100 km)

function pontoDePartida() {
  if (posicao) return posicao;
  if (config.regiao) {
    const [lat, lon] = config.regiao.split(",").map(Number);
    return { lat, lon, origem: $("#cfg-regiao").selectedOptions[0]?.textContent ?? "região padrão" };
  }
  return null;
}

async function carregarRadar() {
  const p = pontoDePartida();
  todosMercados = null;
  if (p) {
    try {
      const r = await api(`/api/proximos?lat=${p.lat.toFixed(4)}&lon=${p.lon.toFixed(4)}&raio_km=${LIMITES.raio_max}&custo_por_km=${config.custo_por_km}`);
      todosMercados = r.mercados;
    } catch {
      /* radar fica vazio */
    }
  }
  desenharRadar();
}

function svg(tag, attrs = {}) {
  const no = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) no.setAttribute(k, v);
  return no;
}

function desenharRadar() {
  const area = $("#radar");
  const p = pontoDePartida();
  area.replaceChildren();
  const c = 120;
  const maxR = 104;
  const longe = Math.max(config.raio_km, ...(todosMercados ?? []).map((m) => m.distancia_km)) * 1.08;
  const r = Math.max(10, (config.raio_km / longe) * maxR);

  area.append(
    svg("circle", { cx: c, cy: c, r: maxR + 8, fill: "var(--fundo)" }),
    ...[0.33, 0.66, 1].map((f) => svg("circle", { cx: c, cy: c, r: maxR * f, fill: "none", stroke: "var(--borda)", "stroke-dasharray": "3 4" })),
    svg("circle", { cx: c, cy: c, r, fill: "color-mix(in srgb, var(--marca) 18%, transparent)", stroke: "var(--marca)", "stroke-width": 2 }),
  );
  let dentro = 0;
  for (const m of todosMercados ?? []) {
    const d = (m.distancia_km / longe) * maxR;
    const ang = ((m.rumo_graus - 90) * Math.PI) / 180;
    const noRaio = m.distancia_km <= config.raio_km;
    if (noRaio) dentro += 1;
    const ponto = svg("circle", {
      cx: c + d * Math.cos(ang), cy: c + d * Math.sin(ang), r: 6,
      fill: noRaio ? "var(--marca)" : "var(--suave)", stroke: "var(--cartao)", "stroke-width": 2,
    });
    const titulo = svg("title");
    titulo.textContent = `${m.nome} — ${km(m.distancia_km)}`;
    ponto.append(titulo);
    area.append(ponto);
  }
  area.append(svg("circle", { cx: c, cy: c, r: 7, fill: "var(--azul)", stroke: "var(--cartao)", "stroke-width": 3 }));

  if (!p) {
    $("#radar-resumo").textContent = `Raio de ${km(config.raio_km)}`;
    $("#radar-ponto").textContent = "Escolha um ponto de partida (localização ou região) para ver quantos mercados ficam no raio.";
    return;
  }
  const total = todosMercados?.length ?? 0;
  const fora = (todosMercados ?? []).filter((m) => m.distancia_km > config.raio_km).sort((a, b) => a.distancia_km - b.distancia_km);
  $("#radar-resumo").textContent = `${dentro} de ${total} mercados com preço ficam no raio de ${km(config.raio_km)}`;
  $("#radar-ponto").textContent = `Medido a partir de: ${p.origem}.` + (fora.length ? ` O próximo mercado fora do raio fica a ${km(fora[0].distancia_km)}.` : "");
}

// ---------- Perto de mim ----------
let posicao = null;          // {lat, lon, origem} só na memória da página
let mercadosPerto = null;    // ids usados ao montar a cesta
let ultimoPerto = null;

const NOMES_GRUPOS_PROTEINA = { proteina_animal: "Carnes e ovos", laticinios: "Leite e queijos", leguminosas: "Feijões" };
const NOMES_SELOS = { mais_perto: "📍 Mais perto", melhor_preco: "💰 Menor preço", melhor_custo_beneficio: "⭐ Melhor custo-benefício" };

async function carregarRegioes() {
  const regioes = await api("/api/regioes");
  const opcoes = () => regioes.map((r) => el("option", { value: `${r.lat},${r.lon}` }, r.nome));
  $("#regiao").append(...opcoes());
  $("#cfg-regiao").append(...opcoes());
  $("#cfg-regiao").value = config.regiao;
  carregarRadar();
}

$("#botao-localizacao").addEventListener("click", () => {
  if (!navigator.geolocation) {
    $("#status-perto").textContent = "Seu navegador não permite localização. Escolha a região.";
    return;
  }
  $("#status-perto").textContent = "Pedindo permissão de localização…";
  navigator.geolocation.getCurrentPosition(
    (p) => buscarPerto(p.coords.latitude, p.coords.longitude, "sua localização"),
    () => ($("#status-perto").textContent = "Não foi possível pegar a localização. Escolha a região."),
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
  );
});

$("#regiao").addEventListener("change", (e) => {
  if (!e.target.value) return;
  const [lat, lon] = e.target.value.split(",").map(Number);
  buscarPerto(lat, lon, e.target.selectedOptions[0].textContent);
});

// Ao abrir o Perto de mim sem posição, usa a região padrão das Configurações.
document.querySelectorAll('[data-aba="perto"], [data-ir="perto"]').forEach((b) => b.addEventListener("click", () => {
  if (!posicao && config.regiao) {
    $("#regiao").value = config.regiao;
    const [lat, lon] = config.regiao.split(",").map(Number);
    buscarPerto(lat, lon, $("#regiao").selectedOptions[0]?.textContent ?? "região padrão");
  }
}));

function rebuscar() {
  if (posicao) buscarPerto(posicao.lat, posicao.lon, posicao.origem);
}

async function buscarPerto(lat, lon, origem) {
  posicao = { lat, lon, origem };
  const raio = config.raio_km;
  $("#status-perto").textContent = `Buscando mercados a até ${km(raio)} de ${origem}…`;
  try {
    const r = await api(`/api/proximos?lat=${lat.toFixed(4)}&lon=${lon.toFixed(4)}&raio_km=${raio}&custo_por_km=${config.custo_por_km}`);
    mostrarPerto(r, raio, origem);
    carregarRadar();
  } catch (e) {
    $("#status-perto").textContent = "Erro: " + e.message;
  }
}

function ordenarMercados(lista) {
  const chave = {
    distancia: (m) => m.distancia_km,
    preco: (m) => m.carrinho_proteinas ?? Infinity,
    custo_beneficio: (m) => m.custo_real ?? Infinity,
  }[config.ordem];
  return [...lista].sort((a, b) => chave(a) - chave(b) || a.distancia_km - b.distancia_km);
}

function mostrarMercados(r) {
  const destaque = { distancia: "mais_perto", preco: "melhor_preco", custo_beneficio: "melhor_custo_beneficio" }[config.ordem];
  $("#lista-mercados").replaceChildren(...ordenarMercados(r.mercados).map((m) => {
    const valor = config.ordem === "distancia"
      ? el("div", { class: "mercado-valor" }, km(m.distancia_km), el("small", {}, "de distância"))
      : config.ordem === "preco"
        ? el("div", { class: "mercado-valor" }, m.carrinho_proteinas != null ? reais(m.carrinho_proteinas) : "—", el("small", {}, "carrinho de proteínas"))
        : el("div", { class: "mercado-valor" }, m.custo_real != null ? reais(m.custo_real) : "—", el("small", {}, "custo real"));
    return el("article", { class: "mercado" + (m.selos.includes(destaque) ? " destaque" : "") },
      el("div", { class: "mercado-nome" }, m.nome),
      valor,
      el("div", { class: "mercado-local" }, m.regiao),
      el("div", { class: "mercado-numeros" },
        el("span", {}, "📍 ", el("b", {}, km(m.distancia_km))),
        el("span", {}, "🚗 ida e volta ", el("b", {}, reais(m.custo_ida_volta))),
        el("span", {}, "🛒 proteínas ", el("b", {}, m.carrinho_proteinas != null ? reais(m.carrinho_proteinas) : "—")),
        el("span", {}, "= ", el("b", {}, m.custo_real != null ? reais(m.custo_real) : "—")),
      ),
      m.selos.length ? el("div", { class: "selos" }, ...m.selos.map((s) => el("span", { class: `selo-mercado selo-${s}` }, NOMES_SELOS[s]))) : "",
    );
  }));
}

function mostrarPerto(r, raio, origem) {
  ultimoPerto = r;
  $("#lista-osm").replaceChildren();
  if (!r.mercados.length) {
    const dica = r.mais_proximo_fora_do_raio_km
      ? ` O mercado mais próximo com preços fica a ${km(r.mais_proximo_fora_do_raio_km)}: aumente o raio nas Configurações.`
      : " Envie um cupom de um mercado da sua região para ele aparecer aqui.";
    $("#status-perto").textContent = `Nenhum mercado com preços a até ${km(raio)} de ${origem}.` + dica;
    $("#resultado-perto").hidden = true;
    mercadosPerto = null;
    return;
  }
  $("#status-perto").textContent = `${r.mercados.length} de ${r.total_com_localizacao} mercados com preços ficam a até ${km(raio)} de ${origem}.`;
  mercadosPerto = { ids: r.mercados.map((m) => m.id), deslocamento: r.custo_segundo_mercado };
  mostrarMercados(r);

  const p = r.proteinas;
  const nome = (id) => mercados[id]?.nome ?? id;
  const resumo = [];
  if (p.carrinho.melhor_mercado) {
    resumo.push(el("div", { class: "cartao opcao recomendada" },
      el("span", { class: "selo" }, "Melhor para proteínas"),
      el("div", { class: "titulo" }, `1 kg de cada: ${p.carrinho.itens.join(", ")}`),
      el("div", { class: "valor" }, nome(p.carrinho.melhor_mercado)),
      el("div", { class: "detalhe" }, Object.entries(p.carrinho.total_por_mercado).map(([m, v]) => `${nome(m)}: ${reais(v)}`).join(" · ")),
    ));
  }
  const maisBarata = p.alimentos[0];
  if (maisBarata) {
    resumo.push(el("div", { class: "cartao opcao com-foto" },
      fotoAlimento(maisBarata.alimento_id, "foto-destaque"),
      el("div", { class: "titulo" }, "Proteína mais barata"),
      el("div", { class: "valor" }, maisBarata.alimento),
      el("div", { class: "detalhe" }, `${reais(maisBarata.precos[maisBarata.melhor_mercado].custo_100g_proteina)} por 100 g de proteína no ${nome(maisBarata.melhor_mercado)}`),
    ));
  }
  $("#resumo-proteinas").replaceChildren(...resumo);

  const ids = mercadosPerto.ids;
  $("#tabela-proteinas").replaceChildren(
    el("thead", {}, el("tr", {}, el("th", {}, "Alimento"), ...ids.map((id) => el("th", { class: "num" }, nome(id))), el("th", { class: "num" }, "Economia no melhor"))),
    el("tbody", {}, ...p.alimentos.map((a) => el("tr", {},
      el("td", {}, el("div", { class: "celula-produto" }, fotoAlimento(a.alimento_id, "foto-mini"),
        el("span", {}, a.alimento, el("span", { class: "fonte" }, `${NOMES_GRUPOS_PROTEINA[a.grupo]} · ${String(a.proteina_100g).replace(".", ",")} g de proteína/100 g`)))),
      ...ids.map((id) => {
        const v = a.precos[id];
        if (!v) return el("td", { class: "num" }, "—");
        return el("td", { class: "num" + (id === a.melhor_mercado && Object.keys(a.precos).length > 1 ? " melhor" : "") },
          `${reais(v.preco_kg)}/kg`,
          el("span", { class: "fonte" }, `${reais(v.custo_100g_proteina)} por 100 g de proteína · ${dataBR(v.data)} · ${v.fonte}`));
      }),
      el("td", { class: "num" }, a.economia_vs_mais_caro_pct > 0 ? `${String(a.economia_vs_mais_caro_pct).replace(".", ",")}%` : "—"),
    ))),
  );
  $("#resultado-perto").hidden = false;
}

$("#botao-cesta-perto").addEventListener("click", () => {
  if (!mercadosPerto) return;
  $("#form-cesta").custo_deslocamento.value = mercadosPerto.deslocamento.toFixed(2);
  irParaAba("cesta");
  $("#filtro-mercados").textContent = `Usando só os mercados no seu raio de ${km(config.raio_km)}: ${mercadosPerto.ids.map((id) => mercados[id]?.nome ?? id).join(", ")}. `;
  $("#filtro-mercados").append(el("button", { type: "button", class: "sugestao", id: "limpar-filtro" }, "usar todos"));
  $("#filtro-mercados").hidden = false;
  $("#limpar-filtro").addEventListener("click", () => {
    mercadosPerto = null;
    $("#filtro-mercados").hidden = true;
  });
});

$("#botao-osm").addEventListener("click", async (evento) => {
  if (!posicao) return;
  const botao = evento.target;
  botao.disabled = true;
  $("#lista-osm").replaceChildren("Consultando o OpenStreetMap…");
  try {
    const raio = Math.min(config.raio_km, 10);
    const r = await api(`/api/osm?lat=${posicao.lat.toFixed(2)}&lon=${posicao.lon.toFixed(2)}&raio_km=${raio}`);
    if (!r.supermercados.length) {
      $("#lista-osm").replaceChildren("Nenhum supermercado encontrado no mapa nessa área.");
      return;
    }
    $("#lista-osm").replaceChildren(
      el("p", { class: "nota" }, config.raio_km > 10 ? "Mostrando até 10 km (limite do mapa gratuito)." : ""),
      el("ul", { class: "explicacao" }, ...r.supermercados.slice(0, 20).map((m) => el("li", {},
        `${m.nome} — ${km(m.distancia_km)} `,
        el("span", { class: m.tem_precos ? "confianca-alta" : "confianca-revisar" }, m.tem_precos ? "tem preços" : "sem preços ainda"),
      ))),
      el("p", { class: "nota" }, `Fonte: ${r.fonte}. Conhece algum desses? `,
        el("button", { type: "button", class: "sugestao", id: "ir-cupom" }, "Enviar um cupom")),
    );
    $("#ir-cupom").addEventListener("click", () => irParaAba("cupom"));
  } catch (e) {
    $("#lista-osm").replaceChildren(e.message);
  } finally {
    botao.disabled = false;
  }
});

// ---------- Enviar cupom (NFC-e) ----------
let notaAtual = null;
let produtosBase = [];

$("#form-cupom").arquivo.addEventListener("change", (e) => {
  $("#nome-arquivo").textContent = e.target.files[0]?.name ?? "com o QR code visível";
});

$("#form-cupom").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const arquivo = form.arquivo.files[0];
  const url = form.url.value.trim();
  $("#erro-cupom").hidden = true;
  $("#nota").hidden = true;
  if (!arquivo && !url) {
    $("#erro-cupom").textContent = "Envie a foto do cupom ou cole o link do QR code.";
    $("#erro-cupom").hidden = false;
    return;
  }
  const botao = form.querySelector("button");
  botao.disabled = true;
  try {
    let opcoes;
    if (arquivo) {
      const corpo = new FormData();
      corpo.append("arquivo", arquivo);
      opcoes = { method: "POST", body: corpo };
    } else {
      opcoes = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) };
    }
    notaAtual = await api(arquivo ? "/api/nfce/imagem" : "/api/nfce/url", opcoes);
    mostrarNota(notaAtual);
  } catch (e) {
    $("#erro-cupom").textContent = e.message;
    $("#erro-cupom").hidden = false;
  } finally {
    botao.disabled = false;
  }
});

function mostrarNota(nota) {
  $("#nota-titulo").textContent = `${nota.emitente} — ${dataBR(nota.data)}`;
  $("#status-nota").textContent = "";
  const tabela = $("#tabela-nota");
  tabela.replaceChildren(el("thead", {}, el("tr", {},
    el("th", {}, "Usar"), el("th", {}, "No cupom"), el("th", {}, "Produto da EconoMIA"),
    el("th", { class: "num" }, "Preço da embalagem"), el("th", {}, "Leitura"),
  )));
  const corpo = el("tbody");
  nota.itens.forEach((item, i) => {
    const marcar = el("input", { type: "checkbox", "data-i": i });
    marcar.checked = item.confianca === "alta";
    const escolha = el("select", { "data-i": i }, el("option", { value: "" }, "— não usar —"),
      ...produtosBase.map((p) => el("option", { value: p.produto_id }, p.produto)));
    escolha.value = item.produto_id ?? "";
    const foto = el("span", { class: "foto-cupom-item" });
    const atualizarFoto = () => {
      const aid = produtosBase.find((p) => p.produto_id === escolha.value)?.alimento_id;
      foto.replaceChildren(aid ? fotoAlimento(aid, "foto-mini") : el("span", { class: "foto-mini sem-foto" }, "?"));
    };
    escolha.addEventListener("change", atualizarFoto);
    const preco = el("input", { type: "number", step: "0.01", min: "0.01", "data-i": i });
    preco.value = item.preco_embalagem ?? item.valor_unitario;
    corpo.append(el("tr", {},
      el("td", {}, marcar),
      el("td", {}, item.descricao, el("span", { class: "fonte" }, `${item.quantidade} ${item.unidade} × ${reais(item.valor_unitario)} = ${reais(item.valor_total)}`)),
      el("td", {}, el("div", { class: "celula-produto" }, foto, escolha)),
      el("td", { class: "num" }, preco),
      el("td", { class: item.confianca === "alta" ? "confianca-alta" : "confianca-revisar" }, item.confianca === "alta" ? "certa" : "revisar"),
    ));
  });
  tabela.append(corpo);
  corpo.querySelectorAll("select").forEach((s) => s.dispatchEvent(new Event("change")));
  $("#nota").hidden = false;
}

$("#salvar-nota").addEventListener("click", async () => {
  const linhas = [...document.querySelectorAll("#tabela-nota tbody tr")];
  const itens = linhas
    .filter((tr) => tr.querySelector("input[type=checkbox]").checked)
    .map((tr) => ({ produto_id: tr.querySelector("select").value, preco: Number(tr.querySelector("input[type=number]").value) }))
    .filter((i) => i.produto_id && i.preco > 0);
  if (!itens.length) {
    $("#status-nota").textContent = "Marque pelo menos um item com produto escolhido.";
    return;
  }
  try {
    const r = await api("/api/nfce/confirmar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ emitente: notaAtual.emitente, cnpj: notaAtual.cnpj, data: notaAtual.data, itens }),
    });
    $("#status-nota").textContent = `✅ ${r.salvos} preço(s) salvo(s). Obrigado por contribuir!`;
    carregarPrecos();
    const opcoes = await api("/api/opcoes");
    mercados = Object.fromEntries(opcoes.mercados.map((m) => [m.id, m]));
  } catch (e) {
    $("#status-nota").textContent = "Não foi possível salvar: " + e.message;
  }
});

// ---------- Preços ----------
async function carregarPrecos() {
  const dados = await api("/api/precos");
  produtosBase = dados.produtos.map((p) => ({ produto_id: p.produto_id, produto: p.produto, alimento_id: p.alimento_id }));
  const ids = dados.mercados.map((m) => m.id);
  const tabela = $("#tabela-precos");
  tabela.replaceChildren(
    el("thead", {}, el("tr", {}, el("th", {}, "Produto"), ...dados.mercados.map((m) => el("th", { class: "num" }, m.nome)))),
  );
  const corpo = el("tbody");
  for (const p of dados.produtos) {
    const valores = ids.map((id) => p.precos[id]?.preco_kg).filter((v) => v !== undefined);
    const menor = Math.min(...valores);
    const linha = el("tr", {}, el("td", {}, el("div", { class: "celula-produto" }, fotoAlimento(p.alimento_id, "foto-mini"), el("span", {}, p.produto))));
    for (const id of ids) {
      const pr = p.precos[id];
      if (!pr) {
        linha.append(el("td", { class: "num" }, "—"));
        continue;
      }
      linha.append(el("td", { class: "num" + (pr.preco_kg === menor && valores.length > 1 ? " melhor" : "") },
        reais(pr.preco),
        el("span", { class: "fonte" }, `${reais(pr.preco_kg)}/kg · ${dataBR(pr.data)}`),
      ));
    }
    corpo.append(linha);
  }
  tabela.append(corpo);
}

// ---------- Conversar ----------
const historico = [];
const NOMES_FERRAMENTAS = {
  montar_cesta: "montou a cesta", consultar_precos: "consultou preços",
  avaliar_promocao: "avaliou a promoção", buscar_conhecimento: "buscou na base",
};

async function carregarStatusLLM() {
  const s = await api("/api/llm");
  $("#status-llm").textContent = s.ativo ? `🤖 ${s.modelo} · grátis` : "🤖 modo sem LLM";
  $("#status-llm").title = s.ativo ? `LLM ${s.modelo} via ${s.provedor} (gratuito)` : "Sem LLM: respostas por regras";
}

const AVATARES = { "Cifrão": "cifrao", "Miau-ricio": "miauricio", "Recibaldo": "recibaldo" };

function adicionarMensagem(classe, texto, gato) {
  const msg = el("div", { class: `msg ${classe}` }, texto);
  const no = gato
    ? el("div", { class: "linha-msg" }, el("img", { src: `img/${gato}.webp`, alt: "", class: "avatar" }), msg)
    : msg;
  $("#mensagens").append(no);
  no.scrollIntoView({ behavior: "smooth", block: "end" });
  return msg;
}

// Alimentos recomendados ou com preço na resposta do chat, com foto.
function cartoesDoChat(dados) {
  const linhas = [];
  for (const i of dados.montar_cesta?.itens_detalhe ?? []) {
    linhas.push(el("li", {}, fotoAlimento(i.alimento_id, "foto-mini"),
      el("span", {}, `${i.quantidade} × ${i.produto}`, el("small", {}, i.mercado)), el("b", {}, reais(i.subtotal))));
  }
  for (const p of dados.consultar_precos?.produtos ?? []) {
    const melhor = p.ofertas[0];
    linhas.push(el("li", {}, fotoAlimento(p.alimento_id, "foto-mini"),
      el("span", {}, p.produto, el("small", {}, `${melhor.mercado} · ${reais(melhor.preco_kg)}/kg`)), el("b", {}, reais(melhor.preco))));
  }
  const promo = dados.avaliar_promocao;
  if (promo?.alimento_id) {
    const veredito = { vale_a_pena: "✅ vale a pena", empate: "➖ empate", nao_vale: "❌ não vale" }[promo.conclusao] ?? "";
    linhas.push(el("li", {}, fotoAlimento(promo.alimento_id, "foto-mini"),
      el("span", {}, promo.alimento, el("small", {}, `normal: ${reais(promo.melhor_preco_kg_normal)}/kg · ${veredito}`)), el("b", {}, `${reais(promo.preco_kg_promocao)}/kg`)));
  }
  return linhas.length ? el("ul", { class: "chat-itens" }, ...linhas) : null;
}

function gatoDaResposta(etapas) {
  const quem = (etapas ?? []).map((e) => e.agente).find((a) => AVATARES[a]);
  return AVATARES[quem] ?? "mia";
}

async function enviarChat(texto) {
  adicionarMensagem("usuario", texto);
  const pensando = adicionarMensagem("assistente pensando", "Pensando… (o LLM local pode levar alguns segundos)", "mia");
  const botao = $("#form-chat button");
  botao.disabled = true;
  try {
    const r = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensagem: texto, historico: historico.slice(-6) }),
    });
    pensando.closest(".linha-msg").remove();
    const msg = adicionarMensagem("assistente", semMarkdown(r.resposta), gatoDaResposta(r.etapas));
    const cartoes = cartoesDoChat(r.dados ?? {});
    if (cartoes) msg.append(cartoes);
    const meta = [];
    if (r.ferramentas_usadas.length) meta.push("A EconoMIA " + [...new Set(r.ferramentas_usadas)].map((f) => NOMES_FERRAMENTAS[f] ?? f).join(", "));
    if (r.fontes.length) meta.push("Fontes: " + [...new Set(r.fontes.map((f) => f.fonte))].join("; "));
    if (r.etapas?.length) meta.push("Agentes: " + textoEtapas(r.etapas));
    if (r.aviso) meta.push("⚠️ " + r.aviso);
    if (meta.length) msg.append(el("span", { class: "meta-msg" }, meta.join(" · ")));
    historico.push({ role: "user", content: texto }, { role: "assistant", content: r.resposta });
  } catch (e) {
    pensando.closest(".linha-msg").remove();
    adicionarMensagem("assistente", "Desculpe, algo deu errado: " + e.message, "mia");
  } finally {
    botao.disabled = false;
  }
}

$("#form-chat").addEventListener("submit", (evento) => {
  evento.preventDefault();
  const campo = evento.target.mensagem;
  const texto = campo.value.trim();
  if (!texto) return;
  campo.value = "";
  enviarChat(texto);
});

document.querySelectorAll(".sugestao").forEach((b) => b.addEventListener("click", () => enviarChat(b.textContent)));

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => { /* o site funciona sem o modo offline */ });
}

iniciar().catch((e) => {
  $("#erro").textContent = "Não foi possível conectar à API: " + e.message;
  $("#erro").hidden = false;
});
