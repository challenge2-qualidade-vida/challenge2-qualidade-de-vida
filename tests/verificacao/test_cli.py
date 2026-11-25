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

    assert (args.limite, args.retornos, args.limite_maximo) == (5, 2, 10)
    assert (args.prompt_analise, args.prompt_validacao) == ("analise", "validacao")


def test_agentes_leem_o_prompt_pedido():
    prompts = PromptsFalsos()

    _, validar = criar_agentes(
        Configuracao(limiar_confianca_verificacao=0.8), object(), prompts, "analise@v2"
    )

    assert prompts.pedidos == ["verificacao/analise@v2", "verificacao/validacao"]
    assert validar.limiar == 0.8


def test_communication_le_o_prompt_de_comunicacao():
    from economia.verificacao.cli import criar_comunicar

    prompts = PromptsFalsos()

    criar_comunicar(object(), prompts)

    assert prompts.pedidos == ["verificacao/comunicacao"]


def test_orquestrador_da_api_usa_o_grafo_e_os_quatro_prompts(monkeypatch):
    from economia.compartilhado.infraestrutura import prompts_langfuse
    from economia.verificacao import cli
    from economia.verificacao.infraestrutura.grafo_langgraph import GrafoLangGraph

    prompts = PromptsFalsos()
    prompts.prompts_lidos = {}
    monkeypatch.setattr(prompts_langfuse, "PromptsDoLangfuse", lambda cliente: prompts)
    monkeypatch.setattr(cli, "criar_pesquisar", lambda configuracao: "pesquisar")

    orquestrador = cli.criar_verificar_alegacao(Configuracao(_env_file=None))

    assert prompts.pedidos == [
        "verificacao/analise",
        "verificacao/validacao",
        "verificacao/comunicacao",
    ]
    assert isinstance(orquestrador._motor, GrafoLangGraph)
    assert orquestrador.parametros.limite_maximo == 10


def test_busca_do_fluxo_vai_sem_o_limiar_de_similaridade(monkeypatch):
    """Regra 6 da spec 82: quem decide se a evidência basta é o Validation, não a busca."""
    from economia.compartilhado.infraestrutura import embeddings_e5
    from economia.pesquisa_evidencias.dominio import modelos as research
    from economia.pesquisa_evidencias.infraestrutura import (
        pesquisador_qdrant,
        repositorio_qdrant,
    )
    from economia.verificacao import cli

    documento = research.DocumentoEvidencia(
        id="guia",
        fonte=research.FonteEvidencia(titulo="Guia", instituicao="Ministério da Saúde"),
        arquivo="guia.pdf",
        hash_sha256="abc",
    )
    fraca = research.EvidenciaRecuperada(
        trecho=research.TrechoEvidencia(
            id="guia-0001", documento_id="guia", texto="Trecho."
        ),
        documento=documento,
        score=0.5,
    )

    class PesquisadorFalso:
        def __init__(self, gerador, repositorio):
            pass

        def pesquisar(self, pergunta, limite):
            return [fraca]

    monkeypatch.setattr(embeddings_e5, "GeradorE5", lambda dispositivo: None)
    monkeypatch.setattr(
        repositorio_qdrant.RepositorioQdrant,
        "conectar",
        classmethod(lambda cls, url, colecao: None),
    )
    monkeypatch.setattr(pesquisador_qdrant, "PesquisadorQdrant", PesquisadorFalso)

    configuracao = Configuracao(_env_file=None)
    assert fraca.score < configuracao.limiar_similaridade

    evidencias = cli.criar_pesquisar(configuracao)("Ovo faz mal?", 5)

    assert [e.trecho.id for e in evidencias] == ["guia-0001"]
    assert evidencias[0].score == 0.5

