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
_CITACAO_AGRUPADA = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)+)\]")


def desagrupar_citacoes(texto: str) -> str:
    """Troca citações agrupadas, como "[1, 3]", por citações separadas: "[1][3]"."""
    return _CITACAO_AGRUPADA.sub(
        lambda m: "".join(f"[{n}]" for n in re.findall(r"\d+", m.group(1))), texto
    )


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


def numeros_validos(numeros: Iterable[int], quantidade: int) -> list[int]:
    """Números de trechos que existem, sem repetição, na ordem em que apareceram."""
    vistos: list[int] = []
    for numero in numeros:
        if 1 <= numero <= quantidade and numero not in vistos:
            vistos.append(numero)
    return vistos


def citacoes_validas(texto: str, quantidade: int) -> list[int]:
    """Números citados pelo LLM que existem, na ordem da primeira citação."""
    return numeros_validos((int(n) for n in _CITACAO.findall(texto)), quantidade)


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


MAXIMO_DE_INGREDIENTES_BUSCADOS = 6
RECEITAS_POR_INGREDIENTE = 1


class RespostaDoLLM(BaseModel):
    """Saída estruturada do LLM ao redigir a resposta (prompt resposta_com_fontes_v2).

    Com o esquema JSON, a lista dos trechos usados não depende de o modelo lembrar de escrever
    os colchetes no texto. As fontes continuam montadas pelo código a partir desses números (RN10).
    """

    encontrou: bool
    resposta: str = ""
    trechos_usados: list[int] = []


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
        resposta_estruturada: bool = False,
        pedido_de_citacao: str | None = None,
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
        self._estruturada = resposta_estruturada
        # com o pedido, uma resposta sem citação ganha uma segunda tentativa antes de virar
        # "não encontrei"; sem ele, vale a regra da versão 1 (descarta na primeira)
        self._pedido_de_citacao = pedido_de_citacao

    @property
    def limiar(self) -> float:
        return self._limiar

    def buscar(self, pergunta: str) -> list[TrechoRecuperado]:
        """Top-k trechos mais próximos da pergunta, sem aplicar o limiar."""
        vetor = self._gerador.gerar_para_pergunta(pergunta)
        return self._repositorio.buscar(vetor, self._quantidade)

    def recuperar(self, pergunta: str) -> list[TrechoRecuperado]:
        """Top-k trechos acima do limiar, do maior score para o menor."""
        return self._acima_do_limiar(self.buscar(pergunta))

    def _acima_do_limiar(
        self, recuperados: Sequence[TrechoRecuperado]
    ) -> list[TrechoRecuperado]:
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

    def somar_receitas_por_ingrediente(
        self,
        recuperados: list[TrechoRecuperado],
        disponiveis: IngredientesDaPergunta,
    ) -> list[TrechoRecuperado]:
        """Com 2 ou mais ingredientes, busca receitas para cada um e soma às da busca geral.

        Uma pergunta como "quero um almoço com arroz, feijão, carne e alface" vira um vetor só,
        que costuma trazer textos gerais sobre refeições. Buscar "Receita com <ingrediente>"
        só entre as receitas garante pelo menos uma opção para cada ingrediente, se houver
        uma acima do limiar. A lista final vem sem repetição e com no máximo um trecho a mais
        que o número de ingredientes, para caber no contexto do LLM.
        """
        ingredientes = disponiveis.ingredientes_pt
        if len(ingredientes) < 2:
            return recuperados
        por_ingrediente: list[TrechoRecuperado] = []
        for ingrediente in ingredientes[:MAXIMO_DE_INGREDIENTES_BUSCADOS]:
            vetor = self._gerador.gerar_para_pergunta(f"Receita com {ingrediente}")
            achados = self._repositorio.buscar(
                vetor, RECEITAS_POR_INGREDIENTE, tipo=TipoDeTrecho.RECEITA
            )
            por_ingrediente += [r for r in achados if r.score >= self._limiar]
        limite = max(self._quantidade, len(ingredientes) + 1)
        # o score que vale é o da pergunta inteira; o da busca por ingrediente só entra para a
        # receita que a busca geral não trouxe (senão o desempate da RN13 sai distorcido)
        da_pergunta = {r.trecho.id: r for r in recuperados}
        garantidos: dict[str, TrechoRecuperado] = {}
        for achado in por_ingrediente:
            garantidos.setdefault(
                achado.trecho.id, da_pergunta.get(achado.trecho.id, achado)
            )
        escolhidos = list(garantidos.values())[:limite]
        for recuperado in sorted(recuperados, key=lambda r: r.score, reverse=True):
            if len(escolhidos) >= limite:
                break
            if recuperado.trecho.id not in garantidos:
                escolhidos.append(recuperado)
        return sorted(escolhidos, key=lambda r: r.score, reverse=True)

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

        mais_proximos = self.buscar(pergunta)
        recuperados = self._acima_do_limiar(mais_proximos)
        if not recuperados:
            return RespostaComFontes(
                texto=NAO_ENCONTREI, encontrou=False, recuperados=tuple(mais_proximos)
            )

        disponiveis = IngredientesDaPergunta()
        faltando: dict[str, tuple[str, ...]] = {}
        if any(r.trecho.tipo is TipoDeTrecho.RECEITA for r in recuperados):
            disponiveis = self.extrair_ingredientes(pergunta)
            if disponiveis.ingredientes_pt or disponiveis.ingredientes_en:
                recuperados = self.somar_receitas_por_ingrediente(
                    recuperados, disponiveis
                )
                faltando = self.contar_faltantes(recuperados, disponiveis)
                recuperados = self.ordenar(recuperados, faltando)

        texto, citados = self.redigir(pergunta, recuperados)
        if not citados:
            # sem citação não há como dizer de onde veio a resposta (RN10): vale a RN11
            return RespostaComFontes(
                texto=NAO_ENCONTREI, encontrou=False, recuperados=tuple(recuperados)
            )

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
            recuperados=tuple(recuperados),
        )

    def redigir(
        self, pergunta: str, recuperados: Sequence[TrechoRecuperado]
    ) -> tuple[str, list[int]]:
        """Texto do LLM e os números dos trechos citados. Sem citação válida, a lista vem vazia."""
        mensagem = montar_mensagem(pergunta, recuperados)
        texto, citados, recusou = self._uma_tentativa(mensagem, len(recuperados))
        if citados or recusou or not self._pedido_de_citacao or not texto.strip():
            return texto, citados
        pedido = self._pedido_de_citacao.replace("{resposta}", texto)
        texto, citados, _ = self._uma_tentativa(
            f"{mensagem}\n\n{pedido}", len(recuperados)
        )
        return texto, citados

    def _uma_tentativa(
        self, mensagem: str, quantidade: int
    ) -> tuple[str, list[int], bool]:
        """Uma chamada ao LLM: texto, trechos citados e se ele disse que não encontrou."""
        if not self._estruturada:
            texto = desagrupar_citacoes(self._llm.gerar(self._prompt, mensagem))
            if MARCA_DE_NAO_ENCONTRADO in texto:
                return texto, [], True
            return texto, citacoes_validas(texto, quantidade), False
        try:
            saida = RespostaDoLLM.model_validate(
                self._llm.gerar_json(
                    self._prompt, mensagem, RespostaDoLLM.model_json_schema()
                )
            )
        except (ValidationError, ValueError):
            return "", [], False
        if not saida.encontrou:
            return saida.resposta, [], True
        if not saida.resposta.strip():
            return "", [], False
        saida.resposta = desagrupar_citacoes(saida.resposta)
        citados = numeros_validos(
            [*citacoes_validas(saida.resposta, quantidade), *saida.trechos_usados],
            quantidade,
        )
        return saida.resposta, citados, False
