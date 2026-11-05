import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api, exigir } from "../api/cliente";
import { mensagemDoProblema } from "../api/problemas";
import { enviarPedido, type BlocosDaResposta } from "../api/sse";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { FotoAlimento } from "../componentes/FotoAlimento";
import { useNavegacao } from "../estado/navegacao";
import { funcionalidadeLigada } from "../funcionalidades";
import { reais, semMarkdown } from "../util/formato";

const NOMES_FERRAMENTAS: Record<string, string> = {
  montar_cesta: "montou a cesta", consultar_precos: "consultou preços",
  avaliar_promocao: "avaliou a promoção", buscar_conhecimento: "buscou na base",
};
const AVATARES: Record<string, string> = { "Cifrão": "cifrao", "Miau-ricio": "miauricio", "Recibaldo": "recibaldo" };
const SUGESTOES: { texto: string; promocao?: boolean }[] = [
  { texto: "Tenho R$ 600 para o mês, somos 4 pessoas" },
  { texto: "Arroz 5 kg por R$ 24,90 é uma boa promoção?", promocao: true },
  { texto: "O que fazer com banana muito madura?" },
  { texto: "O que são alimentos ultraprocessados?" },
];

interface Mensagem {
  id: number;
  quem: "usuario" | "assistente";
  texto: string;
  gato?: string;
  pensando?: boolean;
  blocos?: BlocosDaResposta;
}

/* Os "dados" de cada ferramenta vêm do agente; aqui só lemos os campos que a tela mostra. */
interface DadosDasFerramentas {
  montar_cesta?: { itens_detalhe?: { alimento_id: string; quantidade: number; produto: string; mercado: string; subtotal: number }[] };
  consultar_precos?: { produtos?: { alimento_id: string; produto: string; ofertas: { mercado: string; preco: number; preco_kg: number }[] }[] };
  avaliar_promocao?: { alimento_id?: string; alimento: string; conclusao: string; melhor_preco_kg_normal: number; preco_kg_promocao: number };
}

/** Alimentos recomendados ou com preço na resposta, com foto. */
function CartoesDaResposta({ dados }: { dados: DadosDasFerramentas }) {
  const linhas: ReactNode[] = [];
  for (const i of dados.montar_cesta?.itens_detalhe ?? []) {
    linhas.push(<li key={"c" + i.alimento_id}><FotoAlimento id={i.alimento_id} classe="foto-mini" /><span>{`${i.quantidade} × ${i.produto}`}<small>{i.mercado}</small></span><b>{reais(i.subtotal)}</b></li>);
  }
  for (const p of dados.consultar_precos?.produtos ?? []) {
    const melhor = p.ofertas[0];
    linhas.push(<li key={"p" + p.alimento_id}><FotoAlimento id={p.alimento_id} classe="foto-mini" /><span>{p.produto}<small>{`${melhor.mercado} · ${reais(melhor.preco_kg)}/kg`}</small></span><b>{reais(melhor.preco)}</b></li>);
  }
  const promo = dados.avaliar_promocao;
  if (promo?.alimento_id) {
    const veredito = ({ vale_a_pena: "✅ vale a pena", empate: "➖ empate", nao_vale: "❌ não vale" } as Record<string, string>)[promo.conclusao] ?? "";
    linhas.push(<li key="promo"><FotoAlimento id={promo.alimento_id} classe="foto-mini" /><span>{promo.alimento}<small>{`normal: ${reais(promo.melhor_preco_kg_normal)}/kg · ${veredito}`}</small></span><b>{`${reais(promo.preco_kg_promocao)}/kg`}</b></li>);
  }
  return linhas.length ? <ul className="chat-itens">{linhas}</ul> : null;
}

function rodape(blocos: BlocosDaResposta) {
  const meta: string[] = [];
  if (blocos.ferramentas_usadas?.length) meta.push("A EconoMIA " + [...new Set(blocos.ferramentas_usadas)].map((f) => NOMES_FERRAMENTAS[f] ?? f).join(", "));
  if (blocos.fontes?.length) meta.push("Fontes: " + [...new Set(blocos.fontes.map((f) => f.fonte))].join("; "));
  if (blocos.agentes?.length) meta.push("Agentes: " + blocos.agentes.map((e) => `${e.agente}: ${e.acao}`).join(" → "));
  if (blocos.aviso) meta.push("⚠️ " + blocos.aviso);
  return meta.join(" · ");
}

