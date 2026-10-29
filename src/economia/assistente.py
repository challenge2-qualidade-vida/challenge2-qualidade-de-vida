"""Assistente conversacional: LLM que usa ferramentas, com modo sem LLM de reserva.

O LLM só entende o pedido e redige a resposta. Preços, contas e a cesta vêm
das ferramentas (código determinístico); conhecimento vem do RAG.
"""

import json
import re
from dataclasses import dataclass, field

from .dados import Base
from .explicacao import explicar, reais
from .llm import ClienteLLM, ErroLLM
from .metas import RESTRICOES
from .otimizador import Pedido
from .planejador import planejar
from .precos import avaliar_promocao, consultar_precos
from .rag import BaseConhecimento, contexto_para_llm, normalizar

MAX_RODADAS_FERRAMENTAS = 5

PROMPT_SISTEMA = """Você é a EconoMIA, assistente que ajuda famílias brasileiras a fazer o orçamento de alimentação render sem perder qualidade.

Regras obrigatórias:
0. Só ajude com compras de alimentos, preços, orçamento da alimentação, nutrição, aproveitamento de alimentos e receitas. Para qualquer outro assunto, responda apenas: "Só consigo ajudar com compras, preços e alimentação." Não responda perguntas de outros temas, nem de memória.
1. Responda sempre em português do Brasil, de forma curta (no máximo 6 frases), clara e amigável.
2. NUNCA invente preços, quantidades, calorias ou contas. Para qualquer número, use as ferramentas:
   - montar_cesta: quando a pessoa der orçamento, número de pessoas ou pedir uma cesta/lista de compras;
   - consultar_precos: quando perguntar preço de um produto;
   - avaliar_promocao: quando perguntar se uma promoção ou oferta vale a pena;
   - buscar_conhecimento: para dúvidas sobre alimentação saudável, grupos de alimentos, aproveitamento, receitas e critérios de compra.
3. Ao usar buscar_conhecimento, baseie a resposta só nos trechos recebidos e cite a fonte entre colchetes, por exemplo [1]. Se os trechos não respondem à pergunta, diga que a base da EconoMIA não tem essa informação.
4. Sempre diga a data e a fonte dos preços usados. Se a fonte for "exemplo", avise que não são preços reais.
5. Você não é nutricionista: não prescreva dietas para doenças. Para condições de saúde, recomende procurar um profissional.
6. Se faltar informação para montar a cesta (por exemplo, o número de pessoas), pergunte antes de chamar a ferramenta.
7. Depois de montar_cesta, NÃO repita a lista de itens: a tela já mostra a lista completa. Resuma o custo, o mercado recomendado e a sobra do orçamento, copiando os valores exatamente como vieram da ferramenta."""

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "montar_cesta",
            "description": "Monta a cesta de compras mais barata que cumpre as metas nutricionais e compara comprar em 1 ou 2 mercados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "orcamento": {"type": "number", "description": "Orçamento em reais. Omitir se não houver limite."},
                    "pessoas": {"type": "integer", "description": "Número de pessoas na casa (1 a 20)."},
                    "periodo": {"type": "string", "enum": ["semana", "quinzena", "mes"]},
                    "restricoes": {"type": "array", "items": {"type": "string", "enum": sorted(RESTRICOES)}},
                    "custo_deslocamento": {"type": "number", "description": "Custo em reais para ir a um segundo mercado."},
                },
                "required": ["pessoas"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_precos",
            "description": "Consulta os preços de um produto nos mercados, com preço por kg, data e fonte.",
            "parameters": {
                "type": "object",
                "properties": {"produto": {"type": "string", "description": "Nome do produto, ex.: arroz, feijão preto, ovos."}},
                "required": ["produto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "avaliar_promocao",
            "description": "Diz se o preço de uma promoção é bom comparando o preço por kg com o menor preço normal do mesmo alimento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "preco": {"type": "number", "description": "Preço da promoção em reais."},
                    "embalagem_g": {"type": "number", "description": "Peso da embalagem em gramas (1 kg = 1000)."},
                },
                "required": ["produto", "preco"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_conhecimento",
            "description": "Busca trechos do Guia Alimentar, da Tabela TACO e dos critérios e receitas da EconoMIA.",
            "parameters": {
                "type": "object",
                "properties": {"pergunta": {"type": "string"}},
                "required": ["pergunta"],
            },
        },
    },
]


