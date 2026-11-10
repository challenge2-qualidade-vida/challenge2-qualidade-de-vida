import pytest

from economia.receitas.dominio.modelos import Fonte, TipoDeTrecho, Trecho


def criar_trecho(
    id: str,
    tipo: TipoDeTrecho = TipoDeTrecho.RECEITA,
    fonte: str = "afrodite.json",
    ingredientes: tuple[str, ...] = (),
    titulo: str | None = None,
) -> Trecho:
    return Trecho(
        id=id,
        tipo=tipo,
        documento_id=id,
        titulo=titulo or f"Título {id}",
        texto=f"texto {id}",
        conteudo=f"conteúdo {id}",
        fonte=Fonte(
            titulo=fonte,
            instituicao=f"instituição {fonte}",
            ano=2014,
            url="https://exemplo.org",
        ),
        ingredientes=ingredientes,
    )


@pytest.fixture
def trecho():
    return criar_trecho
