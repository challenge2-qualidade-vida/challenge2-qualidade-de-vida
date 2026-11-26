// Tela Verificar (#98, Refs #72): demo do fluxo multiagente da semana 4. Só aparece com a flag "verificacao".
// Mostra o veredito e o caminho dos agentes (Research → Analysis → Validation → Communication,
// com os retornos do Validation). A tela só formata: tudo vem da rota POST /verificacoes (#82).
import { useState, type FormEvent } from "react";
import { api, exigir } from "../api/cliente";
import { mensagemDoProblema } from "../api/problemas";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { ComoFunciona } from "../componentes/ComoFunciona";
import {
  AGENTES, CLASSIFICACOES, EXEMPLOS_DE_ALEGACAO, PASSOS_DA_VERIFICACAO, PERFIS, TAMANHO_MAXIMO_DA_ALEGACAO,
  destinoDoRetorno, problemaDaAlegacao, resumirPasso, segundos,
  type Perfil, type ResultadoDaVerificacao,
} from "../util/verificacao";

type Estado =
  | { tipo: "vazio" }
  | { tipo: "carregando" }
  | { tipo: "erro"; texto: string }
  | { tipo: "pronto"; resultado: ResultadoDaVerificacao };

export function VereditoDaVerificacao({ resultado }: { resultado: ResultadoDaVerificacao }) {
  const { veredito } = resultado;
  const classificacao = veredito.classificacao ? CLASSIFICACOES[veredito.classificacao] : null;
  return (
    <div id="veredito" className="cartao">
      {!veredito.aprovado_pela_validacao && (
        <div id="aviso-nao-conclusivo" className="erro" role="status">⚠️ Verificação não conclusiva: a validação não aprovou a análise.</div>
      )}
      {classificacao && <span id="classificacao" className="selo">{classificacao.rotulo}</span>}
      {classificacao && <p className="nota">{classificacao.explicacao}</p>}
      <p id="mensagem-veredito">{veredito.mensagem}</p>
      {veredito.fontes.length > 0 && <>
        <h3 className="mercado-titulo">Fontes</h3>
        <ul id="fontes-veredito" className="explicacao">
          {veredito.fontes.map((f) => (
            <li key={f.titulo}>
              {f.url ? <a href={f.url} target="_blank" rel="noreferrer">{f.titulo}</a> : f.titulo}
              {` — ${f.instituicao}${f.ano ? `, ${f.ano}` : ""}`}
            </li>
          ))}
        </ul>
      </>}
    </div>
  );
}

function CaminhoDosAgentes({ resultado }: { resultado: ResultadoDaVerificacao }) {
  return (
    <div id="caminho-agentes" className="cartao">
      <div className="cartao-cabecalho">
        <h3 className="mercado-titulo">Caminho dos agentes</h3>
        <span className="nota">{resultado.retornos === 0 ? "sem retornos" : `${resultado.retornos} retorno${resultado.retornos > 1 ? "s" : ""}`}</span>
      </div>
      <ol className="itens-lista">
        {resultado.historico.flatMap((passo, i) => {
          const agente = AGENTES[passo.agente];
          const destino = destinoDoRetorno(passo);
          const linha = (
            <li key={i} className="item" data-agente={passo.agente}>
              <span className="item-emoji" aria-hidden="true">{agente.emoji}</span>
              <div><span className="item-nome">{agente.nome}</span><span className="item-detalhe">{resumirPasso(passo)}</span></div>
              <span className="item-valor"><small>{segundos(passo.segundos)}</small></span>
            </li>
          );
          if (!destino) return [linha];
          return [linha, (
            <li key={`${i}-retorno`} className="item" data-retorno={passo.saida.retornar_para as string}>
              <span className="item-emoji" aria-hidden="true">↩️</span>
              <div><span className="item-nome">{`Retorno ao ${destino}`}</span><span className="item-detalhe">O Validation pediu outra rodada.</span></div>
              <span />
            </li>
          )];
        })}
      </ol>
    </div>
  );
}

export function Verificar({ visivel }: { visivel: boolean }) {
  const [alegacao, setAlegacao] = useState("");
  const [perfil, setPerfil] = useState<Perfil>("consumidor_geral");
  const [estado, setEstado] = useState<Estado>({ tipo: "vazio" });

  async function verificar(evento?: FormEvent, texto = alegacao) {
    evento?.preventDefault();
    const aviso = problemaDaAlegacao(texto);
    if (aviso) {
      setEstado({ tipo: "erro", texto: aviso });
      return;
    }
    setEstado({ tipo: "carregando" });
    try {
      const resultado = await exigir(api.POST("/verificacoes", { body: { alegacao: texto.trim(), perfil } }));
      setEstado({ tipo: "pronto", resultado });
    } catch (e) {
      setEstado({ tipo: "erro", texto: mensagemDoProblema(e) });
    }
  }

  return (
    <section id="aba-verificar" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="mia" titulo="Verificar alegação" nota="Os agentes buscam na base, analisam, validam e explicam." />
      <div className="cartao">
        <ComoFunciona chave="verificar" passos={PASSOS_DA_VERIFICACAO} />
        <form id="form-verificar" className="formulario" onSubmit={(e) => verificar(e)}>
          <label className="campo">
            <span className="rotulo">O que você ouviu sobre alimentação?</span>
            <input type="text" name="alegacao" maxLength={TAMANHO_MAXIMO_DA_ALEGACAO} placeholder="Ex.: alimentos ultraprocessados devem ser evitados" value={alegacao} onChange={(e) => setAlegacao(e.target.value)} />
          </label>
          <fieldset className="campo">
            <legend className="rotulo">Como quer a resposta?</legend>
            <div className="chips">
              {PERFIS.map((p) => (
                <label className="chip" key={p.valor}><input type="radio" name="perfil" value={p.valor} checked={perfil === p.valor} onChange={() => setPerfil(p.valor)} />{p.rotulo}</label>
              ))}
            </div>
          </fieldset>
          <button type="submit" className="botao largo" disabled={estado.tipo === "carregando"}>Verificar</button>
        </form>
        {estado.tipo === "vazio" && (
          <p id="exemplos-verificar" className="nota exemplos">
            Não sabe o que perguntar? Teste com um exemplo:{" "}
            {EXEMPLOS_DE_ALEGACAO.map((exemplo, i) => (
              <span key={exemplo}>
                {i > 0 && " ou "}
                <button type="button" className="link" onClick={() => { setAlegacao(exemplo); void verificar(undefined, exemplo); }}>{`“${exemplo}”`}</button>
              </span>
            ))}
          </p>
        )}
      </div>
      {estado.tipo === "carregando" && <div className="carregando" role="status">Os agentes estão verificando…</div>}
      {estado.tipo === "erro" && <div id="erro-verificar" className="erro" role="alert">{estado.texto}</div>}
      {estado.tipo === "pronto" && <>
        <VereditoDaVerificacao resultado={estado.resultado} />
        <CaminhoDosAgentes resultado={estado.resultado} />
      </>}
    </section>
  );
}
