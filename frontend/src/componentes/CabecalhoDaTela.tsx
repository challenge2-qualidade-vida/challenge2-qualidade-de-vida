import type { NomeDoGato } from "../efeitos/gatos";
import { GatoVivo } from "./GatoVivo";

export function CabecalhoDaTela({ gato, titulo, nota }: { gato: NomeDoGato; titulo: string; nota: string }) {
  return (
    <div className="cabecalho-tela"><GatoVivo nome={gato} src={`img/${gato}.webp`} /><div><h1 className="titulo-tela">{titulo}</h1><p className="nota">{nota}</p></div></div>
  );
}
