import { useEffect, useState, useSyncExternalStore } from "react";
import { ouvirSessao, pessoaLogada, renovar } from "./autenticacao/sessao";
import { AvisoDosDados, BarraDoTopo, NavegacaoPrincipal, Rodape } from "./componentes/Estrutura";
import { prepararAnimacoes } from "./efeitos/animacoes";
import { iniciarCena3d } from "./efeitos/cena3d";
import { ProvedorDaCesta } from "./estado/cesta";
import { ProvedorDeConfiguracoes } from "./estado/configuracoes";
import { ProvedorDeDados, useCarregarDadosDaApi, type DadosDaApi } from "./estado/dados-da-api";
import { ProvedorDeNavegacao, useNavegacao } from "./estado/navegacao";
import { useNotificacoes } from "./estado/notificacoes";
import { ProvedorDePosicao } from "./estado/posicao";
import { funcionalidadeLigada } from "./funcionalidades";
import { Acesso } from "./telas/Acesso";
import { Cesta } from "./telas/Cesta";
import { Configuracoes } from "./telas/Configuracoes";
import { Conversa } from "./telas/Conversa";
import { Cupom } from "./telas/Cupom";
import { Inicio } from "./telas/Inicio";
import { Perto } from "./telas/Perto";
import { Precos } from "./telas/Precos";

function Telas({ dados }: { dados: DadosDaApi }) {
  const { aba } = useNavegacao();
  useNotificacoes(true);
  useEffect(() => { prepararAnimacoes(); iniciarCena3d(); }, []);
  const escondidas = funcionalidadeLigada("perto") ? [] : (["perto"] as const);
  return (
    <>
      <BarraDoTopo llm={dados.llm} />
      <AvisoDosDados aviso={dados.opcoes.aviso_dados} />
      <main>
        <Inicio visivel={aba === "inicio"} />
        <Cesta visivel={aba === "cesta"} />
        {funcionalidadeLigada("perto") && <Perto visivel={aba === "perto"} />}
        <Configuracoes visivel={aba === "config"} />
        <Conversa visivel={aba === "chat"} />
        {funcionalidadeLigada("precos") && <Precos visivel={aba === "precos"} />}
        <Cupom visivel={aba === "cupom"} />
        <Rodape />
      </main>
      <NavegacaoPrincipal escondidas={[...escondidas]} />
    </>
  );
}

function AppComSessao() {
  const { dados, erro } = useCarregarDadosDaApi();
  if (erro) {
    return (
      <>
        <BarraDoTopo llm={null} comBotoes={false} />
        <main><div id="erro" className="erro">{"Não foi possível conectar à API: " + erro}</div><Rodape /></main>
      </>
    );
  }
  if (!dados) return <BarraDoTopo llm={null} comBotoes={false} />;
  return (
    <ProvedorDeDados dados={dados}>
      <ProvedorDeConfiguracoes>
        <ProvedorDePosicao>
          <ProvedorDaCesta>
            <Telas dados={dados} />
          </ProvedorDaCesta>
        </ProvedorDePosicao>
      </ProvedorDeConfiguracoes>
    </ProvedorDeDados>
  );
}

export function App() {
  const pessoa = useSyncExternalStore(ouvirSessao, pessoaLogada);
  const [verificada, setVerificada] = useState(false);
  // Ao abrir, tenta recuperar a sessão pelo cookie de renovação.
  useEffect(() => { void renovar().finally(() => setVerificada(true)); }, []);
  return (
    <ProvedorDeNavegacao>
      <div className="app">
        {!verificada
          ? <BarraDoTopo llm={null} comBotoes={false} />
          : pessoa
            ? <AppComSessao />
            : <><BarraDoTopo llm={null} comBotoes={false} /><main><Acesso /><Rodape /></main></>}
      </div>
    </ProvedorDeNavegacao>
  );
}
