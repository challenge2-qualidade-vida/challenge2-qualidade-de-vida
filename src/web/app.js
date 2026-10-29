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
document.querySelectorAll(".contador-botao").forEach((b) => b.addEventListener("click", () => {
  const campo = $("#form-cesta").pessoas;
  campo.value = Math.min(20, Math.max(1, Number(campo.value || 1) + Number(b.dataset.passo)));
}));

// ---------- Mascote e dica do dia ----------
const DICAS = [
  ["Compare o preço por quilo, não o da embalagem: o pacote maior nem sempre compensa.", "Critérios da EconoMIA"],
  ["Arroz com feijão é uma combinação completa: as proteínas dos dois se complementam.", "Guia Alimentar para a População Brasileira"],
  ["Frutas e legumes da estação costumam ser mais baratos e mais saborosos.", "Guia Alimentar para a População Brasileira"],
  ["O ovo é uma das proteínas mais baratas e pode substituir a carne em várias refeições.", "Guia Alimentar para a População Brasileira"],
  ["Banana muito madura vira vitamina, mingau ou bolo. Não precisa ir para o lixo!", "Aproveitamento de alimentos (EconoMIA)"],
  ["Planeje as refeições antes de ir ao mercado e nunca faça compras com fome.", "Critérios da EconoMIA"],
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

function atualizarInicio(plano, pedido) {
  if (!plano.recomendacao) {
    falarMascote("😿", `Com ${reais(pedido.orcamento)} não dá para cumprir as metas. Precisaria de ${reais(plano.minimo_necessario ?? 0)}. Vamos tentar um período menor?`);
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

  const lista = $("#lista-restricoes");
  for (const r of opcoes.restricoes) {
    lista.append(el("label", { class: "chip" }, el("input", { type: "checkbox", name: "restricoes", value: r.id }), r.nome));
  }

  mostrarDica();
  carregarPrecos();
  carregarStatusLLM();
  carregarRegioes();
}

// ---------- Cesta ----------
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

function mostrarPlano(plano, pedido) {
  const resumo = $("#resumo");
  resumo.replaceChildren();
  $("#explicacao").replaceChildren(...plano.explicacao.map((f) => el("li", {}, f)));

  if (!plano.recomendacao) {
    resumo.append(cartaoOpcao("Orçamento informado", null, false));
    $("#metas").replaceChildren();
    $("#itens").replaceChildren();
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
  cestaAtual = { alimentos: [...new Set(cesta.itens.map((i) => i.alimento.split(" (")[0]))], restricoes: pedido.restricoes };
  $("#cardapio").replaceChildren();
  $("#resultado").hidden = false;
  $("#resultado").scrollIntoView({ behavior: "smooth", block: "start" });
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
      el("span", { class: "item-emoji", "aria-hidden": "true" }, EMOJI_GRUPOS[i.grupo] ?? "🛒"),
      el("span", {},
        el("span", { class: "item-nome" }, i.produto),
        el("span", { class: "item-detalhe" }, `${i.quantidade} × ${reais(i.preco_unitario)} · ${reais(i.preco_kg)}/kg`),
        el("span", { class: "item-detalhe" }, `Preço de ${dataBR(i.data_preco)} · fonte: ${i.fonte_preco}`),
      ),
      el("span", { class: "item-valor" }, reais(i.subtotal), el("small", {}, NOMES_GRUPOS[i.grupo] ?? i.grupo)),
    ))));
  }
}

function textoEtapas(etapas) {
  return (etapas ?? []).map((e) => `${e.agente}: ${e.acao}`).join(" → ");
}

$("#botao-cardapio").addEventListener("click", async (evento) => {
  if (!cestaAtual) return;
  const botao = evento.target;
  const area = $("#cardapio");
  botao.disabled = true;
  area.replaceChildren("Montando o cardápio… (o LLM local pode levar alguns segundos)");
  try {
    const r = await api("/api/cardapio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cestaAtual),
    });
    area.replaceChildren(semMarkdown(r.resposta), el("span", { class: "meta-msg" }, textoEtapas(r.etapas)));
  } catch (e) {
    area.replaceChildren("Não foi possível montar o cardápio: " + e.message);
  } finally {
    botao.disabled = false;
  }
});

// ---------- Perto de mim ----------
let posicao = null;          // {lat, lon} só na memória da página
let mercadosPerto = null;    // ids usados ao montar a cesta

const NOMES_GRUPOS_PROTEINA = { proteina_animal: "Carnes e ovos", laticinios: "Leite e queijos", leguminosas: "Feijões" };

