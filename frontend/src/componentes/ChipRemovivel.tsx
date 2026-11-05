export function ChipRemovivel({ texto, rotulo, aoRemover }: { texto: string; rotulo: string; aoRemover: () => void }) {
  return <button type="button" className="chip chip-remover" aria-label={rotulo} onClick={aoRemover}>{`${texto} ✕`}</button>;
}
