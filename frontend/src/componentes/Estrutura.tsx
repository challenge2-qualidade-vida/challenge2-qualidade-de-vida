// Barra do topo, aviso dos dados de exemplo e navegação (embaixo no celular, na lateral no computador).
import type { NomeDaAba } from "../efeitos/ponte";
import { useNavegacao } from "../estado/navegacao";
import type { components } from "../api/esquema";

const ENGRENAGEM = "M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z";

export function BarraDoTopo({ llm, comBotoes = true }: { llm: components["schemas"]["EstadoDoLlm"] | null; comBotoes?: boolean }) {
  const { irPara } = useNavegacao();
  return (
    <header className="barra-topo">
      <button type="button" className="marca" data-ir="inicio" aria-label="EconoMIA: voltar para o início" onClick={() => comBotoes && irPara("inicio")}><img src="img/logo-gato.webp" alt="" className="marca-gato" /><img src="img/logo-nome.webp" alt="" className="marca-nome" /></button>
      {comBotoes && (
        <div className="topo-direita">
          <span id="status-llm" className="pilula" title={llm ? (llm.ativo ? `LLM ${llm.modelo} via ${llm.provedor} (gratuito)` : "Sem LLM: respostas por regras") : undefined}>{llm ? (llm.ativo ? `🤖 ${llm.modelo} · grátis` : "🤖 modo sem LLM") : ""}</span>
          <button type="button" className="botao-icone" data-ir="config" aria-label="Configurações" title="Configurações" onClick={() => irPara("config")}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d={ENGRENAGEM} /></svg>
          </button>
        </div>
      )}
    </header>
  );
}

export function AvisoDosDados({ aviso }: { aviso: string | null | undefined }) {
  return aviso
    ? <div id="aviso-dados" className="aviso" title={aviso}>⚠️ Preços de exemplo: os mercados e valores ainda são fictícios.</div>
    : <div id="aviso-dados" className="aviso" hidden></div>;
}

const ABAS: { aba: NomeDaAba; classe?: string; rotulo?: string; desenho: React.ReactNode; texto: React.ReactNode }[] = [
  { aba: "inicio", desenho: <path d="M3 11.5 12 4l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" />, texto: <span>Início</span> },
  { aba: "cesta", desenho: <><path d="M3 4h2l2.2 10.2a1 1 0 0 0 1 .8h8.9a1 1 0 0 0 1-.8L20 7H6.2" /><circle cx="9" cy="19" r="1.5" /><circle cx="17" cy="19" r="1.5" /></>, texto: <span>Cesta</span> },
  { aba: "cupom", classe: "aba-central", rotulo: "Enviar cupom", desenho: <><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></>, texto: <span className="aba-central-texto">Cupom</span> },
  { aba: "perto", desenho: <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></>, texto: <span>Perto</span> },
  { aba: "chat", desenho: <path d="M4 5h16v11H9l-5 4z" />, texto: <span>Mia</span> },
];

export function NavegacaoPrincipal({ escondidas }: { escondidas: NomeDaAba[] }) {
  const { aba: atual, irPara } = useNavegacao();
  return (
    <nav className="nav-baixo" role="tablist" aria-label="Navegação principal">
      {ABAS.filter(({ aba }) => !escondidas.includes(aba)).map(({ aba, classe, rotulo, desenho, texto }) => (
        <button key={aba} className={["aba", classe, atual === aba ? "ativa" : ""].filter(Boolean).join(" ")} data-aba={aba} role="tab" aria-selected={atual === aba} aria-label={rotulo} onClick={() => irPara(aba)}>
          <svg viewBox="0 0 24 24" aria-hidden="true">{desenho}</svg>{texto}
        </button>
      ))}
    </nav>
  );
}

export function Rodape() {
  return (
    <footer className="rodape">
      EconoMIA · Challenge 2, Residência em IA Brasília.<br />Orientação para alimentação equilibrada da população geral; não substitui nutricionista.
    </footer>
  );
}
