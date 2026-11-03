"""Cardápio a partir da cesta (tópico 18). Determinístico: só usa o que está na cesta.

O LLM não escolhe alimentos. Em teste, ele sugeriu "jantar: feijão carioca cru"
e tomate fora da cesta. Aqui cada refeição vem de uma receita cadastrada, cujos
ingredientes apontam para os alimentos da base.
"""

import json
import re
from dataclasses import dataclass, field

from .dados import RAIZ, Base
from .metas import tags_excluidas
from .rag import normalizar

ARQ_RECEITAS = RAIZ / "data" / "receitas" / "receitas.json"
REFEICOES = {"cafe": "Café da manhã", "almoco": "Almoço", "jantar": "Jantar"}
USO_PADRAO_DIAS = 30   # grãos, farinha, óleo: duram meses

_dados = json.loads(ARQ_RECEITAS.read_text(encoding="utf-8"))
RECEITAS: list[dict] = _dados["receitas"]
NOMES: dict[str, str] = _dados["nomes"]
USO_EM_DIAS: dict[str, int] = _dados["uso_em_dias"]

# Palavras que denunciam cada alimento num texto livre (para a Mia conferir o LLM).
TERMOS_ALIMENTOS = {
    "arroz": ["arroz"], "macarrao": ["macarrao", "macarronada", "espaguete"], "aveia": ["aveia"],
    "pao_frances": ["pao", "paes"], "farinha_mandioca": ["farinha", "farofa", "tutu"],
    "feijao_carioca": ["feijao"], "feijao_preto": ["feijao"], "lentilha": ["lentilha"], "ovo": ["ovo", "ovos", "omelete"],
    "frango_peito": ["frango"], "frango_coxa": ["frango"], "patinho": ["carne", "patinho", "bife"],
    "lombo_porco": ["porco", "lombo", "suina"], "sardinha": ["sardinha"], "leite": ["leite"],
    "mucarela": ["queijo", "mucarela", "mussarela"], "batata": ["batata", "batatas", "pure"], "mandioca": ["mandioca", "aipim", "macaxeira"],
    "cenoura": ["cenoura", "cenouras"], "tomate": ["tomate", "tomates"], "cebola": ["cebola", "cebolas"], "repolho": ["repolho"],
    "abobora": ["abobora", "quibebe"], "banana": ["banana", "bananas"], "laranja": ["laranja", "laranjas"], "maca": ["maca", "macas"],
    "oleo_soja": ["oleo"], "acucar": ["acucar"],
}
# Alimentos comuns que a base não tem: nunca podem aparecer no cardápio.
TERMOS_FORA_DA_BASE = [
    "alface", "brocolis", "couve", "pepino", "abobrinha", "berinjela", "pimentao", "ervilha", "milho", "grao de bico",
    "atum", "peixe", "tilapia", "bacon", "linguica", "presunto", "iogurte", "manteiga", "margarina", "tapioca", "cuscuz",
    "abacaxi", "mamao", "manga", "melancia", "uva", "soja", "quinoa", "batata doce",
]


@dataclass
class Refeicao:
    tipo: str
    titulo: str
    receita: str
    ingredientes: list[str]
    alimentos: list[str]
    preparo: str


@dataclass
class Cardapio:
    dias: list[list[Refeicao]] = field(default_factory=list)
    nao_usados: list[str] = field(default_factory=list)

    @property
    def vazio(self) -> bool:
        return not any(self.dias)


def resolver_alimentos(base: Base, alimentos: list[str]) -> list[str]:
    """Aceita ids ou nomes ("feijão carioca", "Arroz branco tipo 1 (cru)") e devolve ids da base."""
    ids = []
    for bruto in alimentos:
        alvo = normalizar(bruto.split(" (")[0]).strip()
        for a in base.alimentos.values():
            if bruto == a.id or (alvo and (alvo == normalizar(NOMES.get(a.id, "")) or alvo in normalizar(a.nome))):
                if a.id not in ids:
                    ids.append(a.id)
                break
    return ids


