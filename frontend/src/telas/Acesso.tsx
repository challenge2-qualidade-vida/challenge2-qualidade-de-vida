// Telas novas de entrar e de criar conta, montadas com as mesmas peças das outras telas
// (cabeçalho com gato, cartão de formulário, campos e botão largo), sem estilo novo.
import { useState, type FormEvent } from "react";
import { mensagemDoProblema } from "../api/problemas";
import { cadastrar, entrar } from "../autenticacao/sessao";
import { CabecalhoDaTela } from "../componentes/CabecalhoDaTela";

export function Acesso() {
  const [modo, setModo] = useState<"entrar" | "cadastro">("entrar");
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const novo = modo === "cadastro";

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      if (novo) await cadastrar(nome.trim(), email.trim(), senha);
      else await entrar(email.trim(), senha);
    } catch (e) {
      setErro((novo ? "Não foi possível criar a conta: " : "Não foi possível entrar: ") + mensagemDoProblema(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section id={novo ? "aba-cadastro" : "aba-entrar"} className="painel">
      <CabecalhoDaTela gato="mia" titulo={novo ? "Criar conta" : "Entrar"} nota={novo ? "Sua cesta e suas preferências ficam salvas na sua conta." : "Entre para montar a cesta e conversar com a Mia."} />
      <form className="cartao formulario" onSubmit={enviar}>
        {novo && (
          <label className="campo">
            <span className="rotulo">🙂 Como podemos te chamar?</span>
            <input type="text" name="nome" autoComplete="given-name" required value={nome} onChange={(e) => setNome(e.target.value)} />
          </label>
        )}
        <label className="campo">
          <span className="rotulo">✉️ E-mail</span>
          <input type="email" name="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="campo">
          <span className="rotulo">🔒 Senha</span>
          <input type="password" name="senha" autoComplete={novo ? "new-password" : "current-password"} minLength={novo ? 8 : undefined} required value={senha} onChange={(e) => setSenha(e.target.value)} />
        </label>
        {novo && <p className="nota">Use pelo menos 8 caracteres.</p>}
        <button type="submit" className="botao largo" disabled={enviando}>{novo ? "Criar conta" : "Entrar"}</button>
      </form>
      <div className="erro" hidden={!erro}>{erro}</div>
      <p className="nota centro">
        {novo ? "Já tem conta? " : "Ainda não tem conta? "}
        <button type="button" className="sugestao" onClick={() => { setModo(novo ? "entrar" : "cadastro"); setErro(null); }}>{novo ? "Entrar" : "Criar conta"}</button>
      </p>
    </section>
  );
}