@dataclass
class RespostaChat:
    resposta: str
    modo: str                                   # "llm" ou "sem_llm"
    ferramentas_usadas: list[str] = field(default_factory=list)
    fontes: list[dict] = field(default_factory=list)
    aviso: str | None = None
    # Resultados brutos das ferramentas, para a tela mostrar sem depender do texto do LLM.
    dados: dict = field(default_factory=dict)
    # Passo a passo dos agentes (tópico 9), para transparência.
    etapas: list[dict] = field(default_factory=list)


class Assistente:
    def __init__(
        self,
        base: Base,
        conhecimento: BaseConhecimento,
        cliente: ClienteLLM | None,
        usar_rag: bool = True,
        prompt_sistema: str = PROMPT_SISTEMA,
        ferramentas: list[str] | None = None,
    ):
        self.base = base
        self.conhecimento = conhecimento
        self.cliente = cliente
        # False = abordagem A do experimento (LLM sem a base de conhecimento).
        self.usar_rag = usar_rag
        self.prompt_sistema = prompt_sistema
        # Nomes das ferramentas liberadas; None = todas. Cada agente recebe só as suas.
        self.ferramentas = [f for f in FERRAMENTAS if ferramentas is None or f["function"]["name"] in ferramentas]

    # ---------- Ferramentas ----------

    def executar(self, nome: str, args: dict, fontes: list[dict]) -> dict:
        if nome == "montar_cesta":
            pedido = Pedido(
                orcamento=args.get("orcamento") or None,
                pessoas=int(args.get("pessoas", 1)),
                periodo=args.get("periodo", "mes") if args.get("periodo") in ("semana", "quinzena", "mes") else "mes",
                restricoes=tuple(r for r in args.get("restricoes", []) if r in RESTRICOES),
            )
            plano = planejar(self.base, pedido, float(args.get("custo_deslocamento") or 0))
            cesta = plano.cesta_recomendada
            resumo = {"explicacao": explicar(plano, self.base), "restricoes": list(pedido.restricoes)}
            if cesta:
                resumo["custo_total"] = cesta.custo_total
                resumo["alimentos"] = sorted({i.alimento.split(" (")[0] for i in cesta.itens})
                resumo["fontes_preco"] = sorted({i.fonte_preco for i in cesta.itens})
                resumo["itens"] = [f"{i.quantidade} x {i.produto} ({i.mercado}) = {reais(i.subtotal)}" for i in cesta.itens]
            return resumo
        if nome == "consultar_precos":
            return consultar_precos(self.base, str(args.get("produto", "")))
        if nome == "avaliar_promocao":
            return avaliar_promocao(self.base, str(args.get("produto", "")), float(args.get("preco", 0)), args.get("embalagem_g"))
        if nome == "buscar_conhecimento":
            resultados = self.conhecimento.buscar(str(args.get("pergunta", "")))
            for r in resultados:
                fontes.append({"titulo": r.trecho.titulo, "fonte": r.trecho.fonte, "texto": r.trecho.texto})
            return {"contexto": contexto_para_llm(resultados)}
        return {"erro": f"Ferramenta desconhecida: {nome}"}

    # ---------- Com LLM ----------

    def _responder_com_llm(self, mensagem: str, historico: list[dict]) -> RespostaChat:
        usadas, fontes, dados = [], [], {}
        conteudo = mensagem
        ferramentas = self.ferramentas
        if self.usar_rag:
            # RAG clássico: os trechos vão junto com a pergunta, sem depender
            # de o modelo decidir chamar buscar_conhecimento.
            resultados = self.conhecimento.buscar(mensagem)
            if resultados:
                fontes.extend({"titulo": r.trecho.titulo, "fonte": r.trecho.fonte, "texto": r.trecho.texto} for r in resultados)
                conteudo = (
                    f"{mensagem}\n\n---\nTrechos da base de conhecimento da EconoMIA "
                    f"(use se forem relevantes e cite [n]):\n{contexto_para_llm(resultados)}"
                )
        else:
            ferramentas = [f for f in ferramentas if f["function"]["name"] != "buscar_conhecimento"]
        mensagens = [{"role": "system", "content": self.prompt_sistema}, *historico, {"role": "user", "content": conteudo}]
        for _ in range(MAX_RODADAS_FERRAMENTAS):
            msg = self.cliente.conversar(mensagens, ferramentas or None)
            chamadas = msg.get("tool_calls") or []
            if not chamadas:
                return RespostaChat(msg.get("content") or "", "llm", usadas, fontes, dados=dados)
            mensagens.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": chamadas})
            for i, chamada in enumerate(chamadas):
                nome = chamada["function"]["name"]
                bruto = chamada["function"].get("arguments") or "{}"
                try:
                    args = json.loads(bruto) if isinstance(bruto, str) else dict(bruto)
                    resultado = self.executar(nome, args, fontes)
                except (ValueError, TypeError) as e:
                    resultado = {"erro": f"Argumentos inválidos: {e}"}
                usadas.append(nome)
                dados[nome] = resultado
                # A lista de itens vai só para a tela; o LLM recebe o resumo.
                para_llm = {k: v for k, v in resultado.items() if k != "itens"}
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": chamada.get("id", f"chamada_{i}"),
                    "content": json.dumps(para_llm, ensure_ascii=False),
                })
        msg = self.cliente.conversar(mensagens)
        return RespostaChat(msg.get("content") or "", "llm", usadas, fontes, dados=dados)

    # ---------- Sem LLM ----------

    def _responder_sem_llm(self, mensagem: str) -> RespostaChat:
        intencao, args = interpretar(mensagem)
        fontes: list[dict] = []
        if intencao == "cesta":
            if "pessoas" not in args:
                return RespostaChat("Para montar a cesta, me diga quantas pessoas moram na casa.", "sem_llm")
            r = self.executar("montar_cesta", args, fontes)
            texto = "\n".join(r["explicacao"])
            if r.get("itens"):
                texto += "\n\nLista:\n" + "\n".join("• " + i for i in r["itens"])
            return RespostaChat(texto, "sem_llm", ["montar_cesta"], dados={"montar_cesta": r})
        if intencao == "promocao":
            r = self.executar("avaliar_promocao", args, fontes)
            return RespostaChat(texto_promocao(r), "sem_llm", ["avaliar_promocao"], dados={"avaliar_promocao": r})
        if intencao == "precos":
            r = self.executar("consultar_precos", args, fontes)
            return RespostaChat(texto_precos(r), "sem_llm", ["consultar_precos"], dados={"consultar_precos": r})
        resultados = self.conhecimento.buscar(mensagem, k=2)
        if not resultados:
            return RespostaChat("A base da EconoMIA não tem informação sobre isso. Posso ajudar com compras, preços, cesta e alimentação.", "sem_llm", ["buscar_conhecimento"])
        texto = "Encontrei isto na base de conhecimento:\n\n" + "\n\n".join(
            f"[{i}] {r.trecho.titulo}\n{r.trecho.texto}" for i, r in enumerate(resultados, 1)
        )
        fontes = [{"titulo": r.trecho.titulo, "fonte": r.trecho.fonte, "texto": r.trecho.texto} for r in resultados]
        return RespostaChat(texto, "sem_llm", ["buscar_conhecimento"], fontes)

    # ---------- Entrada ----------

    def responder(self, mensagem: str, historico: list[dict] | None = None) -> RespostaChat:
        historico = [h for h in (historico or [])[-6:] if h.get("role") in ("user", "assistant")]
        if self.cliente is None:
            r = self._responder_sem_llm(mensagem)
            r.aviso = "Modo sem LLM: respostas montadas direto das ferramentas. Configure um LLM gratuito para conversar."
            return r
        try:
            return self._responder_com_llm(mensagem, historico)
        except ErroLLM as e:
            r = self._responder_sem_llm(mensagem)
            r.aviso = f"O LLM não respondeu ({e}). Resposta montada no modo sem LLM."
            return r


