import pytest

from economia.receitas.aplicacao.indexar_base import (
    amostra_fixa,
    indexar,
    montar_trechos,
)
from economia.receitas.dominio.modelos import (
    Documento,
    Fonte,
    Ingrediente,
    Receita,
    Secao,
    TipoDeTrecho,
)

FONTE = Fonte(titulo="afrodite.json", instituicao="GitHub")


class GeradorFalso:
    nome = "falso"
    dimensao = 2

    def __init__(self):
        self.lotes = []

    def gerar_para_trechos(self, textos):
        self.lotes.append(list(textos))
        return [[1.0, 0.0] for _ in textos]

    def gerar_para_pergunta(self, pergunta):
        return [1.0, 0.0]


class RepositorioFalso:
    def __init__(self):
        self.preparado = None
        self.gravados = []

    def preparar(self, dimensao, recriar=False):
        self.preparado = (dimensao, recriar)

    def gravar(self, trechos, vetores):
        self.gravados += list(zip(trechos, vetores, strict=True))

    def buscar(self, vetor, limite, tipo=None):
        return []

    def contar(self):
        return len(self.gravados)


def receita(id: str, preparo=("Misture.",)) -> Receita:
    return Receita(
        documento_id=id,
        titulo=id,
        ingredientes=(Ingrediente("ovo"),),
        modo_de_preparo=preparo,
        fonte=FONTE,
    )


def test_montar_trechos_descarta_receitas_incompletas_e_fragmenta_documentos():
    documento = Documento(
        documento_id="guia",
        titulo="Guia",
        secoes=(Secao(titulo="S", paragrafos=("Coma comida de verdade.",)),),
        fonte=FONTE,
    )
    trechos, descartadas = montar_trechos(
        [receita("a"), receita("b", preparo=())], [documento]
    )
    assert [t.id for t in trechos] == ["a", "guia:0:0"]
    assert descartadas == 1


def test_indexar_grava_em_lotes(trecho):
    trechos = [trecho(str(n)) for n in range(5)]
    gerador, repositorio = GeradorFalso(), RepositorioFalso()
    progresso = []
    resultado = indexar(
        trechos,
        gerador,
        repositorio,
        tamanho_do_lote=2,
        recriar=True,
        ao_progredir=lambda feitos, total: progresso.append((feitos, total)),
    )
    assert repositorio.preparado == (2, True)
    assert [len(lote) for lote in gerador.lotes] == [2, 2, 1]
    assert [t.id for t, _ in repositorio.gravados] == ["0", "1", "2", "3", "4"]
    assert progresso == [(2, 5), (4, 5), (5, 5)]
    assert resultado.trechos == 5


def test_indexar_recusa_lote_vazio(trecho):
    with pytest.raises(ValueError):
        indexar([trecho("a")], GeradorFalso(), RepositorioFalso(), tamanho_do_lote=0)


def test_indexar_falha_se_o_gerador_perder_vetores(trecho):
    class GeradorQuebrado(GeradorFalso):
        def gerar_para_trechos(self, textos):
            return []

    with pytest.raises(RuntimeError):
        indexar([trecho("a")], GeradorQuebrado(), RepositorioFalso())


def test_amostra_fixa_mantem_a_orientacao_e_divide_as_receitas_entre_as_fontes(trecho):
    trechos = (
        [trecho(f"a{n}", fonte="afrodite.json") for n in range(5)]
        + [trecho(f"r{n}", fonte="RecipeNLG") for n in range(5)]
        + [
            trecho(f"g{n}", tipo=TipoDeTrecho.CONHECIMENTO, fonte="Guia")
            for n in range(3)
        ]
    )
    amostra = amostra_fixa(trechos, receitas=4)
    assert [t.id for t in amostra] == ["a0", "a1", "r0", "r1", "g0", "g1", "g2"]
    assert amostra_fixa(trechos, receitas=4) == amostra
