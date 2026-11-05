// Fora do MVP do grupo (histórico e tendência de preços): só aparece com a flag "precos".
import { FotoAlimento } from "../componentes/FotoAlimento";
import { useDadosDaApi } from "../estado/dados-da-api";
import { dataBR, reais } from "../util/formato";

export function Precos({ visivel }: { visivel: boolean }) {
  const { precos } = useDadosDaApi();
  const ids = precos?.mercados.map((m) => m.id) ?? [];
  return (
    <section id="aba-precos" className="painel" hidden={!visivel}>
      <h1 className="titulo-tela">Tabela de preços</h1>
      <div id="palco-precos" className="palco palco-pequeno" aria-hidden="true"></div>
      <div className="cartao">
        <p className="nota">O menor preço por kg de cada produto aparece em verde. Cada preço mostra a data e a fonte.</p>
        <div className="tabela-rolagem">
          <table id="tabela-precos" className="tabela">
            {precos && <>
              <thead><tr><th>Produto</th>{precos.mercados.map((m) => <th className="num" key={m.id}>{m.nome}</th>)}</tr></thead>
              <tbody>
                {precos.produtos.map((p) => {
                  const valores = ids.map((id) => p.precos[id]?.preco_kg).filter((v): v is number => v !== undefined);
                  const menor = Math.min(...valores);
                  return (
                    <tr key={p.produto_id}>
                      <td><div className="celula-produto"><FotoAlimento id={p.alimento_id} classe="foto-mini" /><span>{p.produto}</span></div></td>
                      {ids.map((id) => {
                        const pr = p.precos[id];
                        if (!pr) return <td className="num" key={id}>—</td>;
                        return <td className={"num" + (pr.preco_kg === menor && valores.length > 1 ? " melhor" : "")} key={id}>{reais(pr.preco)}<span className="fonte">{`${reais(pr.preco_kg)}/kg · ${dataBR(pr.data)}`}</span></td>;
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </>}
          </table>
        </div>
      </div>
    </section>
  );
}
