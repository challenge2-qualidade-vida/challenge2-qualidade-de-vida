// Nota fiscal fictícia desenhada no navegador, para o botão "Testar com uma nota de exemplo"
// da tela Documento. Sem dado pessoal: loja, CNPJ e itens são inventados.
export const PERGUNTA_DE_EXEMPLO = "Quanto gastei com hortifrúti?";

const LINHAS = [
  "MERCADO EXEMPLO LTDA",
  "CNPJ 00.000.000/0001-00",
  "CUPOM FISCAL ELETRONICO - NFC-e",
  "--------------------------------",
  "ARROZ T1 5KG        1 UN   24,90",
  "FEIJAO CARIOCA 1KG  2 UN   15,98",
  "BANANA PRATA KG   1,2 KG    6,59",
  "TOMATE ITALIANO   0,8 KG    5,12",
  "ALFACE CRESPA UN    1 UN    2,99",
  "--------------------------------",
  "TOTAL R$                   55,58",
  "DOCUMENTO FICTICIO - EXEMPLO",
];

/** Desenha o cupom num canvas e devolve um PNG. */
export async function criarNotaDeExemplo(): Promise<File> {
  const canvas = document.createElement("canvas");
  canvas.width = 420;
  canvas.height = 40 + LINHAS.length * 28;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Este navegador não consegue gerar a nota de exemplo.");
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#111";
  ctx.font = "16px monospace";
  LINHAS.forEach((linha, i) => ctx.fillText(linha, 20, 36 + i * 28));
  const blob = await new Promise<Blob | null>((ok) => canvas.toBlob(ok, "image/png"));
  if (!blob) throw new Error("Não foi possível gerar a nota de exemplo.");
  return new File([blob], "nota-de-exemplo.png", { type: "image/png" });
}
