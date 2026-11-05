// Anéis de progresso: orçamento e metas nutricionais.
import type { CSSProperties, ReactNode } from "react";
import type { Cesta } from "../estado/cesta";

const NOMES_METAS = { kcal: "Energia", proteina_g: "Proteína", fibra_g: "Fibra", flv_g: "Frutas e hortaliças" } as const;
const CORES_METAS = { kcal: "var(--marca)", proteina_g: "var(--roxo)", fibra_g: "var(--azul)", flv_g: "var(--verde)" } as const;

export function Anel({ pct, cor, className = "anel", id, children }: { pct?: number; cor?: string; className?: string; id?: string; children?: ReactNode }) {
  const estilo = {
    ...(pct === undefined ? {} : { "--pct": Math.min(Math.max(pct, 0), 100) }),
    ...(cor === undefined ? {} : { "--cor": cor }),
  } as CSSProperties;
  return <div className={className} id={id} style={estilo}>{children}</div>;
}

export function AneisDasMetas({ cesta }: { cesta: Cesta }) {
  return (Object.keys(NOMES_METAS) as (keyof typeof NOMES_METAS)[]).map((chave) => {
    const pct = Math.round((cesta.obtido[chave] / cesta.metas[chave]) * 100);
    return (
      <div className="mini-anel" key={chave}>
        <Anel pct={pct} cor={CORES_METAS[chave]}><div className="anel-centro"><b>{`${pct}%`}</b></div></Anel>
        <span>{NOMES_METAS[chave]}</span>
      </div>
    );
  });
}
