// Fora do MVP do grupo (deslocamento e preços dos mercados): só aparece com a flag "perto".
import { useEffect, useRef, useState } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { mensagemDoProblema } from "../api/problemas";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { FotoAlimento } from "../componentes/FotoAlimento";
import { useCesta } from "../estado/cesta";
import { useConfiguracoes, type Ordem } from "../estado/configuracoes";
import { useDadosDaApi, useNomeDoEstabelecimento } from "../estado/dados-da-api";
import { useNavegacao } from "../estado/navegacao";
import { usePosicao } from "../estado/posicao";
import { dataBR, km, reais } from "../util/formato";

type MercadosProximos = components["schemas"]["MercadosProximos"];
type MercadoProximo = components["schemas"]["MercadoProximo"];
type SupermercadosDoMapa = components["schemas"]["SupermercadosDoMapa"];

const NOMES_GRUPOS_PROTEINA: Record<string, string> = { proteina_animal: "Carnes e ovos", laticinios: "Leite e queijos", leguminosas: "Feijões" };
const NOMES_SELOS: Record<string, string> = { mais_perto: "📍 Mais perto", melhor_preco: "💰 Menor preço", melhor_custo_beneficio: "⭐ Melhor custo-benefício" };
const DESTAQUE: Record<Ordem, string> = { distancia: "mais_perto", preco: "melhor_preco", custo_beneficio: "melhor_custo_beneficio" };
const OPCOES_DE_ORDEM: [Ordem, string][] = [["custo_beneficio", "Custo-benefício"], ["preco", "Menor preço"], ["distancia", "Mais perto"]];

function ordenar(lista: MercadoProximo[], ordem: Ordem) {
  const chave = {
    distancia: (m: MercadoProximo) => m.distancia_km,
    preco: (m: MercadoProximo) => m.carrinho_proteinas ?? Infinity,
    custo_beneficio: (m: MercadoProximo) => m.custo_real ?? Infinity,
  }[ordem];
  return [...lista].sort((a, b) => chave(a) - chave(b) || a.distancia_km - b.distancia_km);
}

const emReais = (v: number | null | undefined) => (v != null ? reais(v) : "—");

function Mercado({ m, ordem }: { m: MercadoProximo; ordem: Ordem }) {
  const valor = ordem === "distancia"
    ? <div className="mercado-valor">{km(m.distancia_km)}<small>de distância</small></div>
    : ordem === "preco"
      ? <div className="mercado-valor">{emReais(m.carrinho_proteinas)}<small>carrinho de proteínas</small></div>
      : <div className="mercado-valor">{emReais(m.custo_real)}<small>custo real</small></div>;
  return (
    <article className={"mercado" + (m.selos.includes(DESTAQUE[ordem] as MercadoProximo["selos"][number]) ? " destaque" : "")}>
      <div className="mercado-nome">{m.nome}</div>
      {valor}
      <div className="mercado-local">{m.regiao}</div>
      <div className="mercado-numeros">
        <span>{"📍 "}<b>{km(m.distancia_km)}</b></span>
        <span>{"🚗 ida e volta "}<b>{reais(m.custo_ida_volta)}</b></span>
        <span>{"🛒 proteínas "}<b>{emReais(m.carrinho_proteinas)}</b></span>
        <span>{"= "}<b>{emReais(m.custo_real)}</b></span>
      </div>
      {m.selos.length ? <div className="selos">{m.selos.map((s) => <span key={s} className={`selo-mercado selo-${s}`}>{NOMES_SELOS[s]}</span>)}</div> : ""}
    </article>
  );
}

