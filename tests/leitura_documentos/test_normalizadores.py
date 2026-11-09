from economia.leitura_documentos.infraestrutura.ingestao.normalizadores import normalizar_texto

def test_normalizar_texto_preserva_paragrafos():
    texto = "  primeira   linha  \r\n\r\n\r\n segunda\tlinha "
    assert normalizar_texto(texto) == "primeira linha\n\nsegunda linha"
