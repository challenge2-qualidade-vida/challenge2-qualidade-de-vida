"""Caso de uso: responder uma pergunta com os trechos da base e as fontes.

Fluxo: preço atual (RN04) → recuperar → limiar (RN11) → ingredientes da pergunta → desempate
pelos ingredientes que faltam → LLM com trechos numerados → fontes (RN10).
As fontes e os ingredientes que faltam são montados pelo código, nunca escritos pelo LLM (RN01).
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence

from pydantic import BaseModel, ValidationError

from economia.receitas.aplicacao.portas import (
    GeradorDeEmbeddings,
    ModeloDeLinguagem,
    RepositorioDeTrechos,
)
from economia.receitas.dominio.correspondencia import ingredientes_que_faltam
from economia.receitas.dominio.modelos import (
    Fonte,
    RespostaComFontes,
    TipoDeTrecho,
    TrechoRecuperado,
)
from economia.receitas.dominio.ordenacao import desempatar

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
    """Numera as citações de 1 a n na ordem do ranking e apaga as de trechos inexistentes.

    A ordem do ranking (score e desempate) vale para a lista de fontes, não a ordem em que
    o LLM citou: a receita completa continua antes da que tem ingredientes faltando.
    """
    novo = {antigo: n for n, antigo in enumerate(sorted(citados), start=1)}

    def trocar(m: re.Match) -> str:
        antigo = int(m.group(1))
        return f"[{novo[antigo]}]" if antigo in novo else ""

    return _CITACAO.sub(trocar, texto).strip()


def formatar_fonte(recuperado: TrechoRecuperado) -> str:
    """Citação legível de um trecho: título, origem, ano, lugar no documento, link e licença."""
    trecho, fonte = recuperado.trecho, recuperado.trecho.fonte
    partes = [trecho.titulo] if trecho.tipo is TipoDeTrecho.RECEITA else []
    # sem repetir o nome quando um contém o outro (ex.: "afrodite.json (dataset no GitHub)")
    if fonte.instituicao in fonte.titulo:
        origem = fonte.titulo
    elif fonte.titulo in fonte.instituicao:
        origem = fonte.instituicao
    else:
        origem = f"{fonte.titulo} ({fonte.instituicao})"
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


class IngredientesDaPergunta(BaseModel):
    """Saída do LLM ao interpretar a pergunta: só os ingredientes citados, em dois idiomas."""

    ingredientes_pt: list[str] = []
    ingredientes_en: list[str] = []

    def no_idioma(self, idioma: str) -> list[str]:
        return self.ingredientes_en if idioma == "en" else self.ingredientes_pt


def bloco_de_ingredientes_que_faltam(
    trechos: Iterable[TrechoRecuperado], faltando: dict[str, tuple[str, ...]]
) -> str:
    """Texto montado pelo código com o que falta em cada receita usada (RN01, RN13)."""
    linhas = []
    for n, recuperado in enumerate(trechos, start=1):
        trecho = recuperado.trecho
        if trecho.tipo is TipoDeTrecho.RECEITA and trecho.id in faltando:
            itens = ", ".join(faltando[trecho.id]) or "nenhum"
            linhas.append(f"- {trecho.titulo} [{n}]: {itens}")
    return "Ingredientes que faltam:\n" + "\n".join(linhas) if linhas else ""


class ResponderPergunta:
    def __init__(
        self,
        gerador: GeradorDeEmbeddings,
        repositorio: RepositorioDeTrechos,
        llm: ModeloDeLinguagem,
        prompt_do_sistema: str,
        limiar: float,
        quantidade: int = 5,
        prompt_de_extracao: str | None = None,
        ingredientes_basicos: Sequence[str] = (),
        tolerancia: float = 0.0,
    ):
        self._gerador = gerador
        self._repositorio = repositorio
        self._llm = llm
        self._prompt = prompt_do_sistema
        self._limiar = limiar
        self._quantidade = quantidade
        self._prompt_de_extracao = prompt_de_extracao
        self._basicos = tuple(ingredientes_basicos)
        self._tolerancia = tolerancia

    def recuperar(self, pergunta: str) -> list[TrechoRecuperado]:
        """Top-k trechos acima do limiar, do maior score para o menor."""
        vetor = self._gerador.gerar_para_pergunta(pergunta)
        recuperados = self._repositorio.buscar(vetor, self._quantidade)
        return [r for r in recuperados if r.score >= self._limiar]

    def extrair_ingredientes(self, pergunta: str) -> IngredientesDaPergunta:
        """O LLM só interpreta a pergunta. Saída inválida vale como "nenhum ingrediente"."""
        if not self._prompt_de_extracao:
            return IngredientesDaPergunta()
        try:
            dados = self._llm.gerar_json(
                self._prompt_de_extracao,
                f"Pergunta: {pergunta}",
                IngredientesDaPergunta.model_json_schema(),
            )
            return IngredientesDaPergunta.model_validate(dados)
        except (ValidationError, ValueError):
            return IngredientesDaPergunta()

    def contar_faltantes(
        self,
        recuperados: Sequence[TrechoRecuperado],
        disponiveis: IngredientesDaPergunta,
    ) -> dict[str, tuple[str, ...]]:
        """Ingredientes que faltam em cada receita recuperada, por função determinística."""
        return {
            r.trecho.id: tuple(
                ingredientes_que_faltam(
                    r.trecho.ingredientes,
                    disponiveis.no_idioma(r.trecho.idioma),
                    self._basicos,
                    r.trecho.idioma,
                )
            )
            for r in recuperados
            if r.trecho.tipo is TipoDeTrecho.RECEITA
        }

    def ordenar(
        self, recuperados: list[TrechoRecuperado], faltando: dict[str, tuple[str, ...]]
    ) -> list[TrechoRecuperado]:
        """Desempate do top-k: com scores na faixa de tolerância, menos ingredientes faltando primeiro.

        Trechos de orientação não têm ingredientes e contam como 0 faltando.
        """
        return desempatar(
            recuperados,
            score=lambda r: r.score,
            faltando=lambda r: len(faltando.get(r.trecho.id, ())),
            tolerancia=self._tolerancia,
        )

    def responder(self, pergunta: str) -> RespostaComFontes:
        if e_pergunta_de_preco(pergunta):
            return RespostaComFontes(texto=AVISO_DE_PRECO, encontrou=False)

        recuperados = self.recuperar(pergunta)
        if not recuperados:
            return RespostaComFontes(texto=NAO_ENCONTREI, encontrou=False)

        disponiveis = IngredientesDaPergunta()
        faltando: dict[str, tuple[str, ...]] = {}
        if any(r.trecho.tipo is TipoDeTrecho.RECEITA for r in recuperados):
            disponiveis = self.extrair_ingredientes(pergunta)
            if disponiveis.ingredientes_pt or disponiveis.ingredientes_en:
                faltando = self.contar_faltantes(recuperados, disponiveis)
                recuperados = self.ordenar(recuperados, faltando)

        texto = self._llm.gerar(self._prompt, montar_mensagem(pergunta, recuperados))
        citados = citacoes_validas(texto, len(recuperados))
        if MARCA_DE_NAO_ENCONTRADO in texto or not citados:
            # sem citação não há como dizer de onde veio a resposta (RN10): vale a RN11
            return RespostaComFontes(texto=NAO_ENCONTREI, encontrou=False)

        usados = tuple(recuperados[n - 1] for n in sorted(citados))
        texto = renumerar(texto, citados)
        bloco = bloco_de_ingredientes_que_faltam(usados, faltando)
        return RespostaComFontes(
            texto=f"{texto}\n\n{bloco}" if bloco else texto,
            encontrou=True,
            trechos=usados,
            fontes=_fontes_unicas(usados),
            ingredientes_disponiveis=tuple(disponiveis.ingredientes_pt),
            faltando=tuple(
                (r.trecho.id, faltando[r.trecho.id])
                for r in usados
                if r.trecho.id in faltando
            ),
        )
