// Separa o texto da resposta em partes de texto e citações [n], para ligar cada citação à fonte.

export type Parte = { tipo: "texto"; valor: string } | { tipo: "citacao"; numero: number };

const CITACAO = /\[(\d+)\]/g;

/** Divide um parágrafo em texto e citações. Números sem fonte correspondente ficam como texto. */
export function separarCitacoes(texto: string, fontesExistentes: Set<number>): Parte[] {
  const partes: Parte[] = [];
  let inicio = 0;
  for (const encontrado of texto.matchAll(CITACAO)) {
    const numero = Number(encontrado[1]);
    const posicao = encontrado.index ?? 0;
    if (!fontesExistentes.has(numero)) continue;
    if (posicao > inicio) partes.push({ tipo: "texto", valor: texto.slice(inicio, posicao) });
    partes.push({ tipo: "citacao", numero });
    inicio = posicao + encontrado[0].length;
  }
  if (inicio < texto.length) partes.push({ tipo: "texto", valor: texto.slice(inicio) });
  return partes;
}

/** Parágrafos da resposta: linhas em branco separam parágrafos; quebras simples são mantidas. */
export function paragrafos(texto: string): string[] {
  return texto
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
}
