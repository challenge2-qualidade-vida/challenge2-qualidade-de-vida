"""Carregadores dos documentos-fonte: afrodite.json, RecipeNLG (Parquet), Guia Alimentar e outros PDFs de orientação, e Markdown."""

import json
import random
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from economia.receitas.dominio.modelos import (
    Documento,
    Fonte,
    Ingrediente,
    Receita,
    Secao,
)

URL_AFRODITE = "https://github.com/adrianosferreira/afrodite.json"
URL_GUIA = "https://bvsms.saude.gov.br/bvs/publicacoes/guia_alimentar_populacao_brasileira_2ed.pdf"
LICENCA_RECIPENLG = "Uso não comercial em pesquisa e ensino (termos do RecipeNLG)"

FONTE_DO_AFRODITE = Fonte(
    titulo="afrodite.json",
    instituicao="afrodite.json (dataset no GitHub)",
    url=URL_AFRODITE,
    licenca="Não declarada",
)
FONTE_DO_GUIA = Fonte(
    titulo="Guia Alimentar para a População Brasileira, 2ª edição",
    instituicao="Ministério da Saúde",
    ano=2014,
    url=URL_GUIA,
    licenca="Reprodução parcial ou total permitida, desde que citada a fonte (a confirmar)",
)
# Cada receita do RecipeNLG cita o próprio link; no catálogo, vale a página do dataset.
FONTE_DO_RECIPENLG = Fonte(
    titulo="RecipeNLG",
    instituicao="Poznań University of Technology",
    ano=2020,
    url="https://recipenlg.cs.put.poznan.pl/",
    licenca=LICENCA_RECIPENLG,
)

# ---------------------------------------------------------------- receitas


def _chave_de_duplicata(titulo: str, ingredientes: Iterable[str]) -> tuple[str, ...]:
    def normalizar(texto: str) -> str:
        sem_acento = (
            unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
        )
        return " ".join(sem_acento.lower().split())

    return (normalizar(titulo), *sorted(normalizar(i) for i in ingredientes))


_NUMERACAO_DO_PASSO = re.compile(r"^\s*\d+\s*[-–.)]\s*")


def _receita_do_afrodite(item: dict) -> Receita:
    ingredientes: list[str] = []
    preparo: list[str] = []
    for secao in item.get("secao", []):
        nome = secao.get("nome", "").strip().lower()
        linhas = [c.strip() for c in secao.get("conteudo", []) if c and c.strip()]
        if nome == "modo de preparo":
            preparo += [_NUMERACAO_DO_PASSO.sub("", linha) for linha in linhas]
        elif nome == "outras informações":
            continue
        else:
            # "Ingredientes" e subseções como "Massa:" e "Recheio:" viram uma lista só
            ingredientes += linhas
    # linhas como "Massa:" ou "Para a calda:" são títulos de subseção, não ingredientes
    ingredientes = [i for i in ingredientes if not i.rstrip().endswith(":")]
    return Receita(
        documento_id=f"afrodite:{item['_id']['$oid']}",
        titulo=item["nome"].strip(),
        ingredientes=tuple(Ingrediente(i) for i in ingredientes),
        modo_de_preparo=tuple(preparo),
        fonte=FONTE_DO_AFRODITE,
        idioma="pt",
    )


def _sem_duplicatas(receitas: Iterable[Receita]) -> list[Receita]:
    vistas: set[tuple[str, ...]] = set()
    unicas = []
    for receita in receitas:
        chave = _chave_de_duplicata(
            receita.titulo, (i.texto for i in receita.ingredientes)
        )
        if chave not in vistas:
            vistas.add(chave)
            unicas.append(receita)
    return unicas


def carregar_afrodite(caminho: Path) -> list[Receita]:
    """Todas as receitas do afrodite.json, sem duplicatas. A curadoria das incompletas vem depois."""
    with Path(caminho).open(encoding="utf-8") as arquivo:
        itens = json.load(arquivo)
    return _sem_duplicatas(_receita_do_afrodite(item) for item in itens)


