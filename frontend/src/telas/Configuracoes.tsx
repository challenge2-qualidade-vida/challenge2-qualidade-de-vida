import { useEffect, useState, type CSSProperties } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { FotoAlimento } from "../componentes/FotoAlimento";
import { useConfiguracoes } from "../estado/configuracoes";
import { useDadosDaApi } from "../estado/dados-da-api";
import { usePontoDePartida } from "../estado/posicao";
import { funcionalidadeLigada } from "../funcionalidades";
import { km, reais } from "../util/formato";
import { OrdemDosMercados } from "./Perto";

type MercadoProximo = components["schemas"]["MercadoProximo"];
type CreditoDeFoto = components["schemas"]["CreditoDeFoto"];

const progresso = (valor: number, min: number, max: number) => ({ "--progresso": `${((valor - min) / (max - min)) * 100}%` }) as CSSProperties;

/** Prévia do raio: os mercados com preço, a partir do ponto de partida, até o raio máximo. */
function Radar({ raio, todos }: { raio: number; todos: MercadoProximo[] | null }) {
  const c = 120, maxR = 104;
  const longe = Math.max(raio, ...(todos ?? []).map((m) => m.distancia_km)) * 1.08;
  const r = Math.max(10, (raio / longe) * maxR);
  return (
    <svg id="radar" viewBox="0 0 240 240" role="img" aria-label="Prévia do raio de busca">
      <circle cx={c} cy={c} r={maxR + 8} fill="var(--fundo)" />
      {[0.33, 0.66, 1].map((f) => <circle key={f} cx={c} cy={c} r={maxR * f} fill="none" stroke="var(--borda)" strokeDasharray="3 4" />)}
      <circle cx={c} cy={c} r={r} fill="color-mix(in srgb, var(--marca) 18%, transparent)" stroke="var(--marca)" strokeWidth={2} />
      {(todos ?? []).map((m) => {
        const d = (m.distancia_km / longe) * maxR, ang = ((m.rumo_graus - 90) * Math.PI) / 180;
        const noRaio = m.distancia_km <= raio;
        return <circle key={m.id} cx={c + d * Math.cos(ang)} cy={c + d * Math.sin(ang)} r={6} fill={noRaio ? "var(--marca)" : "var(--suave)"} stroke="var(--cartao)" strokeWidth={2}><title>{`${m.nome} — ${km(m.distancia_km)}`}</title></circle>;
      })}
      <circle cx={c} cy={c} r={7} fill="var(--azul)" stroke="var(--cartao)" strokeWidth={3} />
    </svg>
  );
}

function RaioDeBusca() {
  const { limites } = useDadosDaApi();
  const { config, salvas, ajustar, salvar } = useConfiguracoes();
  const ponto = usePontoDePartida();
  const [todos, setTodos] = useState<MercadoProximo[] | null>(null);
  const min = limites?.raio_km.minimo ?? 1, max = limites?.raio_km.maximo ?? 100;

  useEffect(() => {
    setTodos(null);
    if (!ponto) return;
    let vivo = true;
    exigir(api.GET("/mercados/proximos", { params: { query: { lat: Number(ponto.lat.toFixed(4)), lon: Number(ponto.lon.toFixed(4)), raio_km: max, custo_por_km: salvas.custo_por_km } } }))
      .then((r) => { if (vivo) setTodos(r.mercados); }).catch(() => { /* radar fica vazio */ });
    return () => { vivo = false; };
  }, [ponto?.lat, ponto?.lon, max, salvas.custo_por_km]); // eslint-disable-line react-hooks/exhaustive-deps

  const dentro = (todos ?? []).filter((m) => m.distancia_km <= config.raio_km).length;
  const fora = (todos ?? []).filter((m) => m.distancia_km > config.raio_km).sort((a, b) => a.distancia_km - b.distancia_km);
  return (
    <div className="cartao">
      <div className="cartao-cabecalho"><h2>📏 Raio de busca</h2><span className="valor-grande"><b id="cfg-raio-valor">{config.raio_km}</b> km</span></div>
      <input type="range" id="cfg-raio" className="deslizante" min={min} max={max} step="1" value={config.raio_km} aria-label="Raio de busca em km" style={progresso(config.raio_km, min, max)}
        onChange={(e) => ajustar({ raio_km: Number(e.target.value) })}
        onPointerUp={(e) => salvar({ raio_km: Number(e.currentTarget.value) })}
        onKeyUp={(e) => salvar({ raio_km: Number(e.currentTarget.value) })} />
      <div className="escala"><span>1 km</span><span>25</span><span>50</span><span>75</span><span>100 km</span></div>
      <div className="chips atalhos" id="cfg-raio-atalhos">
        {[2, 5, 10, 25, 50, 100].map((v) => <button type="button" key={v} className={"chip" + (config.raio_km === v ? " ativo" : "")} data-km={v} onClick={() => salvar({ raio_km: v })}>{`${v} km`}</button>)}
      </div>
      <div className="radar-area">
        <Radar raio={config.raio_km} todos={todos} />
        <div>
          <p id="radar-resumo" className="radar-resumo">{ponto ? `${dentro} de ${todos?.length ?? 0} mercados com preço ficam no raio de ${km(config.raio_km)}` : `Raio de ${km(config.raio_km)}`}</p>
          <p id="radar-ponto" className="nota">{ponto
            ? `Medido a partir de: ${ponto.origem}.` + (fora.length ? ` O próximo mercado fora do raio fica a ${km(fora[0].distancia_km)}.` : "")
            : "Escolha um ponto de partida (localização ou região) para ver quantos mercados ficam no raio."}</p>
          <p className="nota">A lista do mapa (OpenStreetMap) vai até 10 km, para não sobrecarregar o serviço gratuito.</p>
        </div>
      </div>
    </div>
  );
}

