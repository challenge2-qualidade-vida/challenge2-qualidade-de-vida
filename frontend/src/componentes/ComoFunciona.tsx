// "Como funciona": passos curtos no topo da tela, que a pessoa pode ocultar.
// Segue a ajuda no contexto (NN/g): visível, curta e sem tour na primeira abertura.
// Lembra só se a caixa está aberta, no próprio navegador (conveniência leve, sem dado pessoal).
import { useState } from "react";

const lerAberta = (chave: string) => {
  try { return localStorage.getItem(`economia-como-funciona-${chave}`) !== "fechada"; } catch { return true; }
};
const gravarAberta = (chave: string, aberta: boolean) => {
  try { localStorage.setItem(`economia-como-funciona-${chave}`, aberta ? "aberta" : "fechada"); } catch { /* navegação privada */ }
};

export interface PassoDaAjuda { emoji: string; titulo: string; texto: string }

export function ComoFunciona({ chave, passos }: { chave: string; passos: PassoDaAjuda[] }) {
  const [aberta, setAberta] = useState(() => lerAberta(chave));
  return (
    <details className="mais-opcoes como-funciona" open={aberta} onToggle={(e) => {
      const nova = (e.currentTarget as HTMLDetailsElement).open;
      setAberta(nova);
      gravarAberta(chave, nova);
    }}>
      <summary>💡 Como funciona</summary>
      <ol className="itens-lista">
        {passos.map((p, i) => (
          <li key={p.titulo} className="dica">
            <span className="dica-emoji" aria-hidden="true">{p.emoji}</span>
            <p><b>{`${i + 1}. ${p.titulo}`}</b><br /><small>{p.texto}</small></p>
          </li>
        ))}
      </ol>
    </details>
  );
}
