"""Sistema multiagente da EconoMIA (tópico 9).

  Orquestrador  decide quem trabalha, em que ordem, e junta o resultado.
  Cifrão        preços, promoções e cesta (ferramentas determinísticas).
  Miau-ricio    nutrição, aproveitamento e cardápio (RAG).
  Mia           verifica a resposta antes de ela chegar ao usuário. Não usa LLM.

Todos os agentes com LLM usam o mesmo modelo, cada um com seu prompt e
suas ferramentas. O roteamento é feito por regras (sem gastar uma chamada
de LLM só para decidir o caminho).
"""

import json
import re

from .assistente import PROMPT_SISTEMA, Assistente, RespostaChat, interpretar, texto_precos, texto_promocao
from .dados import Base
from .llm import ClienteLLM, ErroLLM
from .rag import BaseConhecimento, contexto_para_llm, normalizar

RECUSA_FORA_DO_TEMA = "Só consigo ajudar com compras, preços e alimentação."
RESPOSTA_SAUDE = (
    "Não posso indicar remédios, tratamentos ou dietas para doenças. Procure um médico ou nutricionista. "
    "Posso ajudar com uma alimentação equilibrada para a população geral e com o orçamento das compras."
)
RESPOSTA_SEM_FONTE = "A base da EconoMIA não tem uma fonte confiável sobre isso, então prefiro não responder para não passar informação errada."

# Perguntas de saúde não vão para o LLM (o modo sem LLM errou essa no tópico 8).
PALAVRAS_SAUDE = [
    "remedio", "medicamento", "doenca", "pressao alta", "hipertens", "diabetes", "diabetic", "colesterol",
    "tratamento", "cancer", "gravidez", "gestante", "alergia grave", "dieta para emagrecer", "emagrecer",
]

PROMPT_CIFRAO = PROMPT_SISTEMA + """

Você é o Cifrão, o agente de preços da EconoMIA. Cuide só de preços, promoções e da cesta de compras, sempre usando as ferramentas."""

PROMPT_MIAURICIO = PROMPT_SISTEMA + """

Você é o Miau-ricio, o agente de nutrição e receitas da EconoMIA. Responda com base nos trechos da base de conhecimento e cite [n]. Não fale de preços."""

PROMPT_CARDAPIO = """Você é o Miau-ricio, agente de receitas da EconoMIA. Responda em português do Brasil.
Monte um cardápio simples de 3 dias (almoço e jantar) usando SOMENTE os alimentos da lista abaixo, mais sal e temperos.
Não use nenhum alimento que não esteja na lista. Prefira as receitas dos trechos da base quando servirem e cite [n].
Seja breve: uma linha por refeição, em texto simples, sem Markdown (sem #, ** ou tabelas)."""

# Palavras que não podem aparecer num cardápio com cada restrição.
PROIBIDOS_POR_RESTRICAO = {
    "sem_porco": ["porco", "suino", "suina", "lombo", "bacon", "linguica", "presunto"],
    "sem_carne_vermelha": ["carne bovina", "carne moida", "patinho", "porco", "lombo", "bife"],
    "vegetariano": ["frango", "carne", "patinho", "porco", "lombo", "peixe", "sardinha", "atum", "bacon"],
    "sem_lactose": ["leite", "queijo", "mucarela", "manteiga", "iogurte"],
    "sem_gluten": ["macarrao", "pao", "trigo", "aveia", "farinha de trigo"],
    "sem_ovo": ["ovo", "omelete"],
}

PALAVRAS_NUTRICAO = [
    "nutri", "proteina", "caloria", "kcal", "fibra", "vitamina", "saudavel", "guia alimentar", "ultraprocess",
    "in natura", "receita", "cardapio", "refeic", "almoco", "jantar", "cafe da manha", "aproveit", "sobra",
    "madura", "estragar", "conserv", "substitu", "trocar", "taco", "alimento", "comer", "feijao", "arroz",
    "fruta", "legume", "verdura",
]


# ---------- Mia: verificação ----------

def _numeros(texto: str) -> set[float]:
    """Todos os valores em reais (R$ 1.234,56) de um texto."""
    valores = set()
    for bruto in re.findall(r"R\$\s*(\d[\d.]*(?:,\d{1,2})?)", texto):
        valores.add(round(float(bruto.replace(".", "").replace(",", ".")), 2))
    return valores


def _numeros_dos_dados(dados: dict) -> set[float]:
    """Todos os números que as ferramentas devolveram (em qualquer formato)."""
    texto = json.dumps(dados, ensure_ascii=False)
    valores = {round(float(n), 2) for n in re.findall(r"(?<![\w.])\d+(?:\.\d+)?", texto)}
    valores |= _numeros(texto)
    return valores


