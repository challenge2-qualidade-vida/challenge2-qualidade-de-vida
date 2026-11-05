// Foto do alimento (Wikimedia Commons, licença livre; créditos nas Configurações).
import { useState } from "react";

export function FotoAlimento({ id, classe = "foto-alimento" }: { id: string; classe?: string }) {
  const [falhou, setFalhou] = useState(false);
  if (falhou) return <span className={`${classe} sem-foto`} aria-hidden="true">🛒</span>;
  return <img src={`img/alimentos/${id}.webp`} alt="" className={classe} loading="lazy" width="240" height="240" onError={() => setFalhou(true)} />;
}
