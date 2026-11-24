// Escala da barra de score. Os scores de similaridade ficam quase todos entre 0,80 e 0,95;
// numa barra de 0 a 1 a diferença entre eles some, então a barra começa em ESCALA_MINIMA.

export const ESCALA_MINIMA = 0.75;

/** Largura da barra, em %, para um score entre ESCALA_MINIMA e 1. */
export function larguraDaBarra(score: number, minimo = ESCALA_MINIMA): number {
  const proporcao = (score - minimo) / (1 - minimo);
  return Math.round(Math.min(1, Math.max(0, proporcao)) * 1000) / 10;
}

/** Número com vírgula decimal, como se escreve em português (0.867 → "0,867"). */
export function decimal(valor: number, casas = 3): string {
  return valor.toFixed(casas).replace(".", ",");
}

/** "1 trecho", "5 trechos". */
export function plural(quantidade: number, singular: string, varios: string): string {
  return `${quantidade} ${quantidade === 1 ? singular : varios}`;
}
