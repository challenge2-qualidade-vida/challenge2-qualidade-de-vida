import { useEffect, useRef } from "react";
import { Anel, AneisDasMetas } from "../componentes/Aneis";
import { GatoVivo } from "../componentes/GatoVivo";
import { animarAbertura, animarTurma, semMovimento } from "../efeitos/animacoes";
import { useCesta } from "../estado/cesta";
import { useDadosDaApi } from "../estado/dados-da-api";
import { useNavegacao } from "../estado/navegacao";
import { funcionalidadeLigada } from "../funcionalidades";
import { reais } from "../util/formato";

const TITULO = "Faça seu dinheiro render";

const DICAS: [string, string][] = [
  ["Compare o preço por quilo, não o da embalagem: o pacote maior nem sempre compensa.", "Critérios da EconoMIA"],
  ["Arroz com feijão é uma combinação completa: as proteínas dos dois se complementam.", "Guia Alimentar para a População Brasileira"],
  ["Prefira legumes, verduras e frutas da estação e cultivados localmente.", "Guia Alimentar para a População Brasileira"],
  ["Ovos são acessíveis e relativamente baratos, e podem substituir a carne em várias refeições.", "Guia Alimentar para a População Brasileira"],
  ["Banana muito madura vira vitamina, mingau ou bolo. Não precisa ir para o lixo!", "Aproveitamento de alimentos (EconoMIA)"],
  ["Planeje as refeições antes de ir ao mercado: faça a lista e defina o orçamento antes de sair.", "Critérios da EconoMIA"],
  ["Prefira alimentos in natura ou minimamente processados aos ultraprocessados.", "Guia Alimentar: a regra de ouro"],
];

const PERSONAGENS = [
  { gato: "mia", nome: "Mia", papel: "Verificação", texto: "A parceira inteligente: confere cada resposta para você economizar, planejar e viver melhor." },
  { gato: "cifrao", nome: "Cifrão", papel: "Preços e ofertas", texto: "O gato da rua que sabe onde tem as melhores ofertas e faz o seu dinheiro render." },
  { gato: "miauricio", nome: "Miau-ricio", papel: "Cesta e receitas", texto: "O estrategista que planeja cada compra, cada receita e cada conquista." },
  { gato: "recibaldo", nome: "Recibaldo", papel: "Cupom fiscal", texto: "O fiscal dos gastos: lê o seu cupom e garante que cada centavo valeu." },
] as const;

/** Com movimento, cada palavra fica numa caixa para entrar animada; sem movimento, o texto fica inteiro. */
function TituloDaAbertura() {
  if (semMovimento) return <h1>{TITULO}</h1>;
  const palavras = TITULO.split(/\s+/);
  return (
    <h1 aria-label={TITULO}>
      {palavras.flatMap((p, i) => {
        const caixa = <span className="palavra" aria-hidden="true" key={i}><span>{p}</span></span>;
        return i ? [" ", caixa] : [caixa];
      })}
    </h1>
  );
}

function UltimaCesta() {
  const { plano, pedido } = useCesta();
  const { estabelecimentos } = useDadosDaApi();
  const { irPara } = useNavegacao();
  const cesta = plano?.recomendacao ? plano.cesta_recomendada : null;
  if (!plano || !pedido || !cesta) {
    return (
      <div className="cartao" id="inicio-resumo" hidden>
        <div className="cartao-cabecalho"><h2>Sua última cesta</h2><button type="button" className="link" data-ir="cesta" onClick={() => irPara("cesta")}>ver lista</button></div>
        <div className="anel-linha"><Anel className="anel anel-grande" id="anel-orcamento"><div className="anel-centro"><b id="anel-orcamento-valor"></b><small>do orçamento</small></div></Anel><div className="anel-legenda" id="inicio-legenda"></div></div>
        <div className="mini-aneis" id="inicio-metas"></div>
      </div>
    );
  }
  const gasto = cesta.custo_total + (plano.recomendacao === "dois" ? plano.custo_deslocamento ?? 0 : 0);
  const mercados = cesta.mercados.map((id) => estabelecimentos[id]?.nome ?? id).join(" + ");
  const pct = pedido.orcamento ? Math.round((gasto / pedido.orcamento) * 100) : null;
  return (
    <div className="cartao" id="inicio-resumo">
      <div className="cartao-cabecalho"><h2>Sua última cesta</h2><button type="button" className="link" data-ir="cesta" onClick={() => irPara("cesta")}>ver lista</button></div>
      <div className="anel-linha">
        <Anel className="anel anel-grande" id="anel-orcamento" pct={pct === null ? 100 : Math.min(pct, 100)} cor={pct === null ? undefined : "var(--marca)"}>
          <div className="anel-centro"><b id="anel-orcamento-valor">{pct === null ? reais(gasto) : `${pct}%`}</b><small>do orçamento</small></div>
        </Anel>
        <div className="anel-legenda" id="inicio-legenda">
          {pedido.orcamento ? <><b>{reais(gasto)}</b>{`de ${reais(pedido.orcamento)} · ${mercados}`}</> : <><b>Sem limite</b>{mercados}</>}
        </div>
      </div>
      <div className="mini-aneis" id="inicio-metas">{funcionalidadeLigada("nutricao") && <AneisDasMetas cesta={cesta} />}</div>
    </div>
  );
}

