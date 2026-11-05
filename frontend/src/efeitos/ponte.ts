// Ponte entre o React e os efeitos (cena 3D, gatos vivos e animações).
// Os efeitos foram escritos fora do React e ouvem eventos no `document`. A ponte guarda
// o estado que eles leem e dispara os mesmos eventos do site antigo.

export type NomeDaAba = "inicio" | "cesta" | "perto" | "chat" | "cupom" | "config" | "precos" | "entrar" | "cadastro";

export interface CestaDaCena {
  /** Ids dos alimentos, um por unidade (no máximo duas unidades de cada). */
  itens: string[];
  coube: boolean;
}

export const ponte: { aba: NomeDaAba; cesta: CestaDaCena | null } = { aba: "inicio", cesta: null };

export function avisarAba(aba: NomeDaAba) {
  ponte.aba = aba;
  document.dispatchEvent(new CustomEvent("economia:aba", { detail: { aba } }));
}

export function avisarCesta(cesta: CestaDaCena, animar: boolean) {
  ponte.cesta = cesta;
  document.dispatchEvent(new CustomEvent("economia:cesta", { detail: { ...cesta, animar } }));
}