function Creditos() {
  const [lista, setLista] = useState<CreditoDeFoto[] | null>(null);
  const [falhou, setFalhou] = useState(false);
  useEffect(() => { exigir(api.GET("/creditos")).then(setLista).catch(() => setFalhou(true)); }, []);
  return (
    <ul id="lista-creditos" className="lista-creditos">
      {falhou && "Não foi possível carregar os créditos."}
      {lista?.map((c) => (
        <li key={c.alimento_id}>
          <FotoAlimento id={c.alimento_id} classe="foto-mini" />
          <span>
            <b>{c.alimento.split(" (")[0]}</b>
            <small><a href={c.pagina} target="_blank" rel="noopener">{c.titulo}</a>{` · ${c.autor} · `}{c.licenca_url ? <a href={c.licenca_url} target="_blank" rel="noopener">{c.licenca}</a> : c.licenca}</small>
          </span>
        </li>
      ))}
    </ul>
  );
}

export function Configuracoes({ visivel }: { visivel: boolean }) {
  const { regioes, limites } = useDadosDaApi();
  const { config, ajustar, salvar, restaurar } = useConfiguracoes();
  const minCusto = limites?.custo_por_km.minimo ?? 20, maxCusto = limites?.custo_por_km.maximo ?? 200;
  const comPerto = funcionalidadeLigada("perto");

  return (
    <section id="aba-config" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="mia" titulo="Configurações" nota="Ajuste a busca do seu jeito. Fica salvo neste aparelho." />

      {comPerto && <RaioDeBusca />}

      {comPerto && (
        <div className="cartao">
          <h2>📍 Ponto de partida padrão</h2>
          <p className="nota">Usado quando você abre o Perto de mim sem compartilhar a localização.</p>
          <select id="cfg-regiao" aria-label="Região padrão" value={config.regiao} onChange={(e) => salvar({ regiao: e.target.value })}>
            <option value="">Perguntar sempre</option>
            {regioes.map((r) => <option value={`${r.lat},${r.lon}`} key={r.id}>{r.nome}</option>)}
          </select>
        </div>
      )}

      {funcionalidadeLigada("deslocamento") && (
        <div className="cartao">
          <div className="cartao-cabecalho"><h2>🚗 Custo do deslocamento</h2><span className="valor-grande"><b id="cfg-custo-valor">{reais(config.custo_por_km)}</b>/km</span></div>
          <input type="range" id="cfg-custo-km" className="deslizante" min={minCusto / 100} max={maxCusto / 100} step="0.05" value={config.custo_por_km / 100} aria-label="Custo por km rodado" style={progresso(config.custo_por_km, minCusto, maxCusto)}
            onChange={(e) => ajustar({ custo_por_km: Math.round(Number(e.target.value) * 100) })}
            onPointerUp={(e) => salvar({ custo_por_km: Math.round(Number(e.currentTarget.value) * 100) })}
            onKeyUp={(e) => salvar({ custo_por_km: Math.round(Number(e.currentTarget.value) * 100) })} />
          <div className="escala"><span>R$ 0,20</span><span>R$ 2,00</span></div>
          <p className="nota">Gasolina ÷ consumo do carro. Ex.: R$ 6,50 ÷ 10 km/L = R$ 0,65 por km. Entra no "custo real" de cada mercado e no custo de ir a um 2º mercado.</p>
        </div>
      )}

      {comPerto && (
        <div className="cartao">
          <h2>🏷️ Ordenar mercados por</h2>
          <OrdemDosMercados nome="cfg-ordem" rotulo="Ordenar mercados por" pequeno={false} />
        </div>
      )}

      <details className="cartao creditos">
        <summary><h2>📷 Créditos das fotos dos alimentos</h2></summary>
        <p className="nota">Fotos do Wikimedia Commons com licenças livres (CC0, domínio público, CC BY e CC BY-SA). Cada uma com autor e licença:</p>
        <Creditos />
      </details>

      <button type="button" id="cfg-restaurar" className="botao-secundario largo" onClick={restaurar}>Restaurar padrões</button>
      <div className="cartao">
        <h2>🔒 Seus dados</h2>
        <p className="nota">Sua última cesta e as preferências ficam só neste aparelho. A EconoMIA não tem login e não guarda sua localização nem o seu orçamento no servidor.</p>
        <button type="button" id="cfg-apagar" className="botao-secundario largo" onClick={() => {
          try { localStorage.clear(); } catch { /* nada guardado */ }
          location.reload();
        }}>Apagar meus dados deste aparelho</button>
      </div>
      <p className="nota centro">As configurações ficam só neste navegador. A sua localização nunca é guardada.</p>
    </section>
  );
}
