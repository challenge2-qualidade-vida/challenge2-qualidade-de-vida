import json

import pyarrow as pa
import pyarrow.parquet as pq

from economia.receitas.dominio.modelos import Fonte
from economia.receitas.infraestrutura.carregadores import (
    carregar_afrodite,
    carregar_recipenlg,
    documento_de_markdown,
    secoes_do_guia,
)

# ---------------------------------------------------------------- afrodite.json


def item_afrodite(oid: str, nome: str, secoes: list[tuple[str, list[str]]]) -> dict:
    return {
        "_id": {"$oid": oid},
        "nome": nome,
        "secao": [{"nome": n, "conteudo": c} for n, c in secoes],
    }


def test_afrodite_le_ingredientes_e_preparo(tmp_path):
    arquivo = tmp_path / "afrodite.json"
    itens = [
        item_afrodite(
            "1",
            " Bolo ",
            [
                (" Ingredientes", ["2 ovos", "Massa:", " ", "1 xícara de farinha"]),
                (" Modo de Preparo", ["1 - Bata os ovos.", "2 - Asse."]),
                (" Outras informações", ["Rendimento: 8 porções"]),
            ],
        )
    ]
    arquivo.write_text(json.dumps(itens), encoding="utf-8")
    [receita] = carregar_afrodite(arquivo)
    assert receita.documento_id == "afrodite:1"
    assert receita.titulo == "Bolo"
    # "Massa:" é título de subseção e linhas vazias saem
    assert [i.texto for i in receita.ingredientes] == ["2 ovos", "1 xícara de farinha"]
    # a numeração dos passos sai
    assert receita.modo_de_preparo == ("Bata os ovos.", "Asse.")
    assert receita.fonte.licenca == "Não declarada"
    assert receita.esta_completa


def test_afrodite_junta_subsecoes_de_ingredientes(tmp_path):
    arquivo = tmp_path / "afrodite.json"
    itens = [
        item_afrodite("1", "Torta", [("Massa:", ["farinha"]), ("Recheio:", ["frango"])])
    ]
    arquivo.write_text(json.dumps(itens), encoding="utf-8")
    [receita] = carregar_afrodite(arquivo)
    assert [i.texto for i in receita.ingredientes] == ["farinha", "frango"]
    # sem modo de preparo, sai na curadoria
    assert not receita.esta_completa


def test_afrodite_remove_duplicatas(tmp_path):
    arquivo = tmp_path / "afrodite.json"
    secoes = [("Ingredientes", ["ovo"]), ("Modo de Preparo", ["Frite."])]
    itens = [
        item_afrodite("1", "Omelete", secoes),
        item_afrodite("2", "omelete ", secoes),
    ]
    arquivo.write_text(json.dumps(itens), encoding="utf-8")
    assert [r.documento_id for r in carregar_afrodite(arquivo)] == ["afrodite:1"]


# ---------------------------------------------------------------- RecipeNLG


def gravar_recipenlg(caminho, linhas: list[dict]) -> None:
    colunas = {chave: [linha[chave] for linha in linhas] for chave in linhas[0]}
    pq.write_table(pa.table(colunas), caminho)


def linha_recipenlg(n: int, ner: list[str] | None = None) -> dict:
    ingredientes = ["2 eggs", "1 carrot"]
    return {
        "Unnamed: 0": n,
        "title": f"Recipe {n}",
        "ingredients": json.dumps(ingredientes),
        "directions": json.dumps(["Mix.", "Bake."]),
        "link": f"www.cookbooks.com/{n}",
        "source": "Gathered",
        "NER": json.dumps(ner if ner is not None else ["eggs", "carrot"]),
    }


def test_recipenlg_amostra_e_estavel_e_respeita_a_quantidade(tmp_path):
    arquivo = tmp_path / "recipenlg.parquet"
    gravar_recipenlg(arquivo, [linha_recipenlg(n) for n in range(50)])
    primeira = carregar_recipenlg(arquivo, quantidade=10, semente=7)
    segunda = carregar_recipenlg(arquivo, quantidade=10, semente=7)
    assert len(primeira) == 10
    assert [r.documento_id for r in primeira] == [r.documento_id for r in segunda]


def test_recipenlg_le_receita_link_e_nomes(tmp_path):
    arquivo = tmp_path / "recipenlg.parquet"
    gravar_recipenlg(arquivo, [linha_recipenlg(3)])
    [receita] = carregar_recipenlg(arquivo, quantidade=5)
    assert receita.idioma == "en"
    assert receita.fonte.url == "https://www.cookbooks.com/3"
    assert [(i.texto, i.nome) for i in receita.ingredientes] == [
        ("2 eggs", "eggs"),
        ("1 carrot", "carrot"),
    ]


def test_recipenlg_sem_ner_alinhado_nao_inventa_nomes(tmp_path):
    arquivo = tmp_path / "recipenlg.parquet"
    gravar_recipenlg(arquivo, [linha_recipenlg(1, ner=["eggs"])])
    [receita] = carregar_recipenlg(arquivo, quantidade=1)
    assert all(i.nome is None for i in receita.ingredientes)


# ---------------------------------------------------------------- Guia Alimentar


def paginas_do_guia(conteudo: dict[int, str]) -> list[str]:
    """Páginas do PDF (índice 0 = PDF 1) com o texto nas páginas impressas pedidas."""
    paginas = ["" for _ in range(140)]
    for impressa, texto in conteudo.items():
        paginas[impressa] = texto  # PDF = impressa + 1 → índice = impressa
    return paginas


