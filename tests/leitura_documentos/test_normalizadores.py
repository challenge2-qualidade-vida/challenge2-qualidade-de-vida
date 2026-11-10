from economia.leitura_documentos.infraestrutura.ingestao.normalizadores import normalizar_texto


def test_normalizar_texto_preserva_paragrafos():
    texto = "  primeira   linha  \r\n\r\n\r\n segunda\tlinha "
    assert normalizar_texto(texto) == "primeira linha\n\nsegunda linha"


def test_normalizar_texto_converte_quebra_de_linha():
    texto = "primeira linha\rsegunda linha"
    assert normalizar_texto(texto) == "primeira linha\nsegunda linha"


def test_normalizar_texto_remove_espacos_externos():
    texto = "   conteúdo com espaços   "
    assert normalizar_texto(texto) == "conteúdo com espaços"


def test_normalizar_texto_vazio():
    assert normalizar_texto("") == ""


def test_normalizar_texto_apenas_espacos():
    assert normalizar_texto("   \t   ") == ""
