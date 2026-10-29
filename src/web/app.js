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

// ---------- Abas ----------
document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((b) => {
      b.classList.toggle("ativa", b === botao);
      b.setAttribute("aria-selected", b === botao);
    });
    document.querySelectorAll(".painel").forEach((p) => (p.hidden = p.id !== `aba-${botao.dataset.aba}`));
  });
});

// ---------- Início ----------
async function iniciar() {
  const opcoes = await api("/api/opcoes");
  mercados = Object.fromEntries(opcoes.mercados.map((m) => [m.id, m]));

  if (opcoes.aviso_dados) {
    const aviso = $("#aviso-dados");
    aviso.textContent = "⚠️ " + opcoes.aviso_dados;
    aviso.hidden = false;
  }

  const lista = $("#lista-restricoes");
  for (const r of opcoes.restricoes) {
    lista.append(el("label", { class: "chip" }, el("input", { type: "checkbox", name: "restricoes", value: r.id }), r.nome));
  }

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

  const botao = evento.target.querySelector("button");
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
    el("div", { class: "cartao opcao" },
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

function mostrarMetas(cesta) {
  const linhas = Object.entries(NOMES_METAS).map(([chave, [nome, unidade]]) => {
    const obtido = cesta.obtido[chave];
    const meta = cesta.metas[chave];
    const pct = Math.round((obtido / meta) * 100);
    const barra = el("div", { class: "barra" }, el("span", { style: `width:${Math.min(pct, 100)}%` }));
    return el("div", { class: "meta-linha" },
      el("span", {}, nome),
      barra,
      el("span", { class: "num" }, `${pct}% da meta`),
    );
  });
  $("#metas").replaceChildren(...linhas);
}

function mostrarItens(cesta) {
  const area = $("#itens");
  area.replaceChildren();
  for (const id of cesta.mercados) {
    const itens = cesta.itens.filter((i) => i.mercado_id === id);
    area.append(el("h3", { class: "mercado-titulo" }, `${mercados[id].nome} — ${reais(cesta.custo_por_mercado[id])}`));
    const tabela = el("table", { class: "tabela" });
    tabela.append(
      el("thead", {}, el("tr", {},
        el("th", {}, "Produto"), el("th", {}, "Grupo"), el("th", { class: "num" }, "Qtd."),
        el("th", { class: "num" }, "Preço"), el("th", { class: "num" }, "Preço/kg"), el("th", { class: "num" }, "Subtotal"),
      )),
    );
    const corpo = el("tbody");
    for (const i of itens) {
      corpo.append(el("tr", {},
        el("td", {}, i.produto, el("span", { class: "fonte" }, `Preço de ${dataBR(i.data_preco)} · fonte: ${i.fonte_preco}`)),
        el("td", {}, NOMES_GRUPOS[i.grupo] ?? i.grupo),
        el("td", { class: "num" }, String(i.quantidade)),
        el("td", { class: "num" }, reais(i.preco_unitario)),
        el("td", { class: "num" }, reais(i.preco_kg)),
        el("td", { class: "num" }, reais(i.subtotal)),
      ));
    }
    tabela.append(corpo);
    area.append(el("div", { class: "tabela-rolagem" }, tabela));
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

function irParaAba(nome) {
  document.querySelector(`.aba[data-aba="${nome}"]`).click();
}

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
  $("#status-llm").textContent = s.ativo ? `LLM: ${s.modelo} (${s.provedor}, gratuito)` : "Modo sem LLM";
}

function adicionarMensagem(classe, texto) {
  const msg = el("div", { class: `msg ${classe}` }, texto);
  $("#mensagens").append(msg);
  msg.scrollIntoView({ behavior: "smooth", block: "end" });
  return msg;
}

async function enviarChat(texto) {
  adicionarMensagem("usuario", texto);
  const pensando = adicionarMensagem("assistente pensando", "Pensando… (o LLM local pode levar alguns segundos)");
  const botao = $("#form-chat button");
  botao.disabled = true;
  try {
    const r = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensagem: texto, historico: historico.slice(-6) }),
    });
    pensando.remove();
    const msg = adicionarMensagem("assistente", semMarkdown(r.resposta));
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
    pensando.remove();
    adicionarMensagem("assistente", "Desculpe, algo deu errado: " + e.message);
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