function LinhaDaMensagem({ m, fim }: { m: Mensagem; fim: (no: HTMLElement | null) => void }) {
  const corpo = (ref?: (no: HTMLElement | null) => void) => (
    <div className={`msg ${m.quem}${m.pensando ? " pensando" : ""}`} ref={ref}>
      {m.texto}
      {m.blocos?.dados && <CartoesDaResposta dados={m.blocos.dados as DadosDasFerramentas} />}
      {m.blocos && rodape(m.blocos) && <span className="meta-msg">{rodape(m.blocos)}</span>}
    </div>
  );
  // A mensagem da pessoa não tem avatar, como no site antigo.
  if (!m.gato) return corpo(fim);
  return <div className="linha-msg" ref={fim}><img src={`img/${m.gato}.webp`} alt="" className="avatar" />{corpo()}</div>;
}

export function Conversa({ visivel }: { visivel: boolean }) {
  const { perguntaPendente, limparPergunta } = useNavegacao();
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const conversa = useRef<string | null>(null);
  const campo = useRef<HTMLInputElement>(null);
  const contador = useRef(0);

  // Atalho "Essa promoção vale?": o texto entra no campo, pronto para completar.
  useEffect(() => {
    if (perguntaPendente === null || !visivel) return;
    setTexto(perguntaPendente);
    campo.current?.focus();
    limparPergunta();
  }, [perguntaPendente, visivel, limparPergunta]);

  const atualizar = (id: number, mudanca: Partial<Mensagem>) => setMensagens((ms) => ms.map((m) => (m.id === id ? { ...m, ...mudanca } : m)));

  async function enviar(pedido: string) {
    const idPessoa = ++contador.current, idResposta = ++contador.current;
    setMensagens((ms) => [...ms,
      { id: idPessoa, quem: "usuario", texto: pedido },
      { id: idResposta, quem: "assistente", texto: "Pensando… (o LLM local pode levar alguns segundos)", gato: "mia", pensando: true }]);
    setEnviando(true);
    try {
      conversa.current ??= (await exigir(api.POST("/conversas"))).id;
      let resposta = "";
      for await (const evento of await enviarPedido(conversa.current, pedido)) {
        if (evento.tipo === "texto") {
          resposta += evento.texto;
          atualizar(idResposta, { texto: semMarkdown(resposta), pensando: false });
        } else if (evento.tipo === "blocos") {
          const quem = (evento.blocos.agentes ?? []).map((e) => e.agente).find((a) => AVATARES[a]);
          atualizar(idResposta, { blocos: evento.blocos, gato: quem ? AVATARES[quem] : "mia" });
        } else if (evento.tipo === "erro") {
          throw evento.problema;
        }
      }
    } catch (e) {
      atualizar(idResposta, { texto: "Desculpe, algo deu errado: " + mensagemDoProblema(e), pensando: false, gato: "mia", blocos: undefined });
    } finally {
      setEnviando(false);
    }
  }

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    const pedido = texto.trim();
    if (!pedido) return;
    setTexto("");
    void enviar(pedido);
  }

  const rolarAteOFim = (no: HTMLElement | null) => no?.scrollIntoView({ behavior: "smooth", block: "end" });

  return (
    <section id="aba-chat" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="mia" titulo="Conversar" nota="A Mia chama o Cifrão ou o Miau-ricio e confere a resposta." />
      <div className="chat">
        <div id="mensagens" className="mensagens" aria-live="polite">
          <div className="linha-msg"><img src="img/mia.webp" alt="" className="avatar" /><div className="msg assistente">Oi! Me conte quanto você tem para as compras, quantas pessoas moram na casa e se há alguma restrição. Também digo se uma promoção vale a pena e tiro dúvidas sobre alimentação.</div></div>
          {mensagens.map((m, i) => <LinhaDaMensagem key={m.id} m={m} fim={i === mensagens.length - 1 ? rolarAteOFim : () => {}} />)}
        </div>
        <div className="sugestoes" id="sugestoes">
          {SUGESTOES.filter((s) => !s.promocao || funcionalidadeLigada("promocao")).map((s) => (
            <button type="button" className="sugestao" key={s.texto} onClick={() => void enviar(s.texto)}>{s.texto}</button>
          ))}
        </div>
        <form id="form-chat" className="form-chat" onSubmit={aoEnviar}>
          <input type="text" name="mensagem" maxLength={1000} placeholder="Escreva sua pergunta…" autoComplete="off" required value={texto} onChange={(e) => setTexto(e.target.value)} ref={campo} />
          <button type="submit" className="botao botao-redondo" aria-label="Enviar" disabled={enviando}>➤</button>
        </form>
      </div>
    </section>
  );
}