# ---------- Interpretação simples (modo sem LLM) ----------

PADROES_RESTRICOES = {
    r"porco|suin[oa]": "sem_porco",
    r"carne vermelha": "sem_carne_vermelha",
    r"vegetarian|nao como (nenhuma )?carne(?! de porco| vermelha| suina)": "vegetariano",
    r"lactose": "sem_lactose",
    r"gluten": "sem_gluten",
    r"sem ovo|nao como ovo|alergia a ovo": "sem_ovo",
}


def _numero(texto: str) -> float:
    """'1.234,56' → 1234.56; '1.000' → 1000; '27.90' → 27.9."""
    texto = texto.rstrip(".,")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")
    return float(texto)


def interpretar(mensagem: str) -> tuple[str, dict]:
    """Descobre a intenção e os parâmetros com expressões regulares."""
    t = normalizar(mensagem)
    args: dict = {}

    if m := re.search(r"r\$\s*(\d[\d.,]*)|(\d[\d.,]*)\s*reais", t):
        valor = _numero(m.group(1) or m.group(2))
    else:
        valor = None

    # Só é pergunta de promoção se houver um preço para avaliar (o experimento
    # do tópico 8 mostrou "quando vale a pena ir a dois mercados" caindo aqui).
    if valor is not None and ("promocao" in t or "oferta" in t or "vale a pena" in t or "compensa" in t):
        produto = re.sub(r"r\$\s*\d[\d.,]*|\d[\d.,]*\s*(reais|kg|g|quilos?)", " ", t)
        produto = re.sub(r"[^a-z ]", " ", produto)
        produto = re.sub(r"\b(essa|esta|promocao|oferta|vale|a|pena|de|do|da|por|o|um|uma|kg|e|boa|no|na|mercado)\b", " ", produto)
        args = {"produto": " ".join(produto.split()), "preco": valor or 0}
        if m := re.search(r"(\d[\d.,]*)\s*(kg|quilos?)\b", t):
            args["embalagem_g"] = _numero(m.group(1)) * 1000
        elif m := re.search(r"(\d+)\s*g\b", t):
            args["embalagem_g"] = float(m.group(1))
        return "promocao", args

    if m := re.search(r"(\d+)\s*(pessoas?|moradores?)", t) or re.search(r"familia de (\d+)", t):
        args["pessoas"] = int(m.group(1))
    if "semana" in t:
        args["periodo"] = "semana"
    elif "quinzena" in t or "15 dias" in t:
        args["periodo"] = "quinzena"
    elif "mes" in t:
        args["periodo"] = "mes"
    restricoes = {r for padrao, r in PADROES_RESTRICOES.items() if re.search(padrao, t)}
    if restricoes:
        args["restricoes"] = sorted(restricoes)
    if valor is not None:
        args["orcamento"] = valor

    if valor is not None or "pessoas" in args or "cesta" in t or "lista de compras" in t:
        return "cesta", args

    if m := re.search(r"(?:preco d[oae]s?|quanto custa[m]?(?: o| a| os| as)?)\s+([a-z ]+)", t):
        return "precos", {"produto": m.group(1).strip()}

    return "conhecimento", {}