async function carregarRegioes() {
  const regioes = await api("/api/regioes");
  $("#regiao").append(...regioes.map((r) => el("option", { value: `${r.lat},${r.lon}` }, r.nome)));
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

$("#raio").addEventListener("change", () => posicao && buscarPerto(posicao.lat, posicao.lon, posicao.origem));

async function buscarPerto(lat, lon, origem) {
  posicao = { lat, lon, origem };
  const raio = Number($("#raio").value) || 10;
  $("#status-perto").textContent = `Buscando mercados a até ${raio} km de ${origem}…`;
  try {
    const r = await api(`/api/proximos?lat=${lat.toFixed(4)}&lon=${lon.toFixed(4)}&raio_km=${raio}`);
    mostrarPerto(r, raio, origem);
  } catch (e) {
    $("#status-perto").textContent = "Erro: " + e.message;
  }
}

function mostrarPerto(r, raio, origem) {
  $("#lista-osm").replaceChildren();
  if (!r.mercados.length) {
    $("#status-perto").textContent = `Nenhum mercado com preços a até ${raio} km de ${origem}. Aumente o raio ou envie um cupom de um mercado da sua região.`;
    $("#resultado-perto").hidden = false;
    $("#tabela-proximos").replaceChildren();
    $("#tabela-proteinas").replaceChildren();
    $("#resumo-proteinas").replaceChildren();
    mercadosPerto = null;
    return;
  }
  $("#status-perto").textContent = `${r.mercados.length} mercado(s) com preços a até ${raio} km de ${origem}. Custo de carro estimado em ${reais(r.custo_por_km)} por km.`;
  mercadosPerto = { ids: r.mercados.map((m) => m.id), deslocamento: r.custo_segundo_mercado };

  $("#tabela-proximos").replaceChildren(
    el("thead", {}, el("tr", {}, el("th", {}, "Mercado"), el("th", {}, "Região"), el("th", { class: "num" }, "Distância"), el("th", { class: "num" }, "Ida e volta (carro)"))),
    el("tbody", {}, ...r.mercados.map((m) => el("tr", {},
      el("td", {}, m.nome), el("td", {}, m.regiao),
      el("td", { class: "num" }, `${String(m.distancia_km).replace(".", ",")} km`),
      el("td", { class: "num" }, reais(m.custo_ida_volta)),
    ))),
  );

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
    resumo.push(el("div", { class: "cartao opcao" },
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
      el("td", {}, a.alimento, el("span", { class: "fonte" }, `${NOMES_GRUPOS_PROTEINA[a.grupo]} · ${String(a.proteina_100g).replace(".", ",")} g de proteína/100 g`)),
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
  $("#filtro-mercados").textContent = `Usando só os mercados perto de você: ${mercadosPerto.ids.map((id) => mercados[id]?.nome ?? id).join(", ")}. `;
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
    const raio = Math.min(Number($("#raio").value) || 10, 10);
    const r = await api(`/api/osm?lat=${posicao.lat.toFixed(2)}&lon=${posicao.lon.toFixed(2)}&raio_km=${raio}`);
    if (!r.supermercados.length) {
      $("#lista-osm").replaceChildren("Nenhum supermercado encontrado no mapa nessa área.");
      return;
    }
    $("#lista-osm").replaceChildren(
      el("ul", { class: "explicacao" }, ...r.supermercados.slice(0, 20).map((m) => el("li", {},
        `${m.nome} — ${String(m.distancia_km).replace(".", ",")} km `,
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
    const preco = el("input", { type: "number", step: "0.01", min: "0.01", "data-i": i });
    preco.value = item.preco_embalagem ?? item.valor_unitario;
    corpo.append(el("tr", {},
      el("td", {}, marcar),
      el("td", {}, item.descricao, el("span", { class: "fonte" }, `${item.quantidade} ${item.unidade} × ${reais(item.valor_unitario)} = ${reais(item.valor_total)}`)),
      el("td", {}, escolha),
      el("td", { class: "num" }, preco),
      el("td", { class: item.confianca === "alta" ? "confianca-alta" : "confianca-revisar" }, item.confianca === "alta" ? "certa" : "revisar"),
    ));
  });
  tabela.append(corpo);
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
  produtosBase = dados.produtos.map((p) => ({ produto_id: p.produto_id, produto: p.produto }));
  const ids = dados.mercados.map((m) => m.id);
  const tabela = $("#tabela-precos");
  tabela.replaceChildren(
    el("thead", {}, el("tr", {}, el("th", {}, "Produto"), ...dados.mercados.map((m) => el("th", { class: "num" }, m.nome)))),
  );
  const corpo = el("tbody");
  for (const p of dados.produtos) {
    const valores = ids.map((id) => p.precos[id]?.preco_kg).filter((v) => v !== undefined);
    const menor = Math.min(...valores);
    const linha = el("tr", {}, el("td", {}, p.produto));
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
    const itens = r.dados?.montar_cesta?.itens;
    if (r.modo === "llm" && itens?.length) {
      msg.append(el("ul", { class: "lista-msg" }, ...itens.map((i) => el("li", {}, i))));
    }
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

iniciar().catch((e) => {
  $("#erro").textContent = "Não foi possível conectar à API: " + e.message;
  $("#erro").hidden = false;
});
