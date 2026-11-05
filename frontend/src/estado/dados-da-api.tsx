// Dados de referência carregados uma vez depois do login: opções do formulário, preços,
// limites das configurações, regiões e o modelo de linguagem.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { mensagemDoProblema } from "../api/problemas";
import { funcionalidadeLigada } from "../funcionalidades";

type E = components["schemas"];

export interface DadosDaApi {
  opcoes: E["Opcoes"];
  estabelecimentos: Record<string, E["Estabelecimento"]>;
  nomesAlimentos: Record<string, string>;
  precos: E["TabelaDePrecos"] | null;
  limites: E["LimitesDeConfiguracao"] | null;
  regioes: E["Regiao"][];
  llm: E["EstadoDoLlm"] | null;
  recarregarPrecos: () => Promise<void>;
}

const Contexto = createContext<DadosDaApi | null>(null);

/** Carrega os dados; enquanto isso, ou se falhar, entrega null e o erro. */
export function useCarregarDadosDaApi() {
  const [dados, setDados] = useState<DadosDaApi | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    async function carregar() {
      const opcoes = await exigir(api.GET("/opcoes"));
      const [precos, limites, regioes, llm] = await Promise.all([
        exigir(api.GET("/precos")).catch(() => null),
        exigir(api.GET("/configuracoes")).catch(() => null),
        funcionalidadeLigada("perto") ? exigir(api.GET("/regioes")).catch(() => []) : Promise.resolve([]),
        exigir(api.GET("/llm")).catch(() => null),
      ]);
      const montar = (tabela: E["TabelaDePrecos"] | null): DadosDaApi => ({
        opcoes,
        estabelecimentos: Object.fromEntries(opcoes.mercados.map((m) => [m.id, m])),
        nomesAlimentos: Object.fromEntries(opcoes.alimentos.map((a) => [a.id, a.nome])),
        precos: tabela, limites, regioes, llm,
        recarregarPrecos: async () => {
          const nova = await exigir(api.GET("/precos"));
          if (vivo) setDados(montar(nova));
        },
      });
      if (vivo) setDados(montar(precos));
    }
    carregar().catch((e) => { if (vivo) setErro(mensagemDoProblema(e)); });
    return () => { vivo = false; };
  }, []);

  return { dados, erro };
}

export function ProvedorDeDados({ dados, children }: { dados: DadosDaApi; children: ReactNode }) {
  return <Contexto.Provider value={dados}>{children}</Contexto.Provider>;
}

export function useDadosDaApi() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useDadosDaApi fora do ProvedorDeDados");
  return valor;
}

/** Nome do estabelecimento, ou o id quando ele não está na lista. */
export function useNomeDoEstabelecimento() {
  const { estabelecimentos } = useDadosDaApi();
  return (id: string) => estabelecimentos[id]?.nome ?? id;
}