def _receita_do_recipenlg(linha: dict) -> Receita:
    ingredientes = json.loads(linha["ingredients"])
    nomes = json.loads(linha["NER"])
    # o NER só corresponde linha a linha quando as listas têm o mesmo tamanho
    alinhados = len(nomes) == len(ingredientes)
    link = linha["link"]
    return Receita(
        documento_id=f"recipenlg:{linha['Unnamed: 0']}",
        titulo=linha["title"].strip(),
        ingredientes=tuple(
            Ingrediente(texto, nome=nomes[n] if alinhados else None)
            for n, texto in enumerate(ingredientes)
            if texto.strip()
        ),
        modo_de_preparo=tuple(json.loads(linha["directions"])),
        fonte=Fonte(
            titulo="RecipeNLG",
            instituicao="Poznań University of Technology",
            ano=2020,
            url=link if link.startswith("http") else f"https://{link}",
            licenca=LICENCA_RECIPENLG,
        ),
        idioma="en",
    )


def carregar_recipenlg(
    caminho: Path, quantidade: int = 3000, semente: int = 42
) -> list[Receita]:
    """Amostra aleatória do RecipeNLG, sempre a mesma para a mesma semente."""
    import pyarrow.parquet as pq

    tabela = pq.read_table(
        caminho,
        columns=["Unnamed: 0", "title", "ingredients", "directions", "link", "NER"],
    )
    indices = sorted(
        random.Random(semente).sample(
            range(tabela.num_rows), min(quantidade, tabela.num_rows)
        )
    )
    linhas = tabela.take(indices).to_pylist()
    return _sem_duplicatas(_receita_do_recipenlg(linha) for linha in linhas)


# ---------------------------------------------------------------- Guia Alimentar

# Capítulos do sumário do Guia (2ª edição), com a página impressa de início.
# "Para saber mais" (p. 131) e o Anexo A (p. 145) ficam fora da base.
CAPITULOS_DO_GUIA = (
    (5, "Apresentação"),
    (7, "Preâmbulo"),
    (11, "Introdução"),
    (15, "Capítulo 1. Princípios"),
    (25, "Capítulo 2. A escolha dos alimentos"),
    (53, "Capítulo 3. Dos alimentos à refeição"),
    (91, "Capítulo 4. O ato de comer e a comensalidade"),
    (103, "Capítulo 5. A compreensão e a superação de obstáculos"),
    (125, "Dez passos para uma alimentação adequada e saudável"),
)
FIM_DO_GUIA = 131
# A página do PDF é a página impressa mais 1 (a capa não tem número).
DESLOCAMENTO_DE_PAGINA = 1

_CABECALHOS = {"MINISTÉRIO DA SAÚDE", "GUIA ALIMENTAR PARA A POPULAÇÃO BRASILEIRA"}
# Os títulos do Guia são em versalete. Extraídos do PDF, ficam com maiúscula no meio da palavra
# ("AlimentAção é mAis") ou em caixa alta.
_MAIUSCULA_NO_MEIO = re.compile(r"[a-zà-ÿ][A-ZÀ-Ý]")
_FIM_DE_FRASE = set(".!?")


def _e_titulo(linha: str) -> bool:
    texto = linha.strip()
    letras = [c for c in texto if c.isalpha()]
    if len(letras) < 3:
        return False
    return bool(_MAIUSCULA_NO_MEIO.search(texto)) or all(c.isupper() for c in letras)


def _e_ruido(linha: str) -> bool:
    texto = linha.strip()
    return not texto or texto.isdigit() or texto in _CABECALHOS


def _arrumar_titulo(partes: list[str]) -> str:
    titulo = " ".join(" ".join(p.split()) for p in partes).lower()
    return titulo[:1].upper() + titulo[1:]


def _juntar_linhas(linhas: list[str]) -> str:
    texto = ""
    for linha in linhas:
        limpa = linha.strip()
        if texto.endswith("-"):
            texto += limpa  # palavra hifenizada na quebra de linha
        else:
            texto = f"{texto} {limpa}" if texto else limpa
    return texto[:1].upper() + texto[1:]


