import json
from pathlib import Path
from economia.leitura_documentos.infraestrutura.ingestao.pipeline import preparar_documentos

def test_arquivo_sem_metadados_nao_e_processado(tmp_path: Path):
    entrada = tmp_path / "base"
    entrada.mkdir()
    (entrada / "guia.txt").write_text("Conteúdo de teste.", encoding="utf-8")
    manifesto = tmp_path / "fontes.json"
    manifesto.write_text(json.dumps({"fontes": []}), encoding="utf-8")
    saida = tmp_path / "out/documentos.jsonl"
    relatorio = tmp_path / "out/relatorio.json"
    resultado = preparar_documentos(entrada, manifesto, saida, relatorio)
    assert resultado["sem_metadados"] == 1
    assert saida.read_text(encoding="utf-8") == ""