def _urgencia(alimento: str) -> int:
    """Quanto menor, mais cedo o alimento precisa ser usado."""
    return USO_EM_DIAS.get(alimento, USO_PADRAO_DIAS)


def _escolher(receita: dict, disponiveis: set[str], usados: dict[str, int]) -> list[str] | None:
    """Ingredientes da receita com o que há na cesta, ou None se faltar uma vaga obrigatória."""
    escolhidos = []
    for vaga in receita["requer"]:
        opcoes = [a for a in vaga if a in disponiveis and a not in escolhidos]
        if not opcoes:
            return None
        # Primeiro o menos usado; no empate, o que estraga antes.
        escolhidos.append(min(opcoes, key=lambda a: (usados.get(a, 0), _urgencia(a))))
    return escolhidos + [a for a in receita["opcional"] if a in disponiveis and a not in escolhidos]


def montar_cardapio(base: Base, alimentos: list[str], restricoes: list[str] | None = None, dias: int = 3) -> Cardapio:
    """Distribui receitas pelos dias: não repete cedo, usa todos os alimentos e o que estraga primeiro."""
    excluidas = tags_excluidas(list(restricoes or []))
    disponiveis = {a for a in resolver_alimentos(base, alimentos) if not excluidas & set(base.alimentos[a].tags)}
    usados: dict[str, int] = {}
    vezes: dict[str, int] = {}
    cardapio = Cardapio()

    for dia in range(dias):
        refeicoes = []
        for tipo, titulo in REFEICOES.items():
            melhor, melhor_nota, melhor_ing = None, None, None
            for i, r in enumerate(RECEITAS):
                # O mesmo prato não se repete no mesmo dia.
                if tipo not in r["refeicoes"] or r["id"] in {x.receita for x in refeicoes}:
                    continue
                ing = _escolher(r, disponiveis, usados)
                if ing is None:
                    continue
                novos = [a for a in ing if a not in usados]
                urgentes = sum(1 for a in novos if _urgencia(a) <= dia + 2)
                nota = (-vezes.get(r["id"], 0), urgentes, len(novos), len(r["requer"]), -i)
                if melhor_nota is None or nota > melhor_nota:
                    melhor, melhor_nota, melhor_ing = r, nota, ing
            if melhor is None:
                continue
            vezes[melhor["id"]] = vezes.get(melhor["id"], 0) + 1
            for a in melhor_ing:
                usados[a] = usados.get(a, 0) + 1
            refeicoes.append(Refeicao(tipo, titulo, melhor["id"], [NOMES[a] for a in melhor_ing], melhor_ing, melhor["preparo"]))
        cardapio.dias.append(refeicoes)

    cardapio.nao_usados = sorted(NOMES[a] for a in disponiveis - usados.keys())
    return cardapio


NOME_RECEITA = {r["id"]: r["nome"] for r in RECEITAS}


def texto_cardapio(c: Cardapio) -> str:
    linhas = []
    for n, refeicoes in enumerate(c.dias, 1):
        linhas.append(f"Dia {n}")
        for r in refeicoes:
            linhas.append(f"• {r.titulo}: {NOME_RECEITA[r.receita]} ({', '.join(r.ingredientes)}). {r.preparo}")
    return "\n".join(linhas)


def problemas_cardapio(texto: str, alimentos: list[str]) -> list[str]:
    """O que a Mia não deixa passar num texto sobre o cardápio: alimento cru ou fora da cesta."""
    t = normalizar(texto)
    problemas = []
    if re.search(r"\bcru[as]?\b", t):
        problemas.append("cita alimento cru")
    permitidos = {termo for a in alimentos for termo in TERMOS_ALIMENTOS.get(a, [])}
    conhecidos = {termo for termos in TERMOS_ALIMENTOS.values() for termo in termos} | set(TERMOS_FORA_DA_BASE)
    fora = sorted(p for p in conhecidos - permitidos if re.search(rf"\b{p}\b", t))
    if fora:
        problemas.append("cita alimento fora da cesta: " + ", ".join(fora))
    return problemas