function Proteinas({ r }: { r: MercadosProximos }) {
  const nome = useNomeDoEstabelecimento();
  const p = r.proteinas;
  if (!p) return null;
  const ids = r.mercados.map((m) => m.id);
  const maisBarata = p.alimentos[0];
  return (
    <>
      <h2 className="secao">🥩 Onde a proteína está mais barata</h2>
      <div id="resumo-proteinas" className="resumo">
        {p.carrinho.melhor_mercado && (
          <div className="cartao opcao recomendada">
            <span className="selo">Melhor para proteínas</span>
            <div className="titulo">{`1 kg de cada: ${p.carrinho.itens.join(", ")}`}</div>
            <div className="valor">{nome(p.carrinho.melhor_mercado)}</div>
            <div className="detalhe">{Object.entries(p.carrinho.total_por_mercado).map(([m, v]) => `${nome(m)}: ${reais(v)}`).join(" · ")}</div>
          </div>
        )}
        {maisBarata && (
          <div className="cartao opcao com-foto">
            <FotoAlimento id={maisBarata.alimento_id} classe="foto-destaque" />
            <div className="titulo">Proteína mais barata</div>
            <div className="valor">{maisBarata.alimento}</div>
            <div className="detalhe">{`${reais(maisBarata.precos[maisBarata.melhor_mercado].custo_100g_proteina)} por 100 g de proteína no ${nome(maisBarata.melhor_mercado)}`}</div>
          </div>
        )}
      </div>
      <div className="cartao">
        <p className="nota">Menor preço por kg em cada mercado e quanto custam 100 g de proteína. Da proteína mais barata para a mais cara.</p>
        <div className="tabela-rolagem"><table className="tabela" id="tabela-proteinas">
          <thead><tr><th>Alimento</th>{ids.map((id) => <th className="num" key={id}>{nome(id)}</th>)}<th className="num">Economia no melhor</th></tr></thead>
          <tbody>
            {p.alimentos.map((a) => (
              <tr key={a.alimento_id}>
                <td><div className="celula-produto"><FotoAlimento id={a.alimento_id} classe="foto-mini" /><span>{a.alimento}<span className="fonte">{`${NOMES_GRUPOS_PROTEINA[a.grupo]} · ${String(a.proteina_100g).replace(".", ",")} g de proteína/100 g`}</span></span></div></td>
                {ids.map((id) => {
                  const v = a.precos[id];
                  if (!v) return <td className="num" key={id}>—</td>;
                  return (
                    <td className={"num" + (id === a.melhor_mercado && Object.keys(a.precos).length > 1 ? " melhor" : "")} key={id}>
                      {`${reais(v.preco_kg)}/kg`}<span className="fonte">{`${reais(v.custo_100g_proteina)} por 100 g de proteína · ${dataBR(v.data)} · ${v.fonte}`}</span>
                    </td>
                  );
                })}
                <td className="num">{a.economia_vs_mais_caro_pct > 0 ? `${String(a.economia_vs_mais_caro_pct).replace(".", ",")}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>
    </>
  );
}

function SupermercadosDaRegiao({ lat, lon }: { lat: number; lon: number }) {
  const { salvas } = useConfiguracoes();
  const { irPara } = useNavegacao();
  const [estado, setEstado] = useState<{ tipo: "vazio" } | { tipo: "texto"; texto: string } | { tipo: "pronto"; r: SupermercadosDoMapa }>({ tipo: "vazio" });
  useEffect(() => { setEstado({ tipo: "vazio" }); }, [lat, lon, salvas.raio_km]);

  async function buscar() {
    setEstado({ tipo: "texto", texto: "Consultando o OpenStreetMap…" });
    try {
      const r = await exigir(api.GET("/mercados/mapa", { params: { query: { lat: Number(lat.toFixed(2)), lon: Number(lon.toFixed(2)), raio_km: Math.min(salvas.raio_km, 10) } } }));
      setEstado(r.supermercados.length ? { tipo: "pronto", r } : { tipo: "texto", texto: "Nenhum supermercado encontrado no mapa nessa área." });
    } catch (e) {
      setEstado({ tipo: "texto", texto: mensagemDoProblema(e) });
    }
  }

  return (
    <>
      <button type="button" id="botao-osm" className="botao-secundario largo" disabled={estado.tipo === "texto" && estado.texto.startsWith("Consultando")} onClick={buscar}>Buscar supermercados no mapa</button>
      <div id="lista-osm">
        {estado.tipo === "texto" && estado.texto}
        {estado.tipo === "pronto" && <>
          <p className="nota">{salvas.raio_km > 10 ? "Mostrando até 10 km (limite do mapa gratuito)." : ""}</p>
          <ul className="explicacao">
            {estado.r.supermercados.slice(0, 20).map((m) => (
              <li key={m.nome}>{`${m.nome} — ${km(m.distancia_km)} `}<span className={m.tem_precos ? "confianca-alta" : "confianca-revisar"}>{m.tem_precos ? "tem preços" : "sem preços ainda"}</span></li>
            ))}
          </ul>
          <p className="nota">{`Fonte: ${estado.r.fonte}. Conhece algum desses? `}<button type="button" className="sugestao" id="ir-cupom" onClick={() => irPara("cupom")}>Enviar um cupom</button></p>
        </>}
      </div>
    </>
  );
}

export function Perto({ visivel }: { visivel: boolean }) {
  const { regioes } = useDadosDaApi();
  const { config, salvas } = useConfiguracoes();
  const { posicao, definir } = usePosicao();
  const { usarMercados } = useCesta();
  const { irPara } = useNavegacao();
  const [regiao, setRegiao] = useState("");
  const [status, setStatus] = useState("");
  const [resultado, setResultado] = useState<MercadosProximos | null>(null);

  async function buscar(lat: number, lon: number, origem: string) {
    definir({ lat, lon, origem });
    const raio = salvas.raio_km;
    setStatus(`Buscando mercados a até ${km(raio)} de ${origem}…`);
    try {
      const r = await exigir(api.GET("/mercados/proximos", { params: { query: { lat: Number(lat.toFixed(4)), lon: Number(lon.toFixed(4)), raio_km: raio, custo_por_km: salvas.custo_por_km } } }));
      if (!r.mercados.length) {
        const dica = r.mais_proximo_fora_do_raio_km
          ? ` O mercado mais próximo com preços fica a ${km(r.mais_proximo_fora_do_raio_km)}: aumente o raio nas Configurações.`
          : " Envie um cupom de um mercado da sua região para ele aparecer aqui.";
        setStatus(`Nenhum mercado com preços a até ${km(raio)} de ${origem}.` + dica);
        setResultado(null);
        return;
      }
      setStatus(`${r.mercados.length} de ${r.total_com_localizacao} mercados com preços ficam a até ${km(raio)} de ${origem}.`);
      setResultado(r);
    } catch (e) {
      setStatus("Erro: " + mensagemDoProblema(e));
    }
  }

  // Ao abrir sem posição, usa a região padrão das Configurações.
  useEffect(() => {
    if (!visivel || posicao || !salvas.regiao) return;
    setRegiao(salvas.regiao);
    const [lat, lon] = salvas.regiao.split(",").map(Number);
    void buscar(lat, lon, regioes.find((r) => `${r.lat},${r.lon}` === salvas.regiao)?.nome ?? "região padrão");
  }, [visivel]); // eslint-disable-line react-hooks/exhaustive-deps

  // Raio ou custo por km salvos de novo: refaz a busca.
  const primeira = useRef(true);
  useEffect(() => {
    if (primeira.current) { primeira.current = false; return; }
    if (posicao) void buscar(posicao.lat, posicao.lon, posicao.origem);
  }, [salvas.raio_km, salvas.custo_por_km]); // eslint-disable-line react-hooks/exhaustive-deps

  function usarLocalizacao() {
    if (!navigator.geolocation) {
      setStatus("Seu navegador não permite localização. Escolha a região.");
      return;
    }
    setStatus("Pedindo permissão de localização…");
    navigator.geolocation.getCurrentPosition(
      (p) => void buscar(p.coords.latitude, p.coords.longitude, "sua localização"),
      () => setStatus("Não foi possível pegar a localização. Escolha a região."),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  }

  return (
    <section id="aba-perto" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="cifrao" titulo="Perto de mim" nota="O Cifrão mostra onde a proteína está mais barata." />
      <div id="palco-perto" className="palco" aria-hidden="true"></div>
      <div className="cartao">
        <button type="button" id="botao-localizacao" className="botao largo" onClick={usarLocalizacao}>📍 Usar minha localização</button>
        <p className="nota centro">Sua localização é usada só para calcular distâncias e não é guardada.</p>
        <label className="campo">
          <span className="rotulo">…ou escolha a região</span>
          <select id="regiao" value={regiao} onChange={(e) => {
            setRegiao(e.target.value);
            if (!e.target.value) return;
            const [lat, lon] = e.target.value.split(",").map(Number);
            void buscar(lat, lon, e.target.selectedOptions[0].textContent ?? "");
          }}>
            <option value="">—</option>
            {regioes.map((r) => <option value={`${r.lat},${r.lon}`} key={r.id}>{r.nome}</option>)}
          </select>
        </label>
        <button type="button" className="raio-chip" data-ir="config" onClick={() => irPara("config")}>
          <span>📏 Buscando num raio de <b id="raio-atual">{km(config.raio_km)}</b></span><span className="raio-chip-acao">Alterar</span>
        </button>
        <div id="status-perto" className="nota">{status}</div>
      </div>

      <div id="resultado-perto" hidden={!resultado}>
        {resultado && posicao && <>
          <h2 className="secao">🏪 Mercados no seu raio</h2>
          <OrdemDosMercados nome="ordem-perto" />
          <div id="lista-mercados" className="lista-mercados">{ordenar(resultado.mercados, config.ordem).map((m) => <Mercado key={m.id} m={m} ordem={config.ordem} />)}</div>
          <p className="nota">Preço = 1 kg de cada proteína que todos os mercados do raio têm. Custo real = preço + ida e volta de carro.</p>
          <button type="button" id="botao-cesta-perto" className="botao largo" onClick={() => {
            usarMercados({ ids: resultado.mercados.map((m) => m.id), deslocamento: resultado.custo_segundo_mercado, raio_km: salvas.raio_km });
            irPara("cesta");
          }}>Montar cesta só com esses mercados</button>

          <Proteinas r={resultado} />

          <h2 className="secao">🗺️ Outros supermercados da região</h2>
          <div className="cartao">
            <p className="nota">Lista do OpenStreetMap. Os que ainda não têm preços passam a ter quando alguém envia um cupom.</p>
            <SupermercadosDaRegiao lat={posicao.lat} lon={posicao.lon} />
          </div>
        </>}
      </div>
    </section>
  );
}

/** Ordenação dos mercados: aparece no Perto e nas Configurações, sempre sincronizada. */
export function OrdemDosMercados({ nome, rotulo = "Ordenar mercados", pequeno = true }: { nome: string; rotulo?: string; pequeno?: boolean }) {
  const { config, salvar } = useConfiguracoes();
  return (
    <div className={pequeno ? "segmentado segmentado-pequeno" : "segmentado"} role="radiogroup" aria-label={rotulo}>
      {OPCOES_DE_ORDEM.map(([valor, texto]) => (
        <label key={valor}><input type="radio" name={nome} value={valor} checked={config.ordem === valor} onChange={() => salvar({ ordem: valor })} /><span>{texto}</span></label>
      ))}
    </div>
  );
}