def _secoes_das_linhas(linhas: list[tuple[str, int]], capitulo: str) -> list[Secao]:
    """Divide as linhas de um capítulo em seções (pelos títulos) e parágrafos.

    Uma linha que termina sem espaço e com pontuação fecha o parágrafo: no PDF, as linhas
    que continuam o parágrafo terminam com espaço.
    """
    secoes: list[Secao] = []
    titulo, pagina = capitulo, linhas[0][1] if linhas else None
    paragrafos: list[str] = []
    atual: list[str] = []

    def fechar_secao() -> None:
        if atual:
            paragrafos.append(_juntar_linhas(atual))
            atual.clear()
        if paragrafos:
            secoes.append(
                Secao(
                    titulo=titulo,
                    paragrafos=tuple(paragrafos),
                    capitulo=capitulo,
                    pagina=pagina,
                )
            )

    n = 0
    while n < len(linhas):
        linha, pagina_da_linha = linhas[n]
        if linha.strip().casefold().startswith("capítulo"):
            n += 1
            continue
        # um título só começa fora de um parágrafo ou logo depois do fim de uma frase
        # (no fim de um bloco, o PDF às vezes deixa espaço depois do ponto final)
        if _e_titulo(linha) and (not atual or atual[-1].rstrip()[-1:] in _FIM_DE_FRASE):
            fechar_secao()
            partes = [linha]
            # o título continua enquanto a linha termina com espaço e a seguinte também é título,
            # ou é um fim curto, sem ponto final ("... ingestão de" + "nutrientes")
            while partes[-1].endswith(" ") and n + 1 < len(linhas):
                seguinte = linhas[n + 1][0]
                fim_curto = (
                    len(seguinte.split()) <= 6
                    and not seguinte.endswith(" ")
                    and seguinte.rstrip()[-1:] not in _FIM_DE_FRASE
                )
                if _e_titulo(seguinte) or fim_curto:
                    partes.append(seguinte)
                    n += 1
                else:
                    break
            titulo_novo = _arrumar_titulo(partes)
            # o título do capítulo ("Princípios") já está em `capitulo`
            titulo = (
                capitulo
                if titulo_novo.casefold() in capitulo.casefold()
                else titulo_novo
            )
            pagina, paragrafos = pagina_da_linha, []
            n += 1
            continue
        atual.append(linha)
        if not linha.endswith(" ") and linha.rstrip()[-1:] in '.!?:”")':
            paragrafos.append(_juntar_linhas(atual))
            atual.clear()
        n += 1
    fechar_secao()
    return secoes


def secoes_do_guia(paginas: list[str]) -> list[Secao]:
    """Monta as seções do Guia a partir do texto de cada página do PDF (índice 0 = página 1 do PDF)."""
    secoes: list[Secao] = []
    limites = [*(inicio for inicio, _ in CAPITULOS_DO_GUIA[1:]), FIM_DO_GUIA]
    for (inicio, capitulo), fim in zip(CAPITULOS_DO_GUIA, limites, strict=True):
        linhas: list[tuple[str, int]] = []
        for impressa in range(inicio, fim):
            indice = impressa + DESLOCAMENTO_DE_PAGINA - 1
            if indice >= len(paginas):
                break
            linhas += [
                (linha, impressa)
                for linha in paginas[indice].splitlines()
                if not _e_ruido(linha)
            ]
        secoes += _secoes_das_linhas(linhas, capitulo)
    return secoes


def carregar_guia_alimentar(caminho: Path) -> Documento:
    """Guia Alimentar para a População Brasileira (2ª edição, 2014), dividido por capítulo e seção."""
    import logging

    from pypdf import PdfReader

    # o pypdf avisa sobre fontes Type1 sem o fontTools, sem afetar o texto
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    paginas = [pagina.extract_text() or "" for pagina in PdfReader(caminho).pages]
    return Documento(
        documento_id="guia-alimentar",
        titulo="Guia Alimentar para a População Brasileira",
        secoes=tuple(secoes_do_guia(paginas)),
        fonte=FONTE_DO_GUIA,
    )


# ---------------------------------------------------------------- Markdown


