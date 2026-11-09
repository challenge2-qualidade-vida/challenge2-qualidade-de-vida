import json
from pathlib import Path

from economia.leitura_documentos.infraestrutura.ingestao.pipeline import (
    preparar_documentos,
)


def criar_manifesto(caminho: Path, fontes: list) -> None:
    """Cria um manifesto temporário para os testes."""
    caminho.write_text(
        json.dumps({"fontes": fontes}, ensure_ascii=False),
        encoding="utf-8",
    )


def criar_metadados(arquivo: str) -> dict:
    """Retorna metadados válidos para um documento."""
    return {
        "arquivo": arquivo,
        "titulo": "Guia alimentar",
        "instituicao": "Ministério da Saúde",
        "ano": 2014,
        "tipo_conteudo": "orientacao",
        "url": "https://www.gov.br/saude",
    }


def test_arquivo_sem_metadados_nao_e_processado(tmp_path: Path):
    entrada = tmp_path / "base"
    entrada.mkdir()

    (entrada / "guia.txt").write_text(
        "Conteúdo de teste.",
        encoding="utf-8",
    )

    manifesto = tmp_path / "fontes.json"
    criar_manifesto(manifesto, [])

    saida = tmp_path / "out/documentos.jsonl"
    relatorio = tmp_path / "out/relatorio.json"

    resultado = preparar_documentos(
        entrada, manifesto, saida, relatorio
    )

    assert resultado["sem_metadados"] == 1
    assert saida.read_text(encoding="utf-8") == ""


def test_documento_com_metadados_e_processado(tmp_path: Path):
    entrada = tmp_path / "base"
    entrada.mkdir()

    (entrada / "guia.txt").write_text(
        "Conteúdo de teste.",
        encoding="utf-8",
    )

    manifesto = tmp_path / "fontes.json"
    criar_manifesto(manifesto, [criar_metadados("guia.txt")])

    saida = tmp_path / "out/documentos.jsonl"
    relatorio = tmp_path / "out/relatorio.json"

    resultado = preparar_documentos(
        entrada, manifesto, saida, relatorio
    )

    registros = [
        json.loads(linha)
        for linha in saida.read_text(encoding="utf-8").splitlines()
    ]

    assert resultado["processados"] == 1
    assert len(registros) == 1
    assert registros[0]["texto"] == "Conteúdo de teste."
    assert registros[0]["fonte"] == "Guia alimentar"


def test_documento_sem_texto_e_identificado(tmp_path: Path):
    entrada = tmp_path / "base"
    entrada.mkdir()

    (entrada / "guia.txt").write_text(
        "   ",
        encoding="utf-8",
    )

    manifesto = tmp_path / "fontes.json"
    criar_manifesto(manifesto, [criar_metadados("guia.txt")])

    saida = tmp_path / "out/documentos.jsonl"
    relatorio = tmp_path / "out/relatorio.json"

    resultado = preparar_documentos(
        entrada, manifesto, saida, relatorio
    )

    assert resultado["sem_texto"] == 1
    assert saida.read_text(encoding="utf-8") == ""


def test_erro_na_extracao_e_registrado(tmp_path: Path, monkeypatch):
    entrada = tmp_path / "base"
    entrada.mkdir()

    (entrada / "guia.txt").write_text(
        "Conteúdo de teste.",
        encoding="utf-8",
    )

    manifesto = tmp_path / "fontes.json"
    criar_manifesto(manifesto, [criar_metadados("guia.txt")])

    saida = tmp_path / "out/documentos.jsonl"
    relatorio = tmp_path / "out/relatorio.json"

    def simular_erro(caminho: Path) -> str:
        raise ValueError("Erro simulado na extração")

    monkeypatch.setattr(
        "economia.leitura_documentos.infraestrutura.ingestao.pipeline.extrair_texto",
        simular_erro,
    )

    resultado = preparar_documentos(
        entrada, manifesto, saida, relatorio
    )

    assert resultado["erros"] == 1
    assert saida.read_text(encoding="utf-8") == ""

    dados_relatorio = json.loads(
        relatorio.read_text(encoding="utf-8")
    )

    assert dados_relatorio["erros"][0]["motivo"] == (
        "Erro simulado na extração"
    )
