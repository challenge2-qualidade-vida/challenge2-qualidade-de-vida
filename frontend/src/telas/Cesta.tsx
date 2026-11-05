import { Fragment, useEffect, useRef, useState, type FormEvent } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { mensagemDoProblema } from "../api/problemas";
import { AneisDasMetas } from "../componentes/Aneis";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { CampoDinheiro } from "../componentes/CampoDinheiro";
import { ChipRemovivel } from "../componentes/ChipRemovivel";
import { FotoAlimento } from "../componentes/FotoAlimento";
import { animarCardapio, animarCestaPronta, contarAte } from "../efeitos/animacoes";
import { useCesta, type Cesta as TipoCesta, type PedidoDeCesta } from "../estado/cesta";
import { useDadosDaApi, useNomeDoEstabelecimento } from "../estado/dados-da-api";
import { funcionalidadeLigada } from "../funcionalidades";
import { dataBR, km, reais, semMarkdown } from "../util/formato";

type RespostaDeCardapio = components["schemas"]["RespostaDeCardapio"];
type Periodo = PedidoDeCesta["periodo"];

const NOMES_GRUPOS: Record<string, string> = {
  cereais: "Cereais e pães", tuberculos: "Raízes e tubérculos", leguminosas: "Feijões",
  proteina_animal: "Carnes e ovos", laticinios: "Leite e queijos", flv: "Frutas e hortaliças",
  oleos: "Óleos", acucar: "Açúcar",
};

const textoEtapas = (etapas?: { agente: string; acao: string }[]) => (etapas ?? []).map((e) => `${e.agente}: ${e.acao}`).join(" → ");

/** Valor do cartão: na cesta recomendada recém-montada, sobe contando até o total. */
function ValorDaOpcao({ centavos, contar }: { centavos: number; contar: boolean }) {
  const [mostrado, setMostrado] = useState(centavos);
  useEffect(() => {
    if (!contar) { setMostrado(centavos); return; }
    return contarAte(centavos, setMostrado);
  }, [centavos, contar]);
  return <div className="valor">{reais(mostrado)}</div>;
}

function CartaoDaOpcao({ titulo, cesta, recomendada, extra, contar }: { titulo: string; cesta: TipoCesta | null | undefined; recomendada: boolean; extra?: string; contar?: boolean }) {
  const nome = useNomeDoEstabelecimento();
  return (
    <div className={"cartao opcao" + (recomendada ? " recomendada" : "")}>
      {recomendada && <span className="selo">Recomendada</span>}
      <div className="titulo">{titulo}</div>
      {cesta
        ? <><ValorDaOpcao centavos={cesta.custo_total} contar={!!contar && recomendada} /><div className="detalhe">{cesta.mercados.map(nome).join(" + ") + (extra ? ` · ${extra}` : "")}</div></>
        : <><div className="valor">—</div><div className="detalhe">Sem opção dentro do orçamento</div></>}
    </div>
  );
}

function ListaDeCompras({ cesta }: { cesta: TipoCesta }) {
  const { estabelecimentos } = useDadosDaApi();
  const { tirarAlimento } = useCesta();
  return cesta.mercados.map((id) => (
    <Fragment key={id}>
      <h3 className="mercado-titulo"><span>{`🏪 ${estabelecimentos[id]?.nome ?? id}`}</span><span>{reais(cesta.custo_por_mercado[id])}</span></h3>
      <ul className="itens-lista">
        {cesta.itens.filter((i) => i.mercado_id === id).map((i) => {
          const nome = i.alimento.split(" (")[0];
          return (
            <li className="item" key={i.produto_id + i.mercado_id}>
              <FotoAlimento id={i.alimento_id} classe="item-foto" />
              <span>
                <span className="item-nome">{i.produto}</span>
                <span className="item-detalhe">{`${i.quantidade} × ${reais(i.preco_unitario)} · ${reais(i.preco_kg)}/kg`}</span>
                <span className="item-detalhe">{`Preço de ${dataBR(i.data_preco)} · fonte: ${i.fonte_preco}`}</span>
                <button type="button" className="item-trocar" aria-label={`Trocar ${nome} por outra opção`} onClick={() => tirarAlimento(i.alimento_id, nome)}>🔄 Trocar</button>
              </span>
              <span className="item-valor">{reais(i.subtotal)}<small>{NOMES_GRUPOS[i.grupo] ?? i.grupo}</small></span>
            </li>
          );
        })}
      </ul>
    </Fragment>
  ));
}