export function Inicio({ visivel }: { visivel: boolean }) {
  const { irPara, perguntar } = useNavegacao();
  const { fala } = useCesta();
  const palco = useRef<HTMLDivElement>(null);
  const turma = useRef<HTMLDivElement>(null);
  const [dica, fonte] = DICAS[new Date().getDate() % DICAS.length];

  useEffect(() => (palco.current ? animarAbertura(palco.current) : undefined), []);
  useEffect(() => turma.current ? animarTurma([...turma.current.querySelectorAll<HTMLElement>(".personagem")]) : undefined, []);

  return (
    <section id="aba-inicio" className="painel" hidden={!visivel}>
      <div id="palco-hero" className="hero" ref={palco}>
        <div className="hero-conteudo">
          <TituloDaAbertura />
          <p className="hero-texto">Diga quanto você tem. A EconoMIA monta a cesta mais barata que cumpre as metas de nutrição e mostra onde comprar.</p>
          <button type="button" className="botao botao-hero" data-ir="cesta" onClick={() => irPara("cesta")}>Montar minha cesta</button>
        </div>
        <div className="hero-palco">
          <GatoVivo nome="mia" src="img/gatos3d/mia.webp" alt="Mia, a gata da EconoMIA" className="hero-gato" />
          <div id="ancora-cesta-hero" aria-hidden="true"></div>
        </div>
      </div>

      <div className="mascote-cartao">
        <div className="mascote"><GatoVivo nome="mia" src="img/mia.webp" alt="Mia, a gata da EconoMIA" /><span className="humor" id="mascote" aria-hidden="true">{fala.rosto}</span></div>
        <div className="balao" id="balao">{fala.frase}</div>
      </div>

      <UltimaCesta />

      <h2 className="secao">O que você quer fazer?</h2>
      <div className="acoes">
        <button type="button" className="acao acao-laranja" data-ir="cesta" onClick={() => irPara("cesta")}><GatoVivo nome="miauricio" src="img/miauricio.webp" className="acao-gato" /><b>Montar cesta</b><small>O Miau-ricio planeja</small></button>
        {funcionalidadeLigada("perto") && <button type="button" className="acao acao-verde" data-ir="perto" onClick={() => irPara("perto")}><GatoVivo nome="cifrao" src="img/cifrao.webp" className="acao-gato" /><b>Achar ofertas perto de mim</b><small>O Cifrão acha ofertas</small></button>}
        {funcionalidadeLigada("promocao") && <button type="button" className="acao acao-roxo" data-pergunta="Essa promoção vale a pena? " onClick={() => perguntar("Essa promoção vale a pena? ")}><GatoVivo nome="mia" src="img/mia.webp" className="acao-gato" /><b>Essa promoção vale?</b><small>Pergunte para a Mia</small></button>}
        <button type="button" className="acao acao-azul" data-ir="cupom" onClick={() => irPara("cupom")}><GatoVivo nome="recibaldo" src="img/recibaldo.webp" className="acao-gato" /><b>Enviar cupom</b><small>O Recibaldo confere</small></button>
      </div>

      <section className="cartao turma" aria-labelledby="titulo-turma">
        <div className="turma-banner"><img src="img/turma.webp" alt="Mia, Recibaldo, Cifrão e Miau-ricio juntos" /></div>
        <h2 id="titulo-turma">Conheça a turma</h2>
        <p className="nota">Quatro agentes de IA, cada um com uma missão.</p>
        <div className="personagens" ref={turma}>
          {PERSONAGENS.map((p) => (
            <article className="personagem" key={p.gato}>
              <div className="personagem-foto"><GatoVivo nome={p.gato} src={`img/${p.gato}.webp`} /></div>
              <h3>{p.nome}</h3>
              <span className="papel">{p.papel}</span>
              <p>{p.texto}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="cartao dica">
        <span className="dica-emoji" aria-hidden="true">💡</span>
        <div>
          <b>Dica do dia</b>
          <p id="dica-texto">{dica}</p>
          <small id="dica-fonte" className="suave">{"Fonte: " + fonte}</small>
        </div>
      </div>

      {funcionalidadeLigada("precos") && <button type="button" className="botao-secundario largo" data-ir="precos" onClick={() => irPara("precos")}>📊 Ver tabela de preços</button>}
    </section>
  );
}
