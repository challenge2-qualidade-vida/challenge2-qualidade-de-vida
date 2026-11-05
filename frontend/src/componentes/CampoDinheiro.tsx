import { proximoValorRedondo } from "../util/formato";

// Campo em reais com as setas próprias, que andam em passos redondos (de 799,92 vão a 800 ou 790).
// O valor do campo fica em reais, como a pessoa digita; quem envia à API converte para centavos.
interface Props {
  name: string;
  valor: string;
  aoMudar: (valor: string) => void;
  passo: number;
  min: number;
  nomeNaSeta: string;
  placeholder?: string;
}

const SETA_CIMA = "M3.5 10.5 8 6l4.5 4.5";
const SETA_BAIXO = "M3.5 5.5 8 10l4.5-4.5";

export function CampoDinheiro({ name, valor, aoMudar, passo, min, nomeNaSeta, placeholder }: Props) {
  const andar = (sentido: 1 | -1) => aoMudar(String(proximoValorRedondo(Number(valor) || 0, passo, sentido, min)));
  return (
    <span className="moeda"><span>R$</span><input type="number" name={name} min={min} step="0.01" value={valor} placeholder={placeholder} inputMode="decimal" onChange={(e) => aoMudar(e.target.value)} /><span className="moeda-setas"><button type="button" className="moeda-seta" data-passo={passo} aria-label={`Aumentar ${nomeNaSeta} em ${passo} reais`} onClick={() => andar(1)}><svg viewBox="0 0 16 16" aria-hidden="true"><path d={SETA_CIMA} /></svg></button><button type="button" className="moeda-seta" data-passo={-passo} aria-label={`Diminuir ${nomeNaSeta} em ${passo} reais`} onClick={() => andar(-1)}><svg viewBox="0 0 16 16" aria-hidden="true"><path d={SETA_BAIXO} /></svg></button></span></span>
  );
}