function Cardapio({ alimentos, restricoes, ingredientes }: { alimentos: string[]; restricoes: string[]; ingredientes: [string, string][] }) {
  const [dias, setDias] = useState<3 | 7>(3);
  const [estado, setEstado] = useState<{ tipo: "vazio" } | { tipo: "carregando" } | { tipo: "erro"; texto: string } | { tipo: "pronto"; resposta: RespostaDeCardapio }>({ tipo: "vazio" });
  const area = useRef<HTMLDivElement>(null);
  // Cesta nova: o cardápio anterior some, como no site antigo.
  const chave = alimentos.join(",");
  useEffect(() => { setEstado({ tipo: "vazio" }); }, [chave]);
  useEffect(() => { if (estado.tipo === "pronto" && area.current) animarCardapio(area.current); }, [estado]);

  async function sugerir() {
    setEstado({ tipo: "carregando" });
    try {
      setEstado({ tipo: "pronto", resposta: await exigir(api.POST("/cardapios", { body: { alimentos, restricoes, dias } })) });
    } catch (e) {
      setEstado({ tipo: "erro", texto: "Não foi possível montar o cardápio: " + mensagemDoProblema(e) });
    }
  }

  const plano = estado.tipo === "pronto" ? estado.resposta.dados?.cardapio : null;
  const nomesReceitas = estado.tipo === "pronto" ? estado.resposta.dados?.nomes_receitas ?? {} : {};
  return (
    <>
      <div id="ingredientes-cesta" className="ingredientes">
        {ingredientes.map(([id, nome]) => <span className="ingrediente" key={id}><FotoAlimento id={id} classe="foto-ingrediente" />{nome}</span>)}
      </div>
      <label className="campo-cardapio">Cardápio para
        <select id="cardapio-dias" value={dias} onChange={(e) => setDias(Number(e.target.value) as 3 | 7)}><option value="3">3 dias</option><option value="7">7 dias</option></select>
      </label>
      <button type="button" id="botao-cardapio" className="botao largo" disabled={estado.tipo === "carregando"} onClick={sugerir}>Sugerir cardápio</button>
      <div id="cardapio" className="cardapio" ref={area}>
        {estado.tipo === "carregando" && "Montando o cardápio…"}
        {estado.tipo === "erro" && estado.texto}
        {estado.tipo === "pronto" && (plano
          ? <>
              {plano.dias.map((refeicoes, n) => (
                <section className="cardapio-dia" key={n}>
                  <h4>{`Dia ${n + 1}`}</h4>
                  {refeicoes.map((x, k) => (
                    <div className="cardapio-refeicao" key={k}>
                      <span className="cardapio-tipo">{x.titulo}</span>
                      <strong>{nomesReceitas[x.receita]}</strong>
                      <span className="cardapio-fotos">{x.alimentos.slice(0, 5).map((a) => <FotoAlimento key={a} id={a} classe="foto-ingrediente" />)}</span>
                      <span className="item-detalhe">{x.ingredientes.join(", ")}</span>
                      <span className="cardapio-preparo">{x.preparo}</span>
                    </div>
                  ))}
                </section>
              ))}
              {plano.nao_usados.length > 0 && <p className="nota">{`Ficaram para os outros dias: ${plano.nao_usados.join(", ")}.`}</p>}
            </>
          : semMarkdown(estado.resposta.resposta))}
        {estado.tipo === "pronto" && <span className="meta-msg">{textoEtapas(estado.resposta.etapas)}</span>}
      </div>
    </>
  );
}