def verificar(resposta: str, dados: dict, restricoes: list[str], mensagem: str = "", fontes: list | None = None) -> list[dict]:
    """Mia confere a resposta. Devolve a lista de problemas encontrados."""
    problemas = []
    fontes = fontes or []

    if dados:
        # Valores aceitos: os que as ferramentas devolveram e os que o usuário escreveu.
        conhecidos = _numeros_dos_dados(dados) | _numeros(mensagem) | {round(float(n.replace(",", ".")), 2) for n in re.findall(r"\d+(?:,\d+)?", mensagem)}
        # Somas/diferenças simples (ex.: sobra do orçamento) já vêm calculadas nas
        # explicações; qualquer valor fora disso é tratado como inventado.
        inventados = sorted(v for v in _numeros(resposta) if not any(abs(v - c) < 0.015 for c in conhecidos))
        if inventados:
            problemas.append({
                "tipo": "valor_nao_confere",
                "detalhe": "Valores que não vieram das ferramentas: " + ", ".join(f"R$ {v:.2f}".replace(".", ",") for v in inventados),
            })

    links = re.findall(r"https?://[^\s)\]>]+", resposta)
    citados = {int(n) for n in re.findall(r"\[(\d+)\]", resposta)}
    if links:
        problemas.append({"tipo": "fonte_inventada", "detalhe": "A resposta traz links que não estão na base: " + ", ".join(links)})
    elif not dados and citados and max(citados) > len(fontes):
        problemas.append({"tipo": "fonte_inventada", "detalhe": f"A resposta cita [{max(citados)}], mas só {len(fontes)} trecho(s) foram usados."})
    elif not dados:
        # Resposta de conhecimento: todo número com unidade precisa estar nos trechos.
        texto_fontes = normalizar(" ".join(f.get("texto", "") for f in fontes)).replace(",", ".")
        sem_fonte = [
            n for n, _ in re.findall(r"(\d+(?:[.,]\d+)?)\s*(mg|g|kcal|%|gramas|calorias)\b", normalizar(resposta))
            if re.search(rf"(?<![\d.]){re.escape(n.replace(',', '.'))}(?![\d])", texto_fontes) is None
        ]
        if sem_fonte:
            problemas.append({"tipo": "fonte_inventada", "detalhe": "Números que não aparecem nos trechos da base: " + ", ".join(sem_fonte)})

    texto_dados = json.dumps(dados, ensure_ascii=False)
    if '"exemplo"' in texto_dados and "exemplo" not in normalizar(resposta):
        problemas.append({"tipo": "faltou_aviso_exemplo", "detalhe": "A resposta usa preços de exemplo e não avisou."})

    t = normalizar(resposta)
    for r in restricoes:
        achados = [p for p in PROIBIDOS_POR_RESTRICAO.get(r, []) if re.search(rf"\b{p}", t)]
        if achados:
            problemas.append({"tipo": "restricao_violada", "detalhe": f"Restrição '{r}' e a resposta cita: {', '.join(achados)}."})
    return problemas


def resposta_segura(dados: dict) -> str | None:
    """Texto montado só com os dados das ferramentas, para quando o LLM erra um valor."""
    if "montar_cesta" in dados:
        return "\n".join(dados["montar_cesta"]["explicacao"])
    if "avaliar_promocao" in dados:
        return texto_promocao(dados["avaliar_promocao"])
    if "consultar_precos" in dados:
        return texto_precos(dados["consultar_precos"])
    return None


def aplicar_verificacao(r: RespostaChat, restricoes: list[str], mensagem: str = "") -> RespostaChat:
    problemas = verificar(r.resposta, r.dados, restricoes, mensagem, r.fontes)
    r.etapas.append({"agente": "Mia", "acao": "verificou a resposta", "problemas": problemas})
    tipos = {p["tipo"] for p in problemas}

    if "fonte_inventada" in tipos:
        r.resposta = RESPOSTA_SEM_FONTE
        r.etapas.append({"agente": "Mia", "acao": "bloqueou a resposta, porque citava uma fonte que não está na base"})
        return r

    if "valor_nao_confere" in tipos and (segura := resposta_segura(r.dados)):
        r.resposta = segura
        r.etapas.append({"agente": "Mia", "acao": "trocou a resposta pelo texto calculado, porque havia valores que não conferem"})
    elif "faltou_aviso_exemplo" in tipos:
        r.resposta += "\n\nAtenção: os preços usados são de exemplo, não preços reais."
        r.etapas.append({"agente": "Mia", "acao": "acrescentou o aviso de preços de exemplo"})
    if "restricao_violada" in tipos:
        r.resposta += "\n\n⚠️ Confira: a sugestão pode citar alimentos que você não come. Desconsidere esses itens."
        r.etapas.append({"agente": "Mia", "acao": "alertou sobre alimento fora das restrições"})
    return r


