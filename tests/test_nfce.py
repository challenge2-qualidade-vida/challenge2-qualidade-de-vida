import io
import json
from pathlib import Path

import pytest
import qrcode

from economia.dados import carregar
from economia.nfce import ErroNFCe, extrair_chave, ler_qrcode, processar, salvar_contribuicao, validar_url

HTML = (Path(__file__).parent / "fixtures" / "nfce_exemplo.html").read_text(encoding="utf-8")
CHAVE = "53261012345678000190650010000123451876543210"   # fictícia, com dígito verificador válido
URL = f"https://www.fazenda.df.gov.br/nfce/qrcode?p={CHAVE}|2|1|1|ABCDEF"


@pytest.fixture(scope="module")
def base():
    return carregar()


def imagem_qr(texto: str) -> bytes:
    buf = io.BytesIO()
    qrcode.make(texto).save(buf, format="PNG")
    return buf.getvalue()


def test_le_qrcode_de_imagem():
    assert ler_qrcode(imagem_qr(URL)) == URL


def test_imagem_sem_qrcode_da_erro():
    buf = io.BytesIO()
    from PIL import Image
    Image.new("RGB", (200, 200), "white").save(buf, format="PNG")
    with pytest.raises(ErroNFCe, match="Não encontrei um QR code"):
        ler_qrcode(buf.getvalue())


def test_arquivo_que_nao_e_imagem_da_erro():
    with pytest.raises(ErroNFCe, match="abrir a imagem"):
        ler_qrcode(b"isto nao e uma imagem")


@pytest.mark.parametrize("url", [URL, "http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?p=1"])
def test_aceita_dominios_da_sefaz_df(url):
    assert validar_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://exemplo.com/nfce?p=1",
        "https://fazenda.df.gov.br.golpe.com/nfce",
        "http://localhost:8000/api/saude",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
    ],
)
def test_recusa_outros_enderecos(url):
    with pytest.raises(ErroNFCe):
        validar_url(url)


def test_extrai_e_valida_chave_de_acesso():
    assert extrair_chave(URL) == CHAVE
    chave_errada = CHAVE[:-1] + str((int(CHAVE[-1]) + 1) % 10)
    assert extrair_chave(URL.replace(CHAVE, chave_errada)) is None


def test_extrai_dados_da_nota(base):
    nota = processar(base, HTML, URL)
    assert nota.emitente == "SUPERMERCADO EXEMPLO LTDA"
    assert nota.cnpj == "12345678000190"
    assert nota.data == "2026-10-27"
    assert nota.chave == CHAVE
    assert len(nota.itens) == 5
    feijao = nota.itens[1]
    assert (feijao.quantidade, feijao.valor_unitario, feijao.valor_total) == (2, 7.29, 14.58)


def test_nao_le_dados_do_consumidor(base):
    assert "000.000.000-00" not in json.dumps(processar(base, HTML, URL).__dict__, default=str)


def test_associa_itens_aos_produtos_da_base(base):
    itens = {i.descricao: i for i in processar(base, HTML, URL).itens}
    assert (itens["ARROZ TIPO 1 5KG"].produto_id, itens["ARROZ TIPO 1 5KG"].confianca) == ("arroz-5kg", "alta")
    assert itens["FEIJAO CARIOCA 1KG"].produto_id == "feijao-carioca-1kg"
    # Vendido por kg: o preço da embalagem de 1 kg é o valor unitário.
    assert (itens["BANANA PRATA KG"].produto_id, itens["BANANA PRATA KG"].preco_embalagem) == ("banana-1kg", 5.49)
    # Não é alimento da base: fica para o usuário revisar.
    assert itens["SABAO EM PO 1KG"].produto_id is None
    # Alimento conhecido, mas tamanho que a base não tem.
    assert itens["ARROZ TIPO 1 2KG"].produto_id is None and "tamanho" in itens["ARROZ TIPO 1 2KG"].produto


def test_contribuicao_entra_na_base_e_substitui_preco_antigo(tmp_path):
    arquivo = tmp_path / "contribuicoes.json"
    n = salvar_contribuicao("SUPERMERCADO EXEMPLO LTDA", "12345678000190", "2026-10-27",
                            [{"produto_id": "arroz-5kg", "preco": 24.90}, {"produto_id": None, "preco": 12.9}], arquivo)
    assert n == 1
    base = carregar(arq_contribuicoes=arquivo)
    assert "nfce-12345678000190" in base.mercados
    precos = [p for p in base.precos if p.mercado == "nfce-12345678000190"]
    assert [(p.produto, p.preco, p.fonte) for p in precos] == [("arroz-5kg", 24.90, "nfce")]

    salvar_contribuicao("SUPERMERCADO EXEMPLO LTDA", "12345678000190", "2026-10-29", [{"produto_id": "arroz-5kg", "preco": 25.50}], arquivo)
    precos = [p for p in carregar(arq_contribuicoes=arquivo).precos if p.mercado == "nfce-12345678000190"]
    assert [(p.preco, p.data) for p in precos] == [(25.50, "2026-10-29")]
