// Cesta montada, pedido que a gerou e o que a Mia diz no Início. A última cesta vem da conta
// da pessoa (GET /cestas/ultima), e não mais do localStorage.
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { mensagemDoProblema } from "../api/problemas";
import { avisarCesta } from "../efeitos/ponte";
import { reais } from "../util/formato";
import { useDadosDaApi } from "./dados-da-api";

type E = components["schemas"];
export type PlanoDeCesta = E["PlanoDeCesta"];
export type PedidoDeCesta = E["PedidoDeCesta"];
export type Cesta = E["Cesta"];

export interface FiltroDeMercados {
  ids: string[];
  /** Centavos: custo de ir a um 2º mercado no raio. */
  deslocamento: number;
  raio_km: number;
}

interface FalaDaMia { rosto: string; frase: string }

interface EstadoDaCesta {
  plano: PlanoDeCesta | null;
  pedido: PedidoDeCesta | null;
  /** Mudou porque a pessoa montou agora (rola a tela e anima) ou porque veio da conta. */
  montadaAgora: boolean;
  montando: boolean;
  erro: string | null;
  fala: FalaDaMia;
  semAlimentos: Map<string, string>;
  ingredientesDisponiveis: Map<string, number>;
  filtro: FiltroDeMercados | null;
  montar: (pedido: Omit<PedidoDeCesta, "sem_alimentos" | "em_casa" | "mercados">) => Promise<void>;
  tirarAlimento: (id: string, nome: string) => void;
  devolverAlimento: (id: string) => void;
  guardarEmCasa: (id: string, kg: number) => void;
  tirarDeCasa: (id: string) => void;
  usarMercados: (filtro: FiltroDeMercados | null) => void;
  /** Ao tirar ou devolver um alimento, a tela Cesta monta de novo com o último formulário. */
  pedidoDeRemontar: number;
}

const FALA_INICIAL: FalaDaMia = { rosto: "✨", frase: "Oi! Eu sou a Mia. Vamos fazer o seu dinheiro do mercado render mais, sem comer pior?" };
const Contexto = createContext<EstadoDaCesta | null>(null);

/** Itens para a cena 3D: um id por unidade, no máximo duas de cada. */
const itensDaCena = (cesta: Cesta) => cesta.itens.flatMap((i) => Array(Math.min(i.quantidade, 2)).fill(i.alimento_id));

export function ProvedorDaCesta({ children }: { children: ReactNode }) {
  const { estabelecimentos } = useDadosDaApi();
  const [plano, setPlano] = useState<PlanoDeCesta | null>(null);
  const [pedido, setPedido] = useState<PedidoDeCesta | null>(null);
  const [montadaAgora, setMontadaAgora] = useState(false);
  const [montando, setMontando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [fala, setFala] = useState<FalaDaMia>(FALA_INICIAL);
  const [semAlimentos, setSemAlimentos] = useState(new Map<string, string>());
  const [ingredientesDisponiveis, setIngredientes] = useState(new Map<string, number>());
  const [filtro, setFiltro] = useState<FiltroDeMercados | null>(null);
  const [pedidoDeRemontar, setRemontar] = useState(0);

  const falarSobre = useCallback((novo: PlanoDeCesta, ped: PedidoDeCesta) => {
    if (!novo.recomendacao || !novo.cesta_recomendada) {
      setFala({
        rosto: "😿",
        frase: ped.orcamento && novo.minimo_necessario
          ? `Com ${reais(ped.orcamento)} não dá para cumprir as metas. Precisaria de ${reais(novo.minimo_necessario)}. Vamos tentar um período menor?`
          : "Com essas escolhas não dá para cumprir as metas. Vamos rever as restrições ou os alimentos que saíram da cesta?",
      });
      return;
    }
    const gasto = novo.cesta_recomendada.custo_total + (novo.recomendacao === "dois" ? novo.custo_deslocamento ?? 0 : 0);
    setFala(ped.orcamento
      ? { rosto: "🎉", frase: `Sua cesta coube no orçamento! Sobraram ${reais(ped.orcamento - gasto)} e todas as metas nutricionais foram cumpridas.` }
      : { rosto: "✨", frase: `Sua cesta custa ${reais(gasto)} e cumpre todas as metas nutricionais.` });
  }, []);

  const mostrar = useCallback((novo: PlanoDeCesta, ped: PedidoDeCesta, agora: boolean) => {
    setPlano(novo);
    setPedido(ped);
    setMontadaAgora(agora);
    falarSobre(novo, ped);
    const cesta = novo.cesta_recomendada;
    avisarCesta(
      { itens: novo.recomendacao && cesta ? itensDaCena(cesta) : [], coube: !ped.orcamento || !!cesta?.dentro_do_orcamento },
      agora,
    );
  }, [falarSobre]);

  // Última cesta da conta. Preço muda: se ela é de outro dia, a Mia avisa para montar de novo.
  const restaurada = useRef(false);
  useEffect(() => {
    if (restaurada.current) return;
    restaurada.current = true;
    exigir(api.GET("/cestas/ultima")).then((ultima) => {
      const cesta = ultima.plano.cesta_recomendada;
      if (!ultima.plano.recomendacao || !cesta?.mercados.every((m) => estabelecimentos[m])) return;
      mostrar(ultima.plano, { ...ultima.pedido, em_casa: [] }, false);
      const dias = Math.floor((Date.now() - new Date(ultima.quando).getTime()) / 86400000);
      if (dias >= 1) setFala({ rosto: "📅", frase: `Sua última cesta é de ${new Date(ultima.quando).toLocaleDateString("pt-BR")}. Os preços podem ter mudado: monte de novo para conferir.` });
    }).catch(() => { /* ainda não montou nenhuma */ });
  }, [estabelecimentos, mostrar]);

  const montar: EstadoDaCesta["montar"] = useCallback(async (dados) => {
    const completo: PedidoDeCesta = {
      ...dados,
      ...(filtro ? { mercados: filtro.ids } : {}),
      sem_alimentos: [...semAlimentos.keys()],
      em_casa: [...ingredientesDisponiveis.entries()].map(([alimento, kg]) => ({ alimento, gramas: Math.round(kg * 1000) })),
    };
    setMontando(true);
    setErro(null);
    try {
      mostrar(await exigir(api.POST("/cestas", { body: completo })), completo, true);
    } catch (e) {
      setErro("Não foi possível montar a cesta: " + mensagemDoProblema(e));
      setPlano(null);
    } finally {
      setMontando(false);
    }
  }, [filtro, semAlimentos, ingredientesDisponiveis, mostrar]);

  const valor: EstadoDaCesta = {
    plano, pedido, montadaAgora, montando, erro, fala, semAlimentos, ingredientesDisponiveis, filtro, pedidoDeRemontar,
    montar,
    tirarAlimento: (id, nome) => { setSemAlimentos((m) => new Map(m).set(id, nome)); setRemontar((n) => n + 1); },
    devolverAlimento: (id) => { setSemAlimentos((m) => { const n = new Map(m); n.delete(id); return n; }); setRemontar((n) => n + 1); },
    guardarEmCasa: (id, kg) => setIngredientes((m) => new Map(m).set(id, kg)),
    tirarDeCasa: (id) => setIngredientes((m) => { const n = new Map(m); n.delete(id); return n; }),
    usarMercados: setFiltro,
  };
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useCesta() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useCesta fora do ProvedorDaCesta");
  return valor;
}
