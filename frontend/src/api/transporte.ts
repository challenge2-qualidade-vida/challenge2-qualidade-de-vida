// Escolhe por onde as chamadas passam: a API de verdade ou os dados falsos tipados.
// VITE_DADOS_FALSOS=1 liga os dados falsos (src/api/dados-falsos), sem mudar nada nas telas.
import { responderComDadosFalsos } from "./dados-falsos";

export const usandoDadosFalsos = import.meta.env.VITE_DADOS_FALSOS === "1";

export const transporte: typeof fetch = usandoDadosFalsos
  ? (entrada, opcoes) => responderComDadosFalsos(new Request(entrada, opcoes))
  : (entrada, opcoes) => fetch(entrada, { credentials: "include", ...opcoes });
