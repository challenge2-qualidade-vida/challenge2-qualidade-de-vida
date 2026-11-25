"""Testes da linha de comando da verificação."""

from economia.compartilhado.configuracao import Configuracao
from economia.verificacao.cli import criar_agentes, criar_parser


class PromptsFalsos:
    def __init__(self):
        self.pedidos = []

    def carregar(self, agente, referencia):
        self.pedidos.append(f"{agente}/{referencia}")
        return f"<{agente}/{referencia}>"


def test_padroes_seguem_a_spec(tmp_path):
    args = criar_parser().parse_args(
        ["avaliar", "--casos", "c.json", "--saida", str(tmp_path / "s.json")]
    )

    assert (args.limite, args.retornos, args.limite_maximo) == (5, 2, 20)
    assert (args.prompt_analise, args.prompt_validacao) == ("analise", "validacao")


def test_agentes_leem_o_prompt_pedido():
    prompts = PromptsFalsos()

    _, validar = criar_agentes(
        Configuracao(limiar_confianca_verificacao=0.8), object(), prompts, "analise@v2"
    )

    assert prompts.pedidos == ["verificacao/analise@v2", "verificacao/validacao"]
    assert validar.limiar == 0.8