# ---------- Orquestrador ----------

class Orquestrador:
    def __init__(self, base: Base, conhecimento: BaseConhecimento, cliente: ClienteLLM | None):
        self.base = base
        self.conhecimento = conhecimento
        self.cliente = cliente
        self.cifrao = Assistente(base, conhecimento, cliente, usar_rag=False, prompt_sistema=PROMPT_CIFRAO,
                                 ferramentas=["montar_cesta", "consultar_precos", "avaliar_promocao"])
        self.miauricio = Assistente(base, conhecimento, cliente, usar_rag=True, prompt_sistema=PROMPT_MIAURICIO, ferramentas=[])
        self.reserva = Assistente(base, conhecimento, None)   # modo sem LLM

    def rotear(self, mensagem: str) -> str:
        """'saude', 'cifrao', 'miauricio' ou 'fora_do_tema'."""
        t = normalizar(mensagem)
        if any(p in t for p in PALAVRAS_SAUDE):
            return "saude"
        intencao, _ = interpretar(mensagem)
        if intencao in ("cesta", "promocao", "precos"):
            return "cifrao"
        if any(p in t for p in PALAVRAS_NUTRICAO) or self.conhecimento.buscar(mensagem):
            return "miauricio"
        return "fora_do_tema"

    def responder(self, mensagem: str, historico: list[dict] | None = None) -> RespostaChat:
        rota = self.rotear(mensagem)
        destino = {"cifrao": "Cifrão", "miauricio": "Miau-ricio", "saude": "ninguém (pergunta de saúde)", "fora_do_tema": "ninguém (fora do tema)"}[rota]
        etapa = {"agente": "Orquestrador", "acao": f"encaminhou para {destino}"}

        if rota in ("fora_do_tema", "saude"):
            texto = RECUSA_FORA_DO_TEMA if rota == "fora_do_tema" else RESPOSTA_SAUDE
            return RespostaChat(texto, "llm" if self.cliente else "sem_llm", etapas=[etapa])

        agente = self.cifrao if rota == "cifrao" else self.miauricio
        if self.cliente is None:
            r = self.reserva.responder(mensagem, historico)
        else:
            r = agente.responder(mensagem, historico)
        r.etapas = [etapa, {"agente": "Cifrão" if rota == "cifrao" else "Miau-ricio", "acao": "respondeu", "ferramentas": r.ferramentas_usadas}]

        restricoes = r.dados.get("montar_cesta", {}).get("restricoes", [])
        return aplicar_verificacao(r, restricoes, mensagem)

    def cardapio(self, alimentos: list[str], restricoes: list[str]) -> RespostaChat:
        """Miau-ricio sugere refeições com os alimentos da cesta; Mia confere as restrições."""
        etapas = [{"agente": "Orquestrador", "acao": "pediu um cardápio ao Miau-ricio"}]
        resultados = self.conhecimento.buscar("receita " + " ".join(alimentos), k=4, minimo=0.05)
        fontes = [{"titulo": r.trecho.titulo, "fonte": r.trecho.fonte, "texto": r.trecho.texto} for r in resultados]

        if self.cliente is None:
            receitas = [r.trecho for r in resultados if "Receita" in r.trecho.titulo]
            texto = "Receitas da base que usam alimentos da sua cesta:\n" + "\n".join(f"• {t.titulo.split(' — ')[-1]}: {t.texto}" for t in receitas)
            r = RespostaChat(texto if receitas else "Não encontrei receitas na base para esses alimentos.", "sem_llm", fontes=fontes, etapas=etapas)
        else:
            mensagens = [
                {"role": "system", "content": PROMPT_CARDAPIO},
                {"role": "user", "content": f"Alimentos da cesta: {', '.join(alimentos)}.\n\nTrechos da base:\n{contexto_para_llm(resultados)}"},
            ]
            try:
                msg = self.cliente.conversar(mensagens)
                r = RespostaChat(msg.get("content") or "", "llm", fontes=fontes, etapas=etapas)
            except ErroLLM as e:
                return RespostaChat(f"Não foi possível gerar o cardápio agora ({e}).", "sem_llm", etapas=etapas)
        r.etapas.append({"agente": "Miau-ricio", "acao": "sugeriu o cardápio"})
        return aplicar_verificacao(r, restricoes)