export function Cesta({ visivel }: { visivel: boolean }) {
  const { opcoes, nomesAlimentos, estabelecimentos } = useDadosDaApi();
  const cesta = useCesta();
  const { plano, pedido, montando, erro, montadaAgora, filtro } = cesta;
  const comDeslocamento = funcionalidadeLigada("deslocamento");

  const [orcamento, setOrcamento] = useState("800");
  const [pessoas, setPessoas] = useState("4");
  const [periodo, setPeriodo] = useState<Periodo>("mes");
  const [restricoes, setRestricoes] = useState<string[]>([]);
  const [custo, setCusto] = useState("10");
  const [alimentoEmCasa, setAlimentoEmCasa] = useState(opcoes.alimentos[0]?.id ?? "");
  const [kgEmCasa, setKgEmCasa] = useState("1");
  const formulario = useRef<HTMLFormElement>(null);
  const tela = useRef<HTMLElement>(null);
  const resultado = useRef<HTMLDivElement>(null);

  // Vindo da tela Perto: usa só os mercados do raio e o custo de ir a um 2º mercado de lá.
  useEffect(() => { if (filtro) setCusto((filtro.deslocamento / 100).toFixed(2)); }, [filtro]);

  function montar(evento?: FormEvent) {
    evento?.preventDefault();
    void cesta.montar({
      orcamento: orcamento ? Math.round(Number(orcamento) * 100) : null,
      pessoas: Number(pessoas),
      periodo,
      restricoes,
      custo_deslocamento: Math.round(Number(custo || 0) * 100),
    });
  }

  // Trocar ou devolver um alimento monta de novo com o mesmo formulário.
  const remontar = useRef(cesta.pedidoDeRemontar);
  useEffect(() => {
    if (remontar.current === cesta.pedidoDeRemontar) return;
    remontar.current = cesta.pedidoDeRemontar;
    montar();
    formulario.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  });

  // Cesta recém-montada: rola até o resultado e anima.
  useEffect(() => {
    if (!montadaAgora || montando || !plano || !tela.current) return;
    resultado.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    animarCestaPronta(tela.current);
  }, [plano, montadaAgora, montando]);

  const recomendada = plano?.recomendacao ? plano.cesta_recomendada : null;
  const casa = (pedido?.em_casa ?? []).map((i) => i.alimento).filter((id) => !recomendada?.itens.some((x) => x.alimento_id === id));
  const alimentosDoCardapio = recomendada ? [...new Set([...recomendada.itens.map((i) => i.alimento_id), ...casa])] : [];
  const ingredientes = recomendada
    ? [...new Map<string, string>([...recomendada.itens.map((i) => [i.alimento_id, i.alimento.split(" (")[0]] as [string, string]), ...casa.map((id) => [id, nomesAlimentos[id]] as [string, string])]).entries()]
    : [];
  const extraDois = plano?.dois_mercados && comDeslocamento && (pedido?.custo_deslocamento ?? 0) > 0 ? `+ ${reais(pedido!.custo_deslocamento!)} de deslocamento` : "";
  const mostrarResultado = !!plano && !montando;

  return (
    <section id="aba-cesta" className="painel" hidden={!visivel} ref={tela}>
      <CabecalhoDaTela gato="miauricio" titulo="Montar cesta" nota="O Miau-ricio monta a cesta mais barata que cumpre as metas." />
      <form id="form-cesta" className="cartao formulario" onSubmit={montar} ref={formulario}>
        <label className="campo">
          <span className="rotulo">💰 Quanto você tem para as compras?</span>
          <CampoDinheiro name="orcamento" valor={orcamento} aoMudar={setOrcamento} passo={10} min={1} nomeNaSeta="o orçamento" placeholder="sem limite" />
        </label>

        <div className="campo">
          <span className="rotulo">👥 Pessoas na casa</span>
          <div className="contador">
            <button type="button" className="contador-botao" data-passo="-1" aria-label="Menos uma pessoa" onClick={() => setPessoas(String(Math.min(20, Math.max(1, Number(pessoas || 1) - 1))))}>−</button>
            <input type="number" name="pessoas" min="1" max="20" value={pessoas} required aria-label="Pessoas na casa" onChange={(e) => setPessoas(e.target.value)} />
            <button type="button" className="contador-botao" data-passo="1" aria-label="Mais uma pessoa" onClick={() => setPessoas(String(Math.min(20, Math.max(1, Number(pessoas || 1) + 1))))}>+</button>
          </div>
        </div>

        <div className="campo">
          <span className="rotulo">📅 Para quanto tempo?</span>
          <div className="segmentado" role="radiogroup">
            {([["semana", "1 semana"], ["quinzena", "15 dias"], ["mes", "1 mês"]] as const).map(([valor, texto]) => (
              <label key={valor}><input type="radio" name="periodo" value={valor} checked={periodo === valor} onChange={() => setPeriodo(valor)} /><span>{texto}</span></label>
            ))}
          </div>
        </div>

        <fieldset className="campo restricoes">
          <legend className="rotulo">🥗 Alguma restrição?</legend>
          <div id="lista-restricoes" className="chips">
            {opcoes.restricoes.map((r) => (
              <label className="chip" key={r.id}><input type="checkbox" name="restricoes" value={r.id} checked={restricoes.includes(r.id)} onChange={(e) => setRestricoes((atual) => e.target.checked ? [...atual, r.id] : atual.filter((x) => x !== r.id))} />{r.nome}</label>
            ))}
          </div>
        </fieldset>

        <details className="mais-opcoes" id="em-casa-opcoes">
          <summary>🏠 O que já tenho em casa</summary>
          <p className="nota">Conta para as metas e sai da conta das compras.</p>
          <div className="em-casa-linha">
            <label className="campo">
              <span className="rotulo">Alimento</span>
              <select id="em-casa-alimento" aria-label="Alimento que tenho em casa" value={alimentoEmCasa} onChange={(e) => setAlimentoEmCasa(e.target.value)}>
                {opcoes.alimentos.map((a) => <option value={a.id} key={a.id}>{a.nome}</option>)}
              </select>
            </label>
            <label className="campo">
              <span className="rotulo">Quantos kg</span>
              <input type="number" id="em-casa-kg" min="0.1" max="200" step="0.1" value={kgEmCasa} inputMode="decimal" onChange={(e) => setKgEmCasa(e.target.value)} />
            </label>
            <button type="button" id="em-casa-adicionar" className="botao-secundario" onClick={() => { const kg = Number(kgEmCasa); if (kg > 0 && kg <= 200) cesta.guardarEmCasa(alimentoEmCasa, kg); }}>Adicionar</button>
          </div>
          <div id="em-casa-lista" className="chips">
            {[...cesta.ingredientesDisponiveis].map(([id, kg]) => (
              <ChipRemovivel key={id} texto={`${String(kg).replace(".", ",")} kg de ${nomesAlimentos[id]}`} rotulo={`Remover ${nomesAlimentos[id]} de casa`} aoRemover={() => cesta.tirarDeCasa(id)} />
            ))}
          </div>
        </details>

        <div id="sem-alimentos-area" className="campo" hidden={cesta.semAlimentos.size === 0}>
          <span className="rotulo">🔄 Fora desta cesta</span>
          <div id="sem-alimentos-lista" className="chips">
            {[...cesta.semAlimentos].map(([id, nome]) => <ChipRemovivel key={id} texto={nome} rotulo={`Devolver ${nome} à cesta`} aoRemover={() => cesta.devolverAlimento(id)} />)}
          </div>
        </div>

        {comDeslocamento && (
          <details className="mais-opcoes">
            <summary>Mais opções</summary>
            <label className="campo">
              <span className="rotulo">🚗 Custo para ir a um 2º mercado</span>
              <CampoDinheiro name="custo_deslocamento" valor={custo} aoMudar={setCusto} passo={1} min={0} nomeNaSeta="o custo" />
            </label>
          </details>
        )}

        {filtro
          ? <p id="filtro-mercados" className="nota">{`Usando só os mercados no seu raio de ${km(filtro.raio_km)}: ${filtro.ids.map((id) => estabelecimentos[id]?.nome ?? id).join(", ")}. `}<button type="button" className="sugestao" id="limpar-filtro" onClick={() => cesta.usarMercados(null)}>usar todos</button></p>
          : <p id="filtro-mercados" className="nota" hidden></p>}
        <button type="submit" className="botao largo" disabled={montando}>Montar minha cesta</button>
      </form>

      <div id="carregando" className="carregando" hidden={!montando}><span className="pulando">🐈</span> Calculando a melhor cesta…</div>
      <div id="erro" className="erro" hidden={!erro}>{erro}</div>

      <div id="resultado" hidden={!mostrarResultado} ref={resultado}>
        <div id="palco-cesta" className="palco palco-cesta" aria-hidden="true"></div>
        <div className="resumo" id="resumo">
          {plano && (recomendada
            ? <>
                <CartaoDaOpcao titulo="Em um só mercado" cesta={plano.um_mercado} recomendada={plano.recomendacao === "um"} contar={montadaAgora} />
                <CartaoDaOpcao titulo="Dividindo em dois mercados" cesta={plano.dois_mercados} recomendada={plano.recomendacao === "dois"} extra={extraDois} contar={montadaAgora} />
                <div className="cartao opcao largura-toda">
                  <div className="titulo">Custo por 1.000 kcal</div>
                  <div className="valor">{reais(recomendada.custo_por_1000_kcal)}</div>
                  <div className="detalhe">{`${reais(recomendada.custo_por_g_proteina)} por grama de proteína`}</div>
                </div>
              </>
            : <CartaoDaOpcao titulo="Orçamento informado" cesta={null} recomendada={false} />)}
        </div>

        {funcionalidadeLigada("nutricao") && (
          <div className="cartao">
            <h2>🎯 Metas nutricionais</h2>
            <div id="metas" className="mini-aneis">{recomendada && <AneisDasMetas cesta={recomendada} />}</div>
          </div>
        )}

        <div className="cartao">
          <h2>🐾 Por que essa cesta?</h2>
          <ul id="explicacao" className="explicacao">{plano?.explicacao.map((f, i) => <li key={i}>{f}</li>)}</ul>
        </div>

        <div className="cartao">
          <h2>📝 Lista de compras</h2>
          <div id="itens">{recomendada && <ListaDeCompras cesta={recomendada} />}</div>
        </div>

        <div className="cartao" id="cartao-cardapio" hidden={!recomendada}>
          <h2><img src="img/miauricio.webp" alt="" className="icone-titulo" /> Cardápio com a sua cesta</h2>
          <p className="nota">O Miau-ricio monta as refeições só com os alimentos da lista, usando primeiro o que estraga mais rápido, e a Mia confere o resultado.</p>
          <Cardapio alimentos={alimentosDoCardapio} restricoes={pedido?.restricoes ?? []} ingredientes={ingredientes} />
        </div>
      </div>
    </section>
  );
}