def documento_de_markdown(
    documento_id: str, texto: str, fonte: Fonte, idioma: str = "pt"
) -> Documento:
    """Texto de orientação em Markdown: `#` e `##` abrem seções; parágrafos separados por linha em branco."""
    titulo_do_documento = fonte.titulo
    secoes: list[Secao] = []
    titulo, capitulo = titulo_do_documento, None
    paragrafos: list[str] = []
    atual: list[str] = []

    def fechar_paragrafo() -> None:
        if atual:
            paragrafos.append(" ".join(atual))
            atual.clear()

    def fechar_secao() -> None:
        fechar_paragrafo()
        if paragrafos:
            secoes.append(
                Secao(titulo=titulo, paragrafos=tuple(paragrafos), capitulo=capitulo)
            )

    for linha in texto.splitlines():
        cabecalho = re.match(r"^(#{1,3})\s+(.+)$", linha)
        if cabecalho:
            fechar_secao()
            paragrafos = []
            nivel, nome = len(cabecalho.group(1)), cabecalho.group(2).strip()
            if nivel == 1:
                titulo_do_documento = titulo = nome
                capitulo = None
            elif nivel == 2:
                capitulo = titulo = nome
            else:
                titulo = nome
        elif linha.strip():
            atual.append(linha.strip())
        else:
            fechar_paragrafo()
    fechar_secao()
    return Documento(
        documento_id=documento_id,
        titulo=titulo_do_documento,
        secoes=tuple(secoes),
        fonte=fonte,
        idioma=idioma,
    )


# ---------------------------------------------------------------- outros PDFs de orientação

_LIGADURAS = {"/f_i": "fi", "/f_l": "fl", "/f_f": "ff", "/f_t": "ft"}
_CABECALHO_DE_CAPITULO = re.compile(r"^cap[ií]tulo\s+\d+\s*$", re.IGNORECASE)


def _limpar_linha(linha: str) -> str:
    for errado, certo in _LIGADURAS.items():
        linha = linha.replace(errado, certo)
    return linha.strip()


def paragrafos_da_pagina(texto: str) -> list[str]:
    """Parágrafos de uma página de folheto ou livro diagramado.

    Uma linha que termina com pontuação fecha o parágrafo. Linhas só com número (página)
    e cabeçalhos "Capítulo N" saem. A hifenização "re -" ou "re-" no fim da linha é juntada.
    """
    paragrafos: list[str] = []
    atual = ""
    for bruta in texto.splitlines():
        linha = _limpar_linha(bruta)
        if not linha or linha.isdigit() or _CABECALHO_DE_CAPITULO.match(linha):
            continue
        if re.search(r"\w ?-$", atual):
            atual = re.sub(r" ?-$", "", atual) + linha
        else:
            atual = f"{atual} {linha}" if atual else linha
        if atual[-1:] in ".!?:":
            paragrafos.append(" ".join(atual.split()))
            atual = ""
    if atual:
        paragrafos.append(" ".join(atual.split()))
    return paragrafos


def secoes_por_pagina(
    paginas: list[str],
    titulo: str,
    capitulos: tuple[tuple[int, str], ...] = (),
    inicio: int = 1,
    fim: int | None = None,
) -> list[Secao]:
    """Uma seção por página (índice 0 = página 1), com o capítulo vigente.

    A página da citação é exata. Páginas sem texto ficam de fora.
    """
    secoes = []
    ultima = fim if fim is not None else len(paginas) + 1
    for numero in range(inicio, min(ultima, len(paginas) + 1)):
        capitulo = None
        for comeco, nome in capitulos:
            if numero >= comeco:
                capitulo = nome
        paragrafos = paragrafos_da_pagina(paginas[numero - 1])
        if paragrafos:
            secoes.append(
                Secao(
                    titulo=capitulo or titulo,
                    paragrafos=tuple(paragrafos),
                    capitulo=capitulo,
                    pagina=numero,
                )
            )
    return secoes


def _paginas_do_pdf(caminho: Path) -> list[str]:
    import logging

    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    leitor = PdfReader(caminho, strict=False)
    paginas = []
    for pagina in leitor.pages:
        try:
            paginas.append(pagina.extract_text() or "")
        except (PyPdfError, KeyError, ValueError):  # página corrompida: segue sem ela
            paginas.append("")
    return paginas


