// Ponto de partida da busca por mercados: a localização (só na memória da página) ou a região padrão.
import { createContext, useContext, useState, type ReactNode } from "react";
import { useConfiguracoes } from "./configuracoes";
import { useDadosDaApi } from "./dados-da-api";

export interface Posicao { lat: number; lon: number; origem: string }

interface Estado { posicao: Posicao | null; definir: (p: Posicao) => void }
const Contexto = createContext<Estado | null>(null);

export function ProvedorDePosicao({ children }: { children: ReactNode }) {
  const [posicao, definir] = useState<Posicao | null>(null);
  return <Contexto.Provider value={{ posicao, definir }}>{children}</Contexto.Provider>;
}

export function usePosicao() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("usePosicao fora do ProvedorDePosicao");
  return valor;
}

/** A localização, ou a região padrão das Configurações, ou nada. */
export function usePontoDePartida(): Posicao | null {
  const { posicao } = usePosicao();
  const { config } = useConfiguracoes();
  const { regioes } = useDadosDaApi();
  if (posicao) return posicao;
  if (!config.regiao) return null;
  const [lat, lon] = config.regiao.split(",").map(Number);
  const nome = regioes.find((r) => `${r.lat},${r.lon}` === config.regiao)?.nome;
  return { lat, lon, origem: nome ?? "região padrão" };
}