def texto_promocao(r: dict) -> str:
    if r["conclusao"] in ("sem_dados", "invalido"):
        return r["mensagem"]
    ref = r["melhor_oferta_normal"]
    base = (
        f"{r['alimento']}: na promoção sai a {reais(r['preco_kg_promocao'])}/kg. "
        f"O menor preço normal na base é {reais(r['melhor_preco_kg_normal'])}/kg ({ref['produto']}, {ref['mercado']}, fonte: {ref['fonte']})."
    )
    pct = f"{abs(r['diferenca_percentual']):.1f}".replace(".", ",")
    veredito = {
        "vale_a_pena": f" A promoção está {pct}% mais barata: vale a pena.",
        "empate": " O preço é praticamente o mesmo: não faz diferença.",
        "nao_vale": f" A promoção está {pct}% mais cara que o preço normal: não vale a pena.",
    }[r["conclusao"]]
    return base + veredito + " " + r["lembrete"]


def texto_precos(r: dict) -> str:
    if not r["encontrados"]:
        return f"Não encontrei '{r['termo']}' na base de preços."
    linhas = []
    for p in r["produtos"]:
        ofertas = "; ".join(f"{o['mercado']} {reais(o['preco'])} ({reais(o['preco_kg'])}/kg)" for o in p["ofertas"])
        linhas.append(f"• {p['produto']}: {ofertas}")
    fontes = {o["fonte"] for p in r["produtos"] for o in p["ofertas"]}
    aviso = " Atenção: são preços de exemplo." if "exemplo" in fontes else ""
    return "Preços encontrados:\n" + "\n".join(linhas) + aviso