@dataclass(frozen=True)
class DocumentoDeOrientacao:
    """Como carregar um PDF de orientação: arquivo, fonte, capítulos e páginas que entram."""

    documento_id: str
    arquivo: str
    titulo: str
    fonte: Fonte
    capitulos: tuple[tuple[int, str], ...] = ()
    inicio: int = 1
    fim: int | None = None


LICENCA_EMBRAPA = "CC BY-NC-ND 4.0 (Infoteca-e, Embrapa)"
LICENCA_CC_BY = "CC BY 4.0"
LICENCA_MS = (
    "CC BY-NC-SA 4.0. Reprodução parcial ou total permitida, desde que citada a fonte"
)

DOCUMENTOS_DE_ORIENTACAO = (
    DocumentoDeOrientacao(
        documento_id="ms-na-cozinha-flv",
        arquivo="na_cozinha_com_as_frutas_legumes_e_verduras.pdf",
        titulo="Na cozinha com as frutas, legumes e verduras",
        fonte=Fonte(
            titulo="Na cozinha com as frutas, legumes e verduras",
            instituicao="Ministério da Saúde e Universidade Federal de Minas Gerais",
            ano=2016,
            url="https://repositorio.ufmg.br/handle/1843/65672",
            licenca=LICENCA_MS,
        ),
        capitulos=(
            (4, "Apresentação"),
            (6, "Introdução"),
            (8, "Capítulo 1. As frutas, legumes e verduras"),
            (26, "Capítulo 2. Pré-preparando as frutas, legumes e verduras"),
            (30, "Capítulo 3. Preparando as frutas, legumes e verduras"),
            (42, "Capítulo 4. Na cozinha com as frutas, legumes e verduras"),
        ),
        inicio=4,
        fim=112,  # as referências começam na página 112
    ),
    DocumentoDeOrientacao(
        documento_id="embrapa-geladeira",
        arquivo="embrapa_hortalica_nao_e_so_salada_geladeira_2020.pdf",
        titulo="Hortaliça não é só salada: Geladeira",
        fonte=Fonte(
            titulo="Hortaliça não é só salada: Geladeira (2ª ed. rev.)",
            instituicao="Embrapa Hortaliças",
            ano=2020,
            url="https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1129028",
            licenca=LICENCA_EMBRAPA,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="embrapa-congelador",
        arquivo="embrapa_hortalica_nao_e_so_salada_congelador_2020.pdf",
        titulo="Hortaliça não é só salada: Congelador",
        fonte=Fonte(
            titulo="Hortaliça não é só salada: Congelador (2ª ed. rev.)",
            instituicao="Embrapa Hortaliças",
            ano=2020,
            url="https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1129067",
            licenca=LICENCA_EMBRAPA,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="embrapa-recomendacoes-compras",
        arquivo="embrapa_recomendacoes_compras_armazenamento_consumo_2020.pdf",
        titulo="Recomendações para compras, armazenamento e consumo de frutas e hortaliças",
        fonte=Fonte(
            titulo="Recomendações para compras, armazenamento e consumo de frutas e hortaliças",
            instituicao="Embrapa Instrumentação e Ceagesp",
            ano=2020,
            url="https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1122781",
            licenca=LICENCA_EMBRAPA,
        ),
    ),
    # Base ampliada para 20 fontes (#16): documentos do catálogo da equipe, escolhidos pelo
    # impacto nas perguntas do Miau-ricio (critérios em docs/semana-2/avaliacao-rag.md).
    DocumentoDeOrientacao(
        documento_id="ms-guia-criancas-2019",
        arquivo="ms_guia_alimentar_criancas_menores_2_anos_2019.pdf",
        titulo="Guia Alimentar para Crianças Brasileiras Menores de 2 Anos",
        fonte=Fonte(
            titulo="Guia Alimentar para Crianças Brasileiras Menores de 2 Anos",
            instituicao="Ministério da Saúde",
            ano=2019,
            url="http://189.28.128.100/dab/docs/portaldab/publicacoes/guia_da_crianca_2019.pdf",
            licenca=LICENCA_MS,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="ms-protocolo-guia-adultos-2021",
        arquivo="ms_protocolo_guia_alimentar_adultos_fasciculo1_2021.pdf",
        titulo="Protocolos de uso do Guia Alimentar: população adulta",
        fonte=Fonte(
            titulo="Protocolos de Uso do Guia Alimentar para a População Brasileira na Orientação Alimentar, Fascículo 1",
            instituicao="Ministério da Saúde e Universidade de São Paulo",
            ano=2021,
            url="https://bvsms.saude.gov.br/bvs/publicacoes/protocolos_guia_alimentar_fasciculo1.pdf",
            licenca=LICENCA_MS,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="opas-laboratorio-flv-2022",
        arquivo="opas_laboratorio_inovacao_flv_2022.pdf",
        titulo="Laboratório de Inovação: frutas, legumes e verduras",
        fonte=Fonte(
            titulo="Laboratório de Inovação: Incentivo à Produção, à Disponibilidade, ao Acesso e ao Consumo de Frutas, Legumes e Verduras",
            instituicao="OPAS, Ministério da Saúde, INCA, FAO e WFP",
            ano=2022,
            url="https://ninho.inca.gov.br/jspui/bitstream/123456789/13758/1/9789275725146_por.pdf",
            licenca="CC BY-NC-SA 3.0 IGO",
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="bjft-percepcao-riscos-2013",
        arquivo="bjft_percepcao_consumidor_riscos_rastreabilidade_2013.pdf",
        titulo="Percepção do consumidor sobre riscos, segurança e rastreabilidade dos alimentos",
        fonte=Fonte(
            titulo="Percepção do consumidor frente aos riscos associados aos alimentos, sua segurança e rastreabilidade",
            instituicao="Brazilian Journal of Food Technology (ITAL)",
            ano=2013,
            url="https://www.scielo.br/j/bjft/a/G6NXXPM79sRRX78HKm6xb8t/",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="raca-ultraprocessados-2022",
        arquivo="raca_ultraprocessados_riscos_2022.pdf",
        titulo="Alimentos ultraprocessados e seus riscos",
        fonte=Fonte(
            titulo="Alimentos ultraprocessados e seus riscos à cultura alimentar e à saúde",
            instituicao="Revista de Alimentação e Cultura das Américas (RACA), Fiocruz",
            ano=2022,
            url="https://raca.fiocruz.br/index.php/raca/article/view/145",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="raca-consumo-pandemia-2024",
        arquivo="raca_consumo_alimentar_pandemia_2024.pdf",
        titulo="O que envolve o consumo alimentar e a pandemia",
        fonte=Fonte(
            titulo="O que envolve o consumo alimentar e como a pandemia por Covid-19 pode ter influenciado",
            instituicao="Revista de Alimentação e Cultura das Américas (RACA), Fiocruz",
            ano=2024,
            url="https://raca.fiocruz.br/index.php/raca/article/view/182",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="raca-comensalidade-pandemia-2024",
        arquivo="raca_comensalidade_pandemia_2024.pdf",
        titulo="Impactos da pandemia na alimentação e na comensalidade",
        fonte=Fonte(
            titulo="Impactos da pandemia de Covid-19 na alimentação e comensalidade",
            instituicao="Revista de Alimentação e Cultura das Américas (RACA), Fiocruz",
            ano=2024,
            url="https://raca.fiocruz.br/index.php/raca/article/view/192",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="raca-ambiente-escolar-2023",
        arquivo="raca_ambiente_escolar_praticas_alimentares_2023.pdf",
        titulo="Ambiente escolar e práticas alimentares familiares e escolares",
        fonte=Fonte(
            titulo="Ambiente escolar e práticas alimentares familiares e escolares",
            instituicao="Revista de Alimentação e Cultura das Américas (RACA), Fiocruz",
            ano=2023,
            url="https://raca.fiocruz.br/index.php/raca/article/view/154",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="ifc-food-safety-handbook-2020",
        arquivo="ifc_food_safety_handbook_2020.pdf",
        titulo="Food Safety Handbook",
        fonte=Fonte(
            titulo="Food Safety Handbook: A Practical Guide for Building a Robust Food Safety Management System",
            instituicao="International Finance Corporation (IFC), Grupo Banco Mundial",
            ano=2020,
            url="https://www.ifc.org/content/dam/ifc/doc/2020/food-safety-handbook-2020-edition-ifc-2023.pdf",
            licenca="CC BY 3.0 IGO",
        ),
        # só o capítulo 3 (perigos, APPCC e temperaturas); os outros tratam de normas,
        # regulamentação e gestão de empresas, e geravam mais de mil trechos de ruído
        inicio=72,
        fim=226,
    ),
    DocumentoDeOrientacao(
        documento_id="bjft-higiene-servicos-2012",
        arquivo="bjft_diagnostico_higiene_servicos_alimentacao_2012.pdf",
        titulo="Diagnóstico das condições higiênicas de serviços de alimentação",
        fonte=Fonte(
            titulo="Diagnóstico das condições higiênicas de serviços de alimentação de acordo com a NBR 15635:2008",
            instituicao="Brazilian Journal of Food Technology (ITAL)",
            ano=2012,
            url="https://www.scielo.br/j/bjft/a/db7TDPqpcFvZdcWFH3YTwJG/",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="raca-praticas-higiene-2019",
        arquivo="raca_praticas_higiene_servicos_alimentacao_2019.pdf",
        titulo="Práticas de higiene em serviços de alimentação",
        fonte=Fonte(
            titulo="Redefinindo para melhor refletir: práticas de higiene em serviços de alimentação",
            instituicao="Revista de Alimentação e Cultura das Américas (RACA), Fiocruz",
            ano=2019,
            url="https://raca.fiocruz.br/index.php/raca/article/view/5",
            licenca=LICENCA_CC_BY,
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="taco-2011",
        arquivo="taco_4_edicao_2011.pdf",
        titulo="Tabela Brasileira de Composição de Alimentos (TACO)",
        fonte=Fonte(
            titulo="Tabela Brasileira de Composição de Alimentos (TACO), 4ª edição revisada e ampliada",
            instituicao="NEPA, Universidade Estadual de Campinas (Unicamp)",
            ano=2011,
            url="https://nepa.unicamp.br/wp-content/uploads/sites/27/2023/10/taco_4_edicao_ampliada_e_revisada.pdf",
            licenca="Reprodução total ou parcial permitida, desde que citada a fonte",
        ),
    ),
    DocumentoDeOrientacao(
        documento_id="cadsc-campanha-desperdicio-2022",
        arquivo="cadsc_campanha_reducao_desperdicio_2022.pdf",
        titulo="Campanha para redução do desperdício em uma unidade de alimentação e nutrição",
        fonte=Fonte(
            titulo="Efetividade de uma campanha para redução de desperdício em uma unidade de alimentação e nutrição",
            instituicao="Cadernos Saúde Coletiva (UFRJ)",
            ano=2022,
            url="https://www.scielo.br/j/cadsc/a/yGYP7nfb9NKybvFDqfxdsJS/",
            licenca=LICENCA_CC_BY,
        ),
    ),
)


def carregar_documento_de_orientacao(
    pasta: Path, especificacao: DocumentoDeOrientacao
) -> Documento:
    """Carrega um PDF de orientação do catálogo, com uma seção por página."""
    paginas = _paginas_do_pdf(Path(pasta) / especificacao.arquivo)
    return Documento(
        documento_id=especificacao.documento_id,
        titulo=especificacao.titulo,
        secoes=tuple(
            secoes_por_pagina(
                paginas,
                especificacao.titulo,
                especificacao.capitulos,
                especificacao.inicio,
                especificacao.fim,
            )
        ),
        fonte=especificacao.fonte,
    )


def catalogo_de_fontes() -> dict[str, Fonte]:
    """Os documentos-fonte da base de conhecimento, pelo id, para conferir o catálogo (#16)."""
    return {
        "guia-alimentar": FONTE_DO_GUIA,
        "afrodite": FONTE_DO_AFRODITE,
        "recipenlg": FONTE_DO_RECIPENLG,
        **{d.documento_id: d.fonte for d in DOCUMENTOS_DE_ORIENTACAO},
    }
