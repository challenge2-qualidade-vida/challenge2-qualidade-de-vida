import { useState, type FormEvent } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";
import { mensagemDoProblema } from "../api/problemas";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";
import { FotoAlimento } from "../componentes/FotoAlimento";
import { GatoVivo } from "../componentes/GatoVivo";
import { useDadosDaApi } from "../estado/dados-da-api";
import { dataBR, reais } from "../util/formato";

type NotaFiscal = components["schemas"]["LeituraDeNota"];

interface LinhaDaRevisao { usar: boolean; produto_id: string; preco: string }

/** Revisão dos itens lidos: a pessoa marca o que está certo e escolhe o produto da EconoMIA. */
function RevisaoDaNota({ nota, aoSalvar }: { nota: NotaFiscal; aoSalvar: () => void }) {
  const { precos, recarregarPrecos } = useDadosDaApi();
  const produtos = precos?.produtos ?? [];
  const [linhas, setLinhas] = useState<LinhaDaRevisao[]>(() => nota.itens.map((item) => ({
    usar: item.confianca === "alta",
    produto_id: item.produto_id ?? "",
    preco: ((item.preco_embalagem ?? item.valor_unitario) / 100).toFixed(2),
  })));
  const [status, setStatus] = useState("");
  const mudar = (i: number, m: Partial<LinhaDaRevisao>) => setLinhas((ls) => ls.map((l, k) => (k === i ? { ...l, ...m } : l)));

  async function salvar() {
    const itens = linhas
      .filter((l) => l.usar)
      .map((l) => ({ produto_id: l.produto_id, preco: Math.round(Number(l.preco) * 100) }))
      .filter((i) => i.produto_id && i.preco > 0);
    if (!itens.length) {
      setStatus("Marque pelo menos um item com produto escolhido.");
      return;
    }
    try {
      const r = await exigir(api.POST("/notas/revisao", { body: { emitente: nota.emitente, cnpj: nota.cnpj, data: nota.data, itens } }));
      setStatus(`✅ ${r.salvos} preço(s) salvo(s). Obrigado por contribuir!`);
      await recarregarPrecos();
      aoSalvar();
    } catch (e) {
      setStatus("Não foi possível salvar: " + mensagemDoProblema(e));
    }
  }

  return (
    <div id="nota" className="cartao">
      <h3 id="nota-titulo" className="mercado-titulo">{`${nota.emitente} — ${dataBR(nota.data)}`}</h3>
      <p className="nota">Marque os itens que estão certos. Itens sem correspondência ficam desmarcados: escolha o produto ou deixe de fora.</p>
      <div className="tabela-rolagem">
        <table className="tabela" id="tabela-nota">
          <thead><tr><th>Usar</th><th>No cupom</th><th>Produto da EconoMIA</th><th className="num">Preço da embalagem</th><th>Leitura</th></tr></thead>
          <tbody>
            {nota.itens.map((item, i) => {
              const alimento = produtos.find((p) => p.produto_id === linhas[i].produto_id)?.alimento_id;
              return (
                <tr key={i}>
                  <td><input type="checkbox" data-i={i} checked={linhas[i].usar} onChange={(e) => mudar(i, { usar: e.target.checked })} /></td>
                  <td>{item.descricao}<span className="fonte">{`${item.quantidade} ${item.unidade} × ${reais(item.valor_unitario)} = ${reais(item.valor_total)}`}</span></td>
                  <td><div className="celula-produto"><span className="foto-cupom-item">{alimento ? <FotoAlimento id={alimento} classe="foto-mini" /> : <span className="foto-mini sem-foto">?</span>}</span>
                    <select data-i={i} value={linhas[i].produto_id} onChange={(e) => mudar(i, { produto_id: e.target.value })}>
                      <option value="">— não usar —</option>
                      {produtos.map((p) => <option value={p.produto_id} key={p.produto_id}>{p.produto}</option>)}
                    </select></div></td>
                  <td className="num"><input type="number" step="0.01" min="0.01" data-i={i} value={linhas[i].preco} onChange={(e) => mudar(i, { preco: e.target.value })} /></td>
                  <td className={item.confianca === "alta" ? "confianca-alta" : "confianca-revisar"}>{item.confianca === "alta" ? "certa" : "revisar"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <button type="button" id="salvar-nota" className="botao largo" onClick={salvar}>Salvar preços conferidos</button>
      <p id="status-nota" className="nota">{status}</p>
    </div>
  );
}

export function Cupom({ visivel }: { visivel: boolean }) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [lendo, setLendo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [nota, setNota] = useState<NotaFiscal | null>(null);
  const [versao, setVersao] = useState(0);

  async function ler(evento: FormEvent) {
    evento.preventDefault();
    setErro(null);
    setNota(null);
    if (!arquivo && !url.trim()) {
      setErro("Envie a foto do cupom ou cole o link do QR code.");
      return;
    }
    setLendo(true);
    try {
      const lida = arquivo
        ? await exigir(api.POST("/notas", {
            // O contrato aceita multipart ou JSON; o tipo gerado só descreve o JSON, então o
            // corpo multipart é montado pelo bodySerializer.
            body: {} as { url: string },
            bodySerializer: () => { const f = new FormData(); f.append("arquivo", arquivo); return f; },
          }))
        : await exigir(api.POST("/notas", { body: { url: url.trim() } }));
      setNota(lida);
      setVersao((v) => v + 1);
    } catch (e) {
      setErro(mensagemDoProblema(e));
    } finally {
      setLendo(false);
    }
  }

  return (
    <section id="aba-cupom" className="painel" hidden={!visivel}>
      <CabecalhoDaTela gato="recibaldo" titulo="Enviar cupom" nota="O Recibaldo lê o cupom e confere cada item." />
      <div id="palco-cupom" className="palco" aria-hidden="true"></div>
      <div className="cartao">
        <p className="nota">O Recibaldo lê o <b>QR code</b> do cupom e busca a nota oficial na SEFAZ-DF. Você confere antes de salvar, e os preços passam a valer para todos. Nenhum dado pessoal (CPF, nome) é lido ou guardado.</p>
        <form id="form-cupom" onSubmit={ler}>
          <label className="foto-cupom">
            <input type="file" name="arquivo" accept="image/*" capture="environment" onChange={(e) => setArquivo(e.target.files?.[0] ?? null)} />
            <GatoVivo nome="recibaldo" src="img/recibaldo.webp" className="foto-gato" />
            <b>Tirar foto do cupom</b>
            <small id="nome-arquivo">{arquivo?.name ?? "com o QR code visível"}</small>
          </label>
          <label className="campo">
            <span className="rotulo">…ou cole o link do QR code</span>
            <input type="url" name="url" placeholder="https://www.fazenda.df.gov.br/nfce/qrcode?p=…" value={url} onChange={(e) => setUrl(e.target.value)} />
          </label>
          <button type="submit" className="botao largo" disabled={lendo}>Ler cupom</button>
        </form>
        <div id="erro-cupom" className="erro" hidden={!erro}>{erro}</div>
      </div>
      {nota
        ? <RevisaoDaNota key={versao} nota={nota} aoSalvar={() => {}} />
        : <div id="nota" className="cartao" hidden></div>}
    </section>
  );
}
