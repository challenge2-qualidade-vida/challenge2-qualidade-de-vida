"""Recuperação de trechos da base de conhecimento (o "R" do RAG).

Cada seção "## " de um .md em data/base-conhecimento/ vira um trecho, e cada
alimento da TACO vira outro. A busca usa TF-IDF (scikit-learn): é gratuita,
roda local, não baixa modelo nenhum e é determinística.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .dados import RAIZ, Base

PASTA_BASE = RAIZ / "data" / "base-conhecimento"
FONTE_TACO = "Tabela TACO 4ª ed. (NEPA/Unicamp), valores aproximados"

# Abaixo desta similaridade o trecho é considerado irrelevante.
SIMILARIDADE_MINIMA = 0.12

STOPWORDS = set(
    """a ao aos as com como da das de do dos e é em entre essa esse esta este eu
    isso la mais mas me meu minha muito na nas no nos o os ou para pela pelo por
    pra qual quais que se sem ser seu sua tem ter um uma uns umas vai voce voces""".split()
)

NOMES_GRUPOS = {
    "cereais": "cereais e pães", "tuberculos": "raízes e tubérculos", "leguminosas": "feijões",
    "proteina_animal": "carnes e ovos", "laticinios": "leite e queijos",
    "flv": "frutas, legumes e verduras", "oleos": "óleos", "acucar": "açúcar",
}


@dataclass(frozen=True)
class Trecho:
    id: str
    titulo: str
    texto: str
    fonte: str


@dataclass(frozen=True)
class Resultado:
    trecho: Trecho
    similaridade: float


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return sem_acento


def tokenizar(texto: str) -> list[str]:
    tokens = []
    for t in re.findall(r"[a-z0-9]+", normalizar(texto)):
        if t in STOPWORDS:
            continue
        # Plural simples: "feijoes" → "feijoe", "frutas" → "fruta".
        if len(t) > 4 and t.endswith("s"):
            t = t[:-1]
        tokens.append(t)
    return tokens


def ler_markdown(arquivo: Path) -> list[Trecho]:
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    titulo_doc, fonte = arquivo.stem, arquivo.name
    for linha in linhas:
        if linha.startswith("# "):
            titulo_doc = linha[2:].strip()
        elif linha.startswith("> Fonte:"):
            fonte = linha[len("> Fonte:"):].strip()
            break

    trechos, secao, corpo = [], None, []

    def fechar():
        if secao and corpo:
            n = len(trechos) + 1
            trechos.append(Trecho(f"{arquivo.stem}#{n}", f"{titulo_doc} — {secao}", "\n".join(corpo).strip(), fonte))

    for linha in linhas:
        if linha.startswith("## "):
            fechar()
            secao, corpo = linha[3:].strip(), []
        elif secao is not None and linha.strip():
            corpo.append(linha.strip())
    fechar()
    return trechos


def trechos_taco(base: Base) -> list[Trecho]:
    trechos = []
    for a in base.alimentos.values():
        texto = (
            f"{a.nome}: por 100 g tem {a.kcal:g} kcal, {a.proteina_g:g} g de proteína e {a.fibra_g:g} g de fibra. "
            f"Grupo: {NOMES_GRUPOS.get(a.grupo, a.grupo)}."
        )
        trechos.append(Trecho(f"taco#{a.id}", f"TACO — {a.nome}", texto, FONTE_TACO))
    return trechos


class BaseConhecimento:
    def __init__(self, base: Base | None = None, pasta: Path = PASTA_BASE):
        self.trechos: list[Trecho] = []
        for arquivo in sorted(pasta.glob("*.md")):
            if arquivo.name != "FONTES.md":
                self.trechos.extend(ler_markdown(arquivo))
        if base is not None:
            self.trechos.extend(trechos_taco(base))

        self._vetorizador = TfidfVectorizer(tokenizer=tokenizar, lowercase=False, token_pattern=None, ngram_range=(1, 2), sublinear_tf=True)
        self._matriz = self._vetorizador.fit_transform(f"{t.titulo}\n{t.texto}" for t in self.trechos)

    def buscar(self, pergunta: str, k: int = 3, minimo: float = SIMILARIDADE_MINIMA) -> list[Resultado]:
        """Os `k` trechos mais parecidos com a pergunta. Lista vazia = a base não sabe."""
        consulta = self._vetorizador.transform([pergunta])
        sims = cosine_similarity(consulta, self._matriz)[0]
        ordem = sims.argsort()[::-1][:k]
        return [Resultado(self.trechos[i], round(float(sims[i]), 3)) for i in ordem if sims[i] >= minimo]


def contexto_para_llm(resultados: list[Resultado]) -> str:
    """Formata os trechos para colocar no prompt do LLM, numerados para citação."""
    if not resultados:
        return "Nenhum trecho relevante encontrado na base de conhecimento."
    partes = [f"[{i}] {r.trecho.titulo}\n{r.trecho.texto}\n(Fonte: {r.trecho.fonte})" for i, r in enumerate(resultados, 1)]
    return "\n\n".join(partes)