def test_guia_divide_por_titulo_e_por_paragrafo_e_tira_cabecalhos():
    linhas = [
        "1514",
        "MINISTÉRIO DA SAÚDE",
        "cAPíTULO 1.",
        "PRINcíPIOS",
        "toda ação humana é guiada ",
        "por princípios.",
        "AlimentAção é mAis que ingestão de ",
        "nutrientes",
        "alimentação diz respeito ",
        "à saúde e ao bem-",
        "estar.",
        "segundo parágrafo.",
    ]
    texto = "\n".join(linhas)
    secoes = [s for s in secoes_do_guia(paginas_do_guia({15: texto})) if s.pagina == 15]
    assert [s.titulo for s in secoes] == [
        "Capítulo 1. Princípios",
        "Alimentação é mais que ingestão de nutrientes",
    ]
    assert secoes[0].paragrafos == ("Toda ação humana é guiada por princípios.",)
    assert secoes[1].paragrafos == (
        # palavra composta quebrada no hífen: o hífen fica e não entra espaço
        "Alimentação diz respeito à saúde e ao bem-estar.",
        "Segundo parágrafo.",
    )
    assert secoes[1].capitulo == "Capítulo 1. Princípios"


def test_guia_cada_passo_vira_uma_secao_mesmo_com_espaco_depois_do_ponto():
    linhas = [
        "Fazer de aLimentos IN NATuRA ",
        "a Base da aLimentação",
        "em grande variedade, frango, peixes ",
        "etc. ",
        "UtiLizar óLeos, GordUras ",
        "em PeQUenas QUantidades",
        "Utilizados com moderação.",
        "1",
        "2",
    ]
    texto = "\n".join(linhas)
    secoes = [
        s for s in secoes_do_guia(paginas_do_guia({125: texto})) if s.pagina == 125
    ]
    assert [s.titulo for s in secoes] == [
        "Fazer de alimentos in natura a base da alimentação",
        "Utilizar óleos, gorduras em pequenas quantidades",
    ]
    assert secoes[1].paragrafos == ("Utilizados com moderação.",)


def test_guia_ignora_paginas_fora_dos_capitulos():
    secoes = secoes_do_guia(paginas_do_guia({135: "texto do anexo."}))
    assert secoes == []


# ---------------------------------------------------------------- Markdown


def test_markdown_divide_por_cabecalhos_e_paragrafos():
    fonte = Fonte(titulo="Conservação de alimentos", instituicao="Embrapa", ano=2020)
    texto = (
        "# Conservação de alimentos\n\n"
        "Introdução curta.\n\n"
        "## Folhas\n\nLave e seque as folhas\nantes de guardar.\n\nGuarde na geladeira.\n\n"
        "### Alface\n\nUse um pote com papel toalha.\n"
    )
    documento = documento_de_markdown("embrapa-conservacao", texto, fonte)
    assert documento.titulo == "Conservação de alimentos"
    assert [(s.capitulo, s.titulo, s.paragrafos) for s in documento.secoes] == [
        (None, "Conservação de alimentos", ("Introdução curta.",)),
        (
            "Folhas",
            "Folhas",
            ("Lave e seque as folhas antes de guardar.", "Guarde na geladeira."),
        ),
        ("Folhas", "Alface", ("Use um pote com papel toalha.",)),
    ]


# ---------------------------------------------------------------- outros PDFs


def test_paragrafos_da_pagina_junta_linhas_e_corrige_o_pdf():
    from economia.receitas.infraestrutura.carregadores import paragrafos_da_pagina

    linhas = [
        "CAPÍTULO 3",
        "O consumo de frutas é re -",
        "comendado todos os dias.",
        "Use a geladeira para con/f_irmar",
        "a durabilidade:",
        "30",
        "sem ponto no fim",
    ]
    assert paragrafos_da_pagina("\n".join(linhas)) == [
        "O consumo de frutas é recomendado todos os dias.",
        "Use a geladeira para confirmar a durabilidade:",
        "sem ponto no fim",
    ]


def test_secoes_por_pagina_seguem_o_capitulo_e_a_pagina():
    from economia.receitas.infraestrutura.carregadores import secoes_por_pagina

    paginas = ["capa.", "texto um.", "", "texto três.", "referências."]
    secoes = secoes_por_pagina(
        paginas,
        "Livro",
        capitulos=((2, "Apresentação"), (4, "Capítulo 1")),
        inicio=2,
        fim=5,
    )
    assert [(s.pagina, s.capitulo, s.paragrafos) for s in secoes] == [
        (2, "Apresentação", ("texto um.",)),
        (4, "Capítulo 1", ("texto três.",)),
    ]
    assert secoes[0].titulo == "Apresentação"


def test_catalogo_de_orientacao_tem_fonte_e_licenca():
    from economia.receitas.infraestrutura.carregadores import DOCUMENTOS_DE_ORIENTACAO

    ids = [d.documento_id for d in DOCUMENTOS_DE_ORIENTACAO]
    assert len(ids) == len(set(ids))
    assert all(
        d.fonte.licenca and d.fonte.url and d.fonte.ano
        for d in DOCUMENTOS_DE_ORIENTACAO
    )
