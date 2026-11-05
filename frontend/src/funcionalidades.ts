// Funcionalidades fora do MVP do grupo (docs/produto/escopo-do-mvp.md, na main).
// Ficam desligadas por padrão e ligam pela variável VITE_FUNCIONALIDADES:
// "todas" ou uma lista separada por vírgula. Com a flag desligada, a tela some e a rota não é chamada.

export type Funcionalidade =
  | "promocao"      // "Essa promoção vale?" (F6)
  | "deslocamento"  // custo de deslocamento e custo por km (F7)
  | "nutricao"      // anéis das metas nutricionais, calculadas pela TACO (F14)
  | "perto"         // tela Perto de mim: mercados no raio, proteínas e mapa (depende de F5 e F7)
  | "precos";       // tabela de preços (histórico e tendência, F8)

const pedidas = (import.meta.env.VITE_FUNCIONALIDADES ?? "").split(",").map((s: string) => s.trim()).filter(Boolean);

export function funcionalidadeLigada(nome: Funcionalidade): boolean {
  return pedidas.includes("todas") || pedidas.includes(nome);
}
