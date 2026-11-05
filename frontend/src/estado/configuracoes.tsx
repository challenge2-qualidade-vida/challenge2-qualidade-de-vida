// Preferências de busca, guardadas só neste navegador. É conveniência leve, sem dado pessoal:
// raio, custo por km, ordenação e a região padrão (um bairro, nunca a localização).
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

export type Ordem = "custo_beneficio" | "preco" | "distancia";
export interface Configuracoes {
  raio_km: number;
  /** Centavos por km. */
  custo_por_km: number;
  ordem: Ordem;
  /** "lat,lon" da região padrão, ou vazio para perguntar sempre. */
  regiao: string;
}

const CHAVE = "economia.config";
export const CONFIG_PADRAO: Configuracoes = { raio_km: 10, custo_por_km: 65, ordem: "custo_beneficio", regiao: "" };

function ler(): Configuracoes {
  try {
    const salvas = JSON.parse(localStorage.getItem(CHAVE) || "{}");
    // O site antigo guardava o custo por km em reais; aqui é em centavos.
    if (typeof salvas.custo_por_km === "number" && salvas.custo_por_km < 10) salvas.custo_por_km = Math.round(salvas.custo_por_km * 100);
    return { ...CONFIG_PADRAO, raio_km: salvas.raio_km ?? CONFIG_PADRAO.raio_km, custo_por_km: salvas.custo_por_km ?? CONFIG_PADRAO.custo_por_km, ordem: salvas.ordem ?? CONFIG_PADRAO.ordem, regiao: salvas.regiao ?? "" };
  } catch {
    return { ...CONFIG_PADRAO };
  }
}

interface Estado {
  /** O que está na tela, inclusive enquanto a pessoa arrasta um controle. */
  config: Configuracoes;
  /** O que foi gravado: a busca por mercados só refaz quando isto muda. */
  salvas: Configuracoes;
  /** Muda na tela sem gravar (enquanto arrasta o controle). */
  ajustar: (mudancas: Partial<Configuracoes>) => void;
  salvar: (mudancas: Partial<Configuracoes>) => void;
  restaurar: () => void;
}

const Contexto = createContext<Estado | null>(null);

export function ProvedorDeConfiguracoes({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<Configuracoes>(ler);
  const [salvas, setSalvas] = useState<Configuracoes>(config);
  const ajustar = useCallback((m: Partial<Configuracoes>) => setConfig((c) => ({ ...c, ...m })), []);
  const salvar = useCallback((m: Partial<Configuracoes>) => setConfig((c) => {
    const nova = { ...c, ...m };
    try { localStorage.setItem(CHAVE, JSON.stringify(nova)); } catch { /* navegação privada: vale só nesta sessão */ }
    setSalvas(nova);
    return nova;
  }), []);
  const restaurar = useCallback(() => salvar({ ...CONFIG_PADRAO }), [salvar]);
  return <Contexto.Provider value={{ config, salvas, ajustar, salvar, restaurar }}>{children}</Contexto.Provider>;
}

export function useConfiguracoes() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useConfiguracoes fora do ProvedorDeConfiguracoes");
  return valor;
}
