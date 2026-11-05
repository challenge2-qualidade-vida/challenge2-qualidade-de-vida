// Notificações por consulta periódica (decisão do grupo). Por enquanto não há tela para elas:
// o hook só mantém a lista, para a central de notificações usar quando for desenhada.
import { useEffect, useState } from "react";
import { api, exigir } from "../api/cliente";
import type { components } from "../api/esquema";

export type Notificacao = components["schemas"]["Notificacao"];
const INTERVALO_MS = 30_000;

export function useNotificacoes(ativo: boolean) {
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  useEffect(() => {
    if (!ativo) return;
    let vivo = true;
    const consultar = () => {
      if (document.hidden) return;
      exigir(api.GET("/notificacoes")).then((lista) => { if (vivo) setNotificacoes(lista); }).catch(() => { /* tenta na próxima */ });
    };
    consultar();
    const relogio = setInterval(consultar, INTERVALO_MS);
    return () => { vivo = false; clearInterval(relogio); };
  }, [ativo]);
  return notificacoes;
}
