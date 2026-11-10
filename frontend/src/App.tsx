import { FormEvent, useEffect, useRef, useState } from "react";

import { ErroDaApi, MENSAGEM_FORA_DO_AR, perguntar, type Resposta, type TrechoDaBusca } from "./api";
import { paragrafos, separarCitacoes } from "./citacoes";
import { decimal, ESCALA_MINIMA, larguraDaBarra, plural } from "./escala";

const EXEMPLOS = [
  "Como guardar folhas verdes na geladeira?",
  "Tenho arroz, ovo e cenoura. Que receita posso fazer?",
  "Posso dar açúcar para uma criança menor de 2 anos?",
  "O que são alimentos ultraprocessados?",
  "Como aproveitar cascas e talos de legumes?",
];

type Estado =
  | { fase: "inicio" }
  | { fase: "carregando"; pergunta: string }
  | { fase: "resposta"; pergunta: string; resposta: Resposta }
  | { fase: "erro"; pergunta: string; mensagem: string };

export default function App() {
  const [pergunta, setPergunta] = useState("");
  const [estado, setEstado] = useState<Estado>({ fase: "inicio" });
  const segundos = useCronometro(estado.fase === "carregando");
  const campo = useRef<HTMLTextAreaElement>(null);

  async function enviar(texto: string) {
    const limpa = texto.trim();
    if (!limpa || estado.fase === "carregando") return;
    setPergunta(limpa);
    setEstado({ fase: "carregando", pergunta: limpa });
    try {
      const resposta = await perguntar(limpa);
      setEstado({ fase: "resposta", pergunta: limpa, resposta });
    } catch (erro) {
      const mensagem = erro instanceof ErroDaApi ? erro.message : MENSAGEM_FORA_DO_AR;
      setEstado({ fase: "erro", pergunta: limpa, mensagem });
    }
  }

  // ?pergunta=... na URL envia a pergunta ao abrir a página (link de demonstração)
  useEffect(() => {
    const daUrl = new URLSearchParams(window.location.search).get("pergunta");
    if (daUrl) void enviar(daUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    void enviar(pergunta);
  }

  const carregando = estado.fase === "carregando";

  return (
    <div className="pagina">
      <header className="cabecalho">
        <span className="avatar" aria-hidden="true">
          🐱
        </span>
        <div>
          <h1>Miau-ricio</h1>
          <p>Pergunte sobre receitas, alimentação e como aproveitar melhor os alimentos.</p>
        </div>
      </header>

      <main>
        <form className="formulario" onSubmit={aoEnviar}>
          <label htmlFor="pergunta" className="rotulo">
            Sua pergunta
          </label>
          <textarea
            id="pergunta"
            ref={campo}
            value={pergunta}
            maxLength={500}
            rows={3}
            placeholder="Ex.: o que posso fazer com arroz, ovo e cenoura?"
            onChange={(e) => setPergunta(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void enviar(pergunta);
              }
            }}
            disabled={carregando}
          />
          <div className="acoes">
            <span className="contador">{pergunta.length}/500</span>
            <button type="submit" disabled={carregando || !pergunta.trim()}>
              {carregando ? "Pensando…" : "Perguntar"}
            </button>
          </div>
        </form>

        {estado.fase === "inicio" && (
          <section className="exemplos" aria-label="Exemplos de perguntas">
            <p>Experimente:</p>
            <ul>
              {EXEMPLOS.map((exemplo) => (
                <li key={exemplo}>
                  <button type="button" className="chip" onClick={() => void enviar(exemplo)}>
                    {exemplo}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {carregando && (
          <section className="cartao carregando" aria-live="polite">
            <div className="pontos" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <p>
              Procurando nos documentos e escrevendo a resposta… <strong>{segundos} s</strong>
            </p>
            <p className="dica">Pode levar alguns segundos (na CPU, alguns minutos).</p>
          </section>
        )}

        {estado.fase === "erro" && (
          <section className="cartao aviso erro" role="alert">
            <p>{estado.mensagem}</p>
            <button type="button" className="secundario" onClick={() => void enviar(estado.pergunta)}>
              Tentar de novo
            </button>
          </section>
        )}

        {estado.fase === "resposta" && <CartaoComTrechos resposta={estado.resposta} />}
      </main>

      <footer className="rodape">
        As respostas usam só a base de conhecimento do EconoMIA e citam as fontes. Preços atuais não vêm
        desta base.
      </footer>
    </div>
  );
}

function CartaoDeResposta({ resposta }: { resposta: Resposta }) {
  if (!resposta.encontrou) {
    return (
      <>
        <section className="cartao aviso" aria-live="polite">
          <p>{resposta.texto}</p>
        </section>
        {resposta.trechos_recuperados.length > 0 && (
          <PainelDeTrechos
            trechos={resposta.trechos_recuperados}
            limiar={resposta.limiar}
            explicacao="Nenhum trecho foi usado. Estes são os mais próximos que a busca encontrou."
          />
        )}
      </>
    );
  }
  const numeros = new Set(resposta.fontes.map((f) => f.numero));
  return (
    <section className="cartao" aria-live="polite">
      <div className="texto">
        {paragrafos(resposta.texto).map((paragrafo, i) => (
          <p key={i}>
            {separarCitacoes(paragrafo, numeros).map((parte, j) =>
              parte.tipo === "texto" ? (
                <span key={j}>{parte.valor}</span>
              ) : (
                <a key={j} className="citacao" href={`#fonte-${parte.numero}`}>
                  [{parte.numero}]
                </a>
              ),
            )}
          </p>
        ))}
      </div>

      {resposta.faltando.some((f) => f.ingredientes.length > 0) && (
        <div className="faltando">
          <h2>Ingredientes que faltam</h2>
          <ul>
            {resposta.faltando.map((f) => (
              <li key={f.receita}>
                <strong>{f.receita}:</strong> {f.ingredientes.length ? f.ingredientes.join(", ") : "nenhum"}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="fontes">
        <h2>Fontes</h2>
        <ol>
          {resposta.fontes.map((fonte) => (
            <li key={fonte.numero} id={`fonte-${fonte.numero}`}>
              <span className="numero">[{fonte.numero}]</span>
              <div>
                <span className={`selo ${fonte.tipo}`}>{fonte.tipo === "receita" ? "Receita" : "Orientação"}</span>
                <p>{fonte.url ? fonte.descricao.replace(` ${fonte.url}`, "") : fonte.descricao}</p>
                {fonte.url && (
                  <a href={fonte.url} target="_blank" rel="noreferrer">
                    Abrir a fonte ↗
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
      <p className="tempo">Respondido em {decimal(resposta.segundos, 1)} s</p>
    </section>
  );
}

function CartaoComTrechos({ resposta }: { resposta: Resposta }) {
  return (
    <>
      <CartaoDeResposta resposta={resposta} />
      {resposta.encontrou && resposta.trechos_recuperados.length > 0 && (
        <PainelDeTrechos
          trechos={resposta.trechos_recuperados}
          limiar={resposta.limiar}
          explicacao="Trechos que a busca entregou ao LLM, na ordem em que ele os recebeu: pelo score e, entre receitas com score parecido, primeiro a que tem menos ingredientes faltando."
        />
      )}
    </>
  );
}

function PainelDeTrechos({
  trechos,
  limiar,
  explicacao,
}: {
  trechos: TrechoDaBusca[];
  limiar: number | null;
  explicacao: string;
}) {
  const [aberto, setAberto] = useState(true);
  const citados = trechos.filter((t) => t.fonte !== null).length;
  return (
    <section className="cartao trechos" aria-label="Trechos recuperados">
      <button type="button" className="cabecalho-painel" onClick={() => setAberto(!aberto)} aria-expanded={aberto}>
        <span>
          <strong>Trechos recuperados</strong> · {plural(trechos.length, "trecho", "trechos")},{" "}
          {plural(citados, "citado", "citados")}
          {limiar !== null && <> · limiar {decimal(limiar)}</>}
        </span>
        <span aria-hidden="true">{aberto ? "▾" : "▸"}</span>
      </button>
      {aberto && (
        <>
          <p className="explicacao">
            {explicacao} O score é a similaridade de cosseno entre a pergunta e o trecho (barra de{" "}
            {decimal(ESCALA_MINIMA, 2)} a 1{limiar !== null && "; a linha marca o limiar"}).
          </p>
          <ol className="lista-trechos">
            {trechos.map((t) => (
              <li key={t.posicao} className={t.acima_do_limiar ? "" : "abaixo"}>
                <div className="linha-score">
                  <span className="score">{decimal(t.score)}</span>
                  <div className="barra" aria-hidden="true">
                    <div className="preenchimento" style={{ width: `${larguraDaBarra(t.score)}%` }} />
                    {limiar !== null && <div className="marca-limiar" style={{ left: `${larguraDaBarra(limiar)}%` }} />}
                  </div>
                  {t.fonte !== null ? (
                    <a className="selo citado" href={`#fonte-${t.fonte}`}>
                      citado [{t.fonte}]
                    </a>
                  ) : (
                    <span className="selo neutro">{t.acima_do_limiar ? "não citado" : "abaixo do limiar"}</span>
                  )}
                </div>
                <div className="titulo-trecho">
                  <span className={`selo ${t.tipo}`}>{t.tipo === "receita" ? "Receita" : "Orientação"}</span>{" "}
                  <strong>{t.titulo}</strong>
                  {t.origem !== t.titulo && <span className="origem"> · {t.origem}</span>}
                </div>
                <p className="resumo">{t.resumo}</p>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}

function useCronometro(ativo: boolean): number {
  const [segundos, setSegundos] = useState(0);
  useEffect(() => {
    if (!ativo) return;
    setSegundos(0);
    const inicio = Date.now();
    const id = setInterval(() => setSegundos(Math.floor((Date.now() - inicio) / 1000)), 500);
    return () => clearInterval(id);
  }, [ativo]);
  return segundos;
}
