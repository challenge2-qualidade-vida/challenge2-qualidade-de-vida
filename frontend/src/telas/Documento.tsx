// Tela Documento (#95): a pessoa envia a imagem ou o PDF de uma nota fiscal com uma pergunta, e o
// Recibaldo responde. Só aparece com a flag "documentos". A tela só formata o que a API devolve:
// valores em centavos com reais() (RN01) e itens para conferir pelo campo `revisar` (RN09).
// O arquivo e a resposta ficam só na memória (RN15).
import { useState, type FormEvent } from "react";
import { api, exigir } from "../api/cliente";
import { mensagemDoProblema } from "../api/problemas";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { ComoFunciona } from "../componentes/ComoFunciona";
import { GatoVivo } from "../componentes/GatoVivo";
import {
  ACEITA, ETAPAS, PASSOS_DO_DOCUMENTO, avisoDaEtapa, etapasAlcancadas, problemaDoEnvio, quantidade, tamanhoDoArquivo,
  tipoDoArquivo, type ResultadoDoDocumento,
} from "../util/documentos";
import { reais } from "../util/formato";
import { PERGUNTA_DE_EXEMPLO, criarNotaDeExemplo } from "../util/nota-de-exemplo";

type Estado =
  | { tipo: "vazio" }
  | { tipo: "enviando" }
  | { tipo: "erro"; texto: string }
  | { tipo: "pronto"; resultado: ResultadoDoDocumento };

export function ResultadoDoEnvio({ resultado }: { resultado: ResultadoDoDocumento }) {
  const alcancadas = etapasAlcancadas(resultado.etapa);
  const aviso = avisoDaEtapa(resultado);
  return (
    <>
      <div id="etapas-documento" className="cartao">
        <h3 className="mercado-titulo">Processamento</h3>
        <ol className="itens-lista">
          {ETAPAS.map(({ etapa, texto }) => (
            <li key={etapa} className="item" data-etapa={etapa} data-alcancada={alcancadas.includes(etapa)}>
              <span className="item-emoji" aria-hidden="true">{alcancadas.includes(etapa) ? "✅" : "⏳"}</span>
              <div><span className="item-nome">{texto}</span></div>
              <span />
            </li>
          ))}
        </ol>
        {aviso && <p id="aviso-etapa" className="nota" role="status">{aviso}</p>}
      </div>
      {resultado.etapa === "extraido" && resultado.resposta && (
        <div id="resposta-documento" className="cartao">
          <h3 className="mercado-titulo">Resposta do Recibaldo</h3>
          <p className="nota">{resultado.tipo === "pdf" ? "Lida do PDF" : "Lida da imagem"}</p>
          <p>{resultado.resposta}</p>
        </div>
      )}
      {resultado.etapa === "extraido" && resultado.itens && resultado.itens.length > 0 && (
        <div id="itens-documento" className="cartao">
          <h3 className="mercado-titulo">Itens lidos</h3>
          <div className="tabela-rolagem">
            <table className="tabela">
              <thead><tr><th>Item</th><th className="num">Quantidade</th><th className="num">Valor</th><th>Leitura</th></tr></thead>
              <tbody>
                {resultado.itens.map((item, i) => (
                  <tr key={i} data-revisar={item.revisar}>
                    <td>{item.descricao}</td>
                    <td className="num">{quantidade(item)}</td>
                    <td className="num">{reais(item.valor_total)}</td>
                    <td>{item.revisar ? "⚠️ conferir" : "ok"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {resultado.itens.some((i) => i.revisar) && <p className="nota">Os itens marcados para conferir tiveram leitura com baixa confiança. Confira na nota antes de usar esses valores.</p>}
        </div>
      )}
    </>
  );
}

export function Documento({ visivel }: { visivel: boolean }) {
  const [pergunta, setPergunta] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [estado, setEstado] = useState<Estado>({ tipo: "vazio" });

  async function enviar(evento?: FormEvent, texto = pergunta, doc = arquivo) {
    evento?.preventDefault();
    const aviso = problemaDoEnvio(texto, doc);
    if (aviso || !doc) {
      setEstado({ tipo: "erro", texto: aviso ?? "Escolha uma imagem ou um PDF." });
      return;
    }
    setEstado({ tipo: "enviando" });
    try {
      const resultado = await exigir(api.POST("/documentos", {
        // O tipo gerado descreve o multipart como texto; o corpo de verdade é montado aqui.
        body: { pergunta: texto.trim(), arquivo: doc.name },
        bodySerializer: () => {
          const f = new FormData();
          f.append("pergunta", texto.trim());
          f.append("arquivo", doc);
          return f;
        },
      }));
      setEstado({ tipo: "pronto", resultado });
    } catch (e) {
      setEstado({ tipo: "erro", texto: mensagemDoProblema(e) });
    }
  }

  async function testarComExemplo() {
    try {
      const nota = await criarNotaDeExemplo();
      setArquivo(nota);
      setPergunta(PERGUNTA_DE_EXEMPLO);
      await enviar(undefined, PERGUNTA_DE_EXEMPLO, nota);
    } catch (e) {
      setEstado({ tipo: "erro", texto: mensagemDoProblema(e) });
    }
  }

  const tipo = arquivo ? tipoDoArquivo(arquivo) : null;
  return (
    <section id="aba-documento" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="recibaldo" titulo="Perguntar sobre a nota" nota="Envie a foto ou o PDF da nota e o Recibaldo responde." />
      <div className="cartao">
        <ComoFunciona chave="documento" passos={PASSOS_DO_DOCUMENTO} />
        <p className="nota">Aceita imagem (JPEG, PNG ou WebP) ou PDF, até 10 MB. A nota não fica guardada no aparelho.</p>
        <form id="form-documento" onSubmit={(e) => enviar(e)}>
          <label className="foto-cupom">
            <input type="file" name="arquivo" accept={ACEITA} onChange={(e) => setArquivo(e.target.files?.[0] ?? null)} />
            <GatoVivo nome="recibaldo" src="img/recibaldo.webp" className="foto-gato" />
            <b>Escolher imagem ou PDF</b>
            <small id="nome-documento">{arquivo ? `${tipo === "pdf" ? "📄" : "🖼️"} ${arquivo.name} · ${tamanhoDoArquivo(arquivo.size)}` : "foto da nota ou PDF da NFC-e"}</small>
          </label>
          <label className="campo">
            <span className="rotulo">O que você quer saber sobre a nota?</span>
            <input type="text" name="pergunta" placeholder="Ex.: quanto gastei com hortifrúti?" value={pergunta} onChange={(e) => setPergunta(e.target.value)} />
          </label>
          <button type="submit" className="botao largo" disabled={estado.tipo === "enviando"}>Enviar</button>
        </form>
        {estado.tipo === "vazio" && (
          <p id="exemplo-documento" className="nota">
            Não tem uma nota aqui agora?{" "}
            <button type="button" className="link" onClick={() => void testarComExemplo()}>Testar com uma nota de exemplo</button>
          </p>
        )}
      </div>
      {estado.tipo === "enviando" && <div className="carregando" role="status">Enviando o documento…</div>}
      {estado.tipo === "erro" && <div id="erro-documento" className="erro" role="alert">{estado.texto}</div>}
      {estado.tipo === "pronto" && <ResultadoDoEnvio resultado={estado.resultado} />}
    </section>
  );
}
