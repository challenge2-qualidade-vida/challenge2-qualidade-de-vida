"""Valida a busca semântica real da Research Agent."""

from economia.compartilhado.configuracao import obter_configuracao
from economia.compartilhado.infraestrutura.embeddings_e5 import GeradorE5
from economia.pesquisa_evidencias.infraestrutura.pesquisador_qdrant import (
    PesquisadorQdrant,
)
from economia.pesquisa_evidencias.infraestrutura.repositorio_qdrant import (
    RepositorioQdrant,
)


def main() -> None:
    configuracao = obter_configuracao()

    gerador = GeradorE5(
        dispositivo=configuracao.dispositivo_embeddings,
    )

    repositorio = RepositorioQdrant.conectar(
        url=configuracao.qdrant_url,
        colecao=configuracao.colecao_pesquisa_evidencias,
    )

    pesquisador = PesquisadorQdrant(
        gerador=gerador,
        repositorio=repositorio,
    )

    pergunta = (
        "Quais alimentos são fontes de fibras e como contribuem "
        "para a saúde intestinal?"
    )

    print("Pergunta:", pergunta)
    print("Pesquisando evidências...\n")

    evidencias = pesquisador.pesquisar(
        pergunta=pergunta,
        limite=5,
    )

    print(f"Evidências recuperadas: {len(evidencias)}\n")

    for indice, evidencia in enumerate(evidencias, start=1):
        trecho = evidencia.trecho
        documento = evidencia.documento

        print(f"--- EVIDÊNCIA {indice} ---")
        print(f"Similaridade: {evidencia.score:.4f}")
        print(f"Fonte: {documento.fonte.titulo}")
        print(f"Instituição: {documento.fonte.instituicao}")
        print(f"Ano: {documento.fonte.ano}")
        print(f"Arquivo: {documento.arquivo}")
        print(f"Páginas: {trecho.pagina_inicial} a {trecho.pagina_final}")
        print(f"URL: {documento.fonte.url}")
        print(f"Trecho: {trecho.texto[:700]}")
        print()


if __name__ == "__main__":
    main()
