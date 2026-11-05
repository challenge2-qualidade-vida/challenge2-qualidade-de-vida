// Tela aberta. O site troca de tela sem mudar o endereço, como o antigo (decisão em docs/decisoes.md).
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { avisarAba, type NomeDaAba } from "../efeitos/ponte";

interface Navegacao {
  aba: NomeDaAba;
  irPara: (aba: NomeDaAba) => void;
  /** Texto que a tela Mia põe no campo ao abrir (atalho "Essa promoção vale?"). */
  perguntaPendente: string | null;
  perguntar: (texto: string) => void;
  limparPergunta: () => void;
}

const Contexto = createContext<Navegacao | null>(null);

export function ProvedorDeNavegacao({ children, inicial = "inicio" }: { children: ReactNode; inicial?: NomeDaAba }) {
  const [aba, setAba] = useState<NomeDaAba>(inicial);
  const [perguntaPendente, setPergunta] = useState<string | null>(null);

  const irPara = useCallback((nome: NomeDaAba) => {
    // A tela nova precisa estar desenhada antes de voltar ao topo, como no site antigo,
    // senão a rolagem suave para no meio da página antiga.
    const trocar = () => {
      flushSync(() => setAba(nome));
      avisarAba(nome);
      window.scrollTo({ top: 0, behavior: "smooth" });
    };
    if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(trocar);
    else trocar();
  }, []);

  const perguntar = useCallback((texto: string) => {
    setPergunta(texto);
    irPara("chat");
  }, [irPara]);

  return (
    <Contexto.Provider value={{ aba, irPara, perguntaPendente, perguntar, limparPergunta: () => setPergunta(null) }}>
      {children}
    </Contexto.Provider>
  );
}

export function useNavegacao() {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useNavegacao fora do ProvedorDeNavegacao");
  return valor;
}
