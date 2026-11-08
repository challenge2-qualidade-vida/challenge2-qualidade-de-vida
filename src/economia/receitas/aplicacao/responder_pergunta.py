"""Caso de uso: responder uma pergunta com os trechos da base e as fontes.

Fluxo: preço atual (RN04) → recuperar → limiar (RN11) → LLM com trechos numerados → fontes (RN10).
As fontes são montadas pelo código a partir dos trechos citados, nunca escritas pelo LLM.
"""

import re
import unicodedata
from collections.abc import Sequence

from economia.receitas.aplicacao.portas import (
    GeradorDeEmbeddings,
    ModeloDeLinguagem,
    RepositorioDeTrechos,
)
from economia.receitas.dominio.modelos import (
    Fonte,
    RespostaComFontes,
    TipoDeTrecho,
    TrechoRecuperado,
)

AVISO_DE_PRECO = (
    "Preços atuais não vêm da base de conhecimento de receitas e alimentação. "
    "Para saber quanto um produto custa hoje, consulte os preços cadastrados dos mercados."
)
NAO_ENCONTREI = (
    "Não encontrei essa informação na base de conhecimento. "
    "Prefiro não responder a inventar uma resposta."
)
MARCA_DE_NAO_ENCONTRADO = "NAO_ENCONTRADO"

_CITACAO = re.compile(r"\[(\d+)\]")
# Só o preço *atual* fica fora da base (RN04). Perguntas de consumo, como "como avaliar uma
# promoção" ou "o que é preço por unidade", são respondidas pela base.
_PERGUNTA_DE_PRECO = (
    re.compile(r"\bquanto (custa|custam|esta|estao|ta|sai|saem|vale|valem)\b"),
    re.compile(
        r"\b(preco|precos|valor)\b.*\b(hoje|atual|atuais|agora|no mercado|nos mercados)\b"
    ),
    re.compile(r"\bonde\b.*\bmais barat[oa]s?\b"),
)


def _sem_acento(texto: str) -> str:
    return (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    )


def e_pergunta_de_preco(pergunta: str) -> bool:
    """Regra determinística: perguntas sobre preço não passam pela base (RN04)."""
    texto = _sem_acento(pergunta)
    return any(regra.search(texto) for regra in _PERGUNTA_DE_PRECO)


def montar_mensagem(pergunta: str, trechos: Sequence[TrechoRecuperado]) -> str:
    """Pergunta e trechos numerados [1]…[n], que o LLM cita pelo número."""
    blocos = []
    for n, recuperado in enumerate(trechos, start=1):
        trecho = recuperado.trecho
        rotulo = "Receita" if trecho.tipo is TipoDeTrecho.RECEITA else "Orientação"
        cabecalho = f"[{n}] {rotulo}: {trecho.titulo}"
        if trecho.secao and trecho.secao != trecho.titulo:
            cabecalho += f" — {trecho.secao}"
        blocos.append(f"{cabecalho}\n{trecho.conteudo}")
    return f"Pergunta: {pergunta}\n\nTrechos:\n\n" + "\n\n".join(blocos)


def citacoes_validas(texto: str, quantidade: int) -> list[int]:
    """Números citados pelo LLM que existem, na ordem da primeira citação."""
    vistos: list[int] = []
    for numero in (int(n) for n in _CITACAO.findall(texto)):
        if 1 <= numero <= quantidade and numero not in vistos:
            vistos.append(numero)
    return vistos


def renumerar(texto: str, citados: Sequence[int]) -> str:
    """Troca os números do LLM pela ordem das fontes e apaga citações de trechos inexistentes."""
    novo = {antigo: n for n, antigo in enumerate(citados, start=1)}

    def trocar(m: re.Match) -> str:
        antigo = int(m.group(1))
        return f"[{novo[antigo]}]" if antigo in novo else ""

    return _CITACAO.sub(trocar, texto).strip()


def formatar_fonte(recuperado: TrechoRecuperado) -> str:
    """Citação legível de um trecho: título, origem, ano, lugar no documento, link e licença."""
    trecho, fonte = recuperado.trecho, recuperado.trecho.fonte
    partes = [trecho.titulo] if trecho.tipo is TipoDeTrecho.RECEITA else []
    origem = (
        fonte.titulo
        if fonte.instituicao in fonte.titulo
        else f"{fonte.titulo} ({fonte.instituicao})"
    )
    partes.append(f"{origem}, {fonte.ano}" if fonte.ano else origem)
    if trecho.capitulo:
        partes.append(trecho.capitulo)
    if trecho.secao and trecho.secao != trecho.capitulo:
        partes.append(trecho.secao)
    if trecho.pagina:
        partes.append(f"p. {trecho.pagina}")
    texto = ". ".join(partes) + "."
    if fonte.url:
        texto += f" {fonte.url}"
    if fonte.licenca:
        texto += f" Licença: {fonte.licenca}."
    return texto


def _fontes_unicas(trechos: Sequence[TrechoRecuperado]) -> tuple[Fonte, ...]:
    fontes: list[Fonte] = []
    for recuperado in trechos:
        if recuperado.trecho.fonte not in fontes:
            fontes.append(recuperado.trecho.fonte)
    return tuple(fontes)


class ResponderPergunta:
    def __init__(
        self,
        gerador: GeradorDeEmbeddings,
        repositorio: RepositorioDeTrechos,
        llm: ModeloDeLinguagem,
        prompt_do_sistema: str,
        limiar: float,
        quantidade: int = 5,
    ):
        self._gerador = gerador
        self._repositorio = repositorio
        self._llm = llm
        self._prompt = prompt_do_sistema
        self._limiar = limiar
        self._quantidade = quantidade

    def recuperar(self, pergunta: str) -> list[TrechoRecuperado]:
        """Top-k trechos acima do limiar, do maior score para o menor."""
        vetor = self._gerador.gerar_para_pergunta(pergunta)
        recuperados = self._repositorio.buscar(vetor, self._quantidade)
        return [r for r in recuperados if r.score >= self._limiar]

    def ordenar(
        self, pergunta: str, recuperados: list[TrechoRecuperado]
    ) -> list[TrechoRecuperado]:
        """Ponto de extensão para o desempate pelos ingredientes que faltam (fase 7b)."""
        return recuperados

    def responder(self, pergunta: str) -> RespostaComFontes:
        if e_pergunta_de_preco(pergunta):
            return RespostaComFontes(texto=AVISO_DE_PRECO, encontrou=False)

        recuperados = self.recuperar(pergunta)
        if not recuperados:
            return RespostaComFontes(texto=NAO_ENCONTREI, encontrou=False)
        recuperados = self.ordenar(pergunta, recuperados)

        texto = self._llm.gerar(self._prompt, montar_mensagem(pergunta, recuperados))
        citados = citacoes_validas(texto, len(recuperados))
        if MARCA_DE_NAO_ENCONTRADO in texto or not citados:
            # sem citação não há como dizer de onde veio a resposta (RN10): vale a RN11
            return RespostaComFontes(texto=NAO_ENCONTREI, encontrou=False)

        usados = tuple(recuperados[n - 1] for n in citados)
        return RespostaComFontes(
            texto=renumerar(texto, citados),
            encontrou=True,
            trechos=usados,
            fontes=_fontes_unicas(usados),
        )
