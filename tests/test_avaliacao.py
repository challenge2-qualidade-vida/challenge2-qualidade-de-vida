from economia.avaliacao import avaliar, carregar_perguntas, cita_fonte, contem_gabarito, recusou


def test_perguntas_do_experimento_sao_validas():
    perguntas = carregar_perguntas()
    assert len({p["id"] for p in perguntas}) == len(perguntas)
    for p in perguntas:
        assert p.get("deve_recusar") or p["deve_conter"], p["id"]


def test_contem_gabarito_exige_um_termo_de_cada_grupo():
    grupos = [["in natura", "minimamente processad"], ["ultraprocessad"]]
    assert contem_gabarito("Prefira alimentos in natura a ultraprocessados.", grupos)
    assert not contem_gabarito("Prefira alimentos in natura.", grupos)


def test_recusou():
    assert recusou("A base da EconoMIA não tem essa informação.")
    assert recusou("Só consigo ajudar com compras, preços e alimentação.")
    assert not recusou("A acerola tem 941 mg de vitamina C.")


def test_cita_fonte_exige_marcador_e_fontes():
    assert cita_fonte("Prefira in natura [1].", [{"fonte": "Guia"}])
    assert not cita_fonte("Prefira in natura.", [{"fonte": "Guia"}])
    assert not cita_fonte("Prefira in natura [1].", [])


def test_avaliar_pergunta_de_recusa():
    p = {"id": "x", "categoria": "fora_do_tema", "deve_recusar": True}
    assert avaliar(p, "Só consigo ajudar com compras.", [], []) == {"correcao": 1, "fundamentacao": None, "incerteza": 1, "ferramenta": None}


def test_avaliar_pergunta_de_ferramenta():
    p = {"id": "f", "categoria": "ferramenta", "deve_conter": [["7,99"]], "ferramenta": "consultar_precos"}
    assert avaliar(p, "Custa R$ 7,99.", ["consultar_precos"], [])["ferramenta"] == 1
    assert avaliar(p, "Custa R$ 7,99.", [], [])["ferramenta"] == 0
