// Grava os dados falsos a partir das respostas do protótipo (src/economia/api.py).
// Rodar com o protótipo no ar:  node scripts/gravar-dados-falsos.mjs [http://localhost:8000]
// Os valores em dinheiro viram centavos (inteiros), como pede o contrato provisório.
import { mkdirSync, writeFileSync } from "node:fs";

const BASE = process.argv[2] ?? "http://localhost:8000";
const SAIDA = new URL("../src/api/dados-falsos/gravacoes/", import.meta.url);

// Campos que guardam dinheiro em reais no protótipo.
const DINHEIRO = new Set([
  "preco", "preco_kg", "preco_unitario", "subtotal", "custo_total", "custo_por_1000_kcal", "custo_por_g_proteina",
  "minimo_necessario", "custo_deslocamento", "economia_bruta_dois", "economia_liquida_dois", "carrinho_proteinas",
  "custo_real", "custo_ida_volta", "custo_segundo_mercado", "custo_100g_proteina", "valor_unitario", "valor_total",
  "preco_embalagem", "melhor_preco_kg_normal", "preco_kg_promocao", "orcamento", "custo_por_km",
]);
// Mapas cujos valores são dinheiro (chave = id do mercado).
const MAPAS_DE_DINHEIRO = new Set(["custo_por_mercado", "total_por_mercado"]);

const centavos = (v) => (typeof v === "number" ? Math.round(v * 100) : v);

function converter(valor, chave) {
  if (Array.isArray(valor)) return valor.map((v) => converter(v));
  if (valor && typeof valor === "object") {
    if (MAPAS_DE_DINHEIRO.has(chave) || chave === "custo_por_km") return Object.fromEntries(Object.entries(valor).map(([k, v]) => [k, centavos(v)]));
    return Object.fromEntries(Object.entries(valor).map(([k, v]) => [k, converter(v, k)]));
  }
  return DINHEIRO.has(chave) ? centavos(valor) : valor;
}

async function pedir(caminho, corpo) {
  const r = await fetch(BASE + caminho, corpo
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) }
    : undefined);
  if (!r.ok) throw new Error(`${caminho}: ${r.status}`);
  return r.json();
}

function gravar(nome, dados) {
  writeFileSync(new URL(`${nome}.json`, SAIDA), JSON.stringify(converter(dados), null, 1) + "\n");
  console.log("gravado", nome);
}

mkdirSync(SAIDA, { recursive: true });
const pedidoPadrao = { orcamento: 800, pessoas: 4, periodo: "mes", restricoes: [], custo_deslocamento: 10, sem_alimentos: [], em_casa: [] };
for (const nome of ["opcoes", "precos", "creditos", "configuracoes", "regioes", "llm"]) gravar(nome, await pedir(`/api/${nome}`));
const regioes = await pedir("/api/regioes");
const proximos = {};
// Cada região no raio padrão (10 km) e no máximo (100 km), com o custo por km padrão.
for (const r of regioes) for (const raio of [10, 100]) {
  proximos[`${r.lat.toFixed(4)},${r.lon.toFixed(4)},${raio}`] = await pedir(`/api/proximos?lat=${r.lat.toFixed(4)}&lon=${r.lon.toFixed(4)}&raio_km=${raio}&custo_por_km=0.65`);
}
gravar("proximos", proximos);
const plano = await pedir("/api/cesta", pedidoPadrao);
gravar("cesta", plano);
const alimentos = [...new Set(plano.cesta_recomendada.itens.map((i) => i.alimento_id))];
gravar("cardapio", await pedir("/api/cardapio", { alimentos, restricoes: [], dias: 3 }));
