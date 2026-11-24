"""Executa a indexação da base científica da Research Agent."""

from pathlib import Path

from economia.compartilhado.configuracao import obter_configuracao
from economia.compartilhado.infraestrutura.embeddings_e5 import (
    GeradorE5,
    contador_de_tokens_e5,
)
from economia.leitura_documentos.infraestrutura.ingestao.leitor_documental import (
    LeitorDocumentalPDF,
)
from economia.pesquisa_evidencias.infraestrutura.indexador import (
    IndexadorEvidencias,
)
from economia.pesquisa_evidencias.infraestrutura.preparador_documentos import (
    PreparadorDocumentos,
)
from economia.pesquisa_evidencias.infraestrutura.repositorio_qdrant import (
    RepositorioQdrant,
)


def main() -> None:
    """Inicializa os componentes e executa a indexação."""
    configuracao = obter_configuracao()

    pasta_base = Path("data/base-conhecimento")
    caminho_manifesto = pasta_base / "fontes.json"

    if not pasta_base.is_dir():
        raise FileNotFoundError(f"Pasta de documentos não encontrada: {pasta_base}")

    if not caminho_manifesto.is_file():
        raise FileNotFoundError(f"Manifesto não encontrado: {caminho_manifesto}")

    print("1/5 - Carregando contador de tokens E5...")
    contar_tokens = contador_de_tokens_e5()

    print("2/5 - Inicializando modelo de embeddings...")
    gerador = GeradorE5(
        dispositivo=configuracao.dispositivo_embeddings,
    )

    print("3/5 - Conectando ao Qdrant...")
    repositorio = RepositorioQdrant.conectar(
        url=configuracao.qdrant_url,
        colecao=configuracao.colecao_pesquisa_evidencias,
    )

    print("4/5 - Preparando indexador...")
    preparador = PreparadorDocumentos(
        leitor_documental=LeitorDocumentalPDF(),
        contar_tokens=contar_tokens,
    )

    indexador = IndexadorEvidencias(
        preparador=preparador,
        gerador=gerador,
        repositorio=repositorio,
        pasta_base=pasta_base,
        caminho_manifesto=caminho_manifesto,
        tamanho_lote=64,
    )

    print("5/5 - Executando indexação...")
    resultado = indexador.executar()

    total_qdrant = repositorio.contar()

    print("\n=== RESULTADO DA INDEXAÇÃO ===")
    print(f"Documentos processados: {resultado['documentos']}")
    print(f"Trechos processados: {resultado['trechos']}")
    print(f"Lotes gravados: {resultado['lotes']}")
    print(f"Pontos na coleção: {total_qdrant}")
    print(f"Coleção: {configuracao.colecao_pesquisa_evidencias}")

    if total_qdrant != resultado["trechos"]:
        raise RuntimeError(
            "A quantidade de pontos no Qdrant não corresponde "
            "à quantidade de trechos processados."
        )

    print("\nINDEXAÇÃO VALIDADA COM SUCESSO!")


if __name__ == "__main__":
    main()
