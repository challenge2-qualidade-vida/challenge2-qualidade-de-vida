"""Passos dos cenários da observabilidade (specs/29-observabilidade-langfuse/cenarios.feature).

Usa o SDK real do Langfuse com um exportador de spans em memória: o mascaramento, a pessoa,
a sessão e o vínculo com o prompt são conferidos como o Langfuse os receberia, sem rede.
Os scores, que o SDK envia por outra fila, são guardados numa lista.
"""

import json
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pytest_bdd import given, parsers, scenarios, then, when

from economia.api.app import app, obter_caso_de_uso, obter_observador
from economia.api.observabilidade import NOME_DO_REGISTRO, ObservadorDePerguntas
from economia.compartilhado import mascaramento
from economia.compartilhado.configuracao import Configuracao
from economia.compartilhado.infraestrutura.llm_ollama import ModeloOllama
from economia.compartilhado.infraestrutura.observabilidade_langfuse import (
    RegistroDeGeracoes,
    criar_cliente,
)
from economia.compartilhado.infraestrutura.prompts_langfuse import (
    PRODUCAO,
    PromptsDoLangfuse,
    sincronizar_prompts,
)
from economia.receitas.aplicacao.indexar_base import indexar, montar_trechos
from economia.receitas.aplicacao.responder_pergunta import ResponderPergunta
from economia.receitas.dominio.modelos import Documento, Fonte, Secao
from economia.receitas.infraestrutura.experimento_langfuse import (
    RepositorioObservado,
)

scenarios("29-observabilidade-langfuse/cenarios.feature")

PESSOA = "3f2b8c1e-9a4d-4e6f-8b2a-1c3d5e7f9a0b"
CONVERSA = "7a1c2d3e-4f5a-4b6c-9d7e-8f9a0b1c2d3e"
PERGUNTA_PADRAO = "como conservo alface?"


# --- dublês -------------------------------------------------------------------


class OllamaFalso:
    """Cliente do Ollama que cita o primeiro trecho, com tokens, ou que está fora do ar."""

    def __init__(self):
        self.fora_do_ar = False

    def chat(self, **_):
        if self.fora_do_ar:
            raise ConnectionError("Ollama fora do ar")
        return {
            "message": {"content": "Guarde as folhas secas num pote fechado [1]."},
            "prompt_eval_count": 120,
            "eval_count": 15,
        }


class LangfuseQueFalha:
    def start_as_current_observation(self, **_):
        raise ConnectionError("Langfuse fora do ar")


@dataclass
class PromptFalso:
    name: str
    prompt: str
    version: int
    labels: list[str] = field(default_factory=list)
    is_fallback: bool = False


class LangfuseDePrompts:
    """Prompt management em memória: versões numeradas, cada rótulo numa versão só."""

    def __init__(self):
        self.versoes: dict[str, list[PromptFalso]] = {}
        self.criados = 0
        self.fora_do_ar = False

    def create_prompt(self, *, name, prompt, labels, **_):
        versoes = self.versoes.setdefault(name, [])
        for antigo in versoes:
            antigo.labels = [r for r in antigo.labels if r not in labels]
        novo = PromptFalso(name, prompt, len(versoes) + 1, list(labels))
        versoes.append(novo)
        self.criados += 1
        return novo

    def update_prompt(self, *, name, version, new_labels):
        for p in self.versoes[name]:
            if p.version == version:
                p.labels = sorted(set(p.labels) | set(new_labels))

    def get_prompt(self, name, *, label, fallback=None, **_):
        if self.fora_do_ar:
            return PromptFalso(name, fallback, 0, is_fallback=True)
        for p in reversed(self.versoes.get(name, [])):
            if label in p.labels:
                return p
        raise LookupError(label)


# --- fixtures -------------------------------------------------------------------


@pytest.fixture(scope="module")
def exportador():
    return InMemorySpanExporter()


@pytest.fixture(scope="module")
def langfuse(exportador):
    """Cliente real do Langfuse, com o mascaramento da RN30, exportando para a memória."""
    configuracao = Configuracao(
        _env_file=None,
        langfuse_public_key="pk-lf-bdd-observabilidade",
        langfuse_secret_key="sk-lf-bdd-observabilidade",
        langfuse_base_url="http://127.0.0.1:9",
    )
    return criar_cliente(configuracao, span_exporter=exportador)


@pytest.fixture
def scores(langfuse, monkeypatch):
    guardados = []
    monkeypatch.setattr(langfuse, "create_score", lambda **k: guardados.append(k))
    return guardados


@pytest.fixture
def ambiente(contexto, langfuse, exportador, scores):
    exportador.clear()
    contexto.update(
        langfuse=langfuse,
        ollama=OllamaFalso(),
        prompts=None,
        cabecalhos={},
        prompts_falsos=LangfuseDePrompts(),
    )
    _base_com_folhas(contexto)
    return contexto


def _base_com_folhas(contexto):
    documento = Documento(
        documento_id="conservacao-folhas",
        titulo="Conservação de folhas",
        secoes=(
            Secao(
                titulo="Folhas",
                paragrafos=(
                    "Para conservar alface e outras folhas, guarde secas num pote fechado.",
                ),
            ),
        ),
        fonte=Fonte(
            titulo="Conservação de folhas", instituicao="Embrapa", ano=2020, url=None
        ),
    )
    trechos, _ = montar_trechos([], [documento])
    indexar(trechos, contexto["gerador"], contexto["repositorio"])


def _caso_de_uso(contexto):
    cliente = contexto["langfuse"]
    prompt = "Responda citando os trechos."
    lidos = {}
    if contexto["prompts"] is not None:
        prompt = contexto["prompts"].carregar("miau-ricio", "resposta_com_fontes_v1")
        lidos = contexto["prompts"].prompts_lidos
    return ResponderPergunta(
        contexto["gerador"],
        RepositorioObservado(contexto["repositorio"], cliente)
        if cliente
        else contexto["repositorio"],
        ModeloOllama(
            cliente=contexto["ollama"],
            modelo="qwen2.5:7b",
            ao_gerar=RegistroDeGeracoes(cliente, prompts_do_langfuse=lidos)
            if cliente
            else None,
        ),
        prompt_do_sistema=prompt,
        limiar=contexto["limiar"],
    )


def _perguntar(contexto, pergunta=PERGUNTA_PADRAO, cabecalhos=None, observador=None):
    app.dependency_overrides[obter_caso_de_uso] = lambda: _caso_de_uso(contexto)
    app.dependency_overrides[obter_observador] = lambda: (
        observador or ObservadorDePerguntas(contexto["langfuse"])
    )
    try:
        resposta = TestClient(app).post(
            "/api/v1/receitas/perguntas",
            json={"pergunta": pergunta},
            headers=cabecalhos or {},
        )
    finally:
        app.dependency_overrides.clear()
    if contexto["langfuse"]:
        contexto["langfuse"].flush()
    return resposta


def _sem_tempo(corpo: dict) -> dict:
    return {k: v for k, v in corpo.items() if k != "segundos"}


def _spans(exportador, nome=None):
    spans = exportador.get_finished_spans()
    return [s for s in spans if nome is None or s.name == nome]


def _raiz(exportador):
    [raiz] = _spans(exportador, NOME_DO_REGISTRO)
    return dict(raiz.attributes)


# --- dado -------------------------------------------------------------------------


@given("que as chaves do Langfuse estão configuradas")
def chaves_configuradas(ambiente):
    assert ambiente["langfuse"] is not None


@given("que as chaves do Langfuse não estão configuradas")
def chaves_nao_configuradas(ambiente):
    ambiente["langfuse"] = criar_cliente(Configuracao(_env_file=None))
    assert ambiente["langfuse"] is None


@given("um identificador anônimo e um identificador de conversa válidos")
def identificadores_validos(ambiente):
    ambiente["cabecalhos"] = {"X-Identificador-Anonimo": PESSOA, "X-Conversa": CONVERSA}


@given("uma função de mascaramento que falha")
def mascaramento_que_falha(ambiente, monkeypatch):
    def quebrar(_):
        raise RuntimeError("padrão inválido")

    monkeypatch.setattr(mascaramento, "mascarar_dado", quebrar)


@given("que a base de conhecimento tem um trecho sobre conservação de folhas")
def base_com_folhas(ambiente):
    pass  # a base do ambiente já tem o trecho


@given("que o Ollama está fora do ar")
def ollama_fora_do_ar(ambiente):
    ambiente["ollama"].fora_do_ar = True


@given("um cliente do Langfuse que falha ao enviar")
def langfuse_que_falha(ambiente):
    ambiente["observador"] = ObservadorDePerguntas(LangfuseQueFalha())


@given(parsers.parse('o arquivo de prompt "{arquivo}"'))
def arquivo_de_prompt(ambiente, arquivo, tmp_path):
    agente, nome = arquivo.split("/")
    (tmp_path / agente).mkdir(exist_ok=True)
    (tmp_path / agente / nome).write_text("Prompt da versão 2")
    ambiente["pasta"] = tmp_path
    ambiente["em_uso"] = {arquivo.removesuffix(".md")}


@given("que os prompts já foram sincronizados")
def prompts_sincronizados(ambiente, tmp_path):
    arquivo_de_prompt(ambiente, "miau-ricio/resposta_com_fontes_v2.md", tmp_path)
    sincronizar_prompts(
        ambiente["prompts_falsos"], ambiente["em_uso"], ambiente["pasta"]
    )
    ambiente["criados_antes"] = ambiente["prompts_falsos"].criados


@given("que o Langfuse não responde")
def langfuse_nao_responde(ambiente):
    ambiente["prompts_falsos"].fora_do_ar = True


@given("que o prompt de resposta foi lido do Langfuse")
def prompt_lido_do_langfuse(ambiente):
    ambiente["prompts_falsos"].create_prompt(
        name="miau-ricio/resposta_com_fontes",
        prompt="Prompt do Langfuse: responda citando os trechos.",
        labels=["v1", PRODUCAO],
    )
    ambiente["prompts"] = PromptsDoLangfuse(ambiente["prompts_falsos"])


# --- quando -----------------------------------------------------------------------


@when(parsers.parse('a API recebe a pergunta "{pergunta}"'))
def api_recebe_a_pergunta(ambiente, pergunta):
    ambiente["http"] = _perguntar(ambiente, pergunta)


@when("a API recebe uma pergunta")
def api_recebe_uma_pergunta(ambiente):
    ambiente["http"] = _perguntar(ambiente, observador=ambiente.get("observador"))


@when("a API recebe uma pergunta com os dois cabeçalhos")
def api_recebe_com_cabecalhos(ambiente):
    ambiente["http"] = _perguntar(ambiente, cabecalhos=ambiente["cabecalhos"])


@when(
    parsers.parse(
        'a API recebe uma pergunta com o cabeçalho X-Identificador-Anonimo "{valor}"'
    )
)
def api_recebe_identificador_invalido(ambiente, valor):
    ambiente["http"] = _perguntar(
        ambiente, cabecalhos={"X-Identificador-Anonimo": valor}
    )


@when("eu sincronizo os prompts")
@when("eu sincronizo os prompts de novo")
def sincronizar(ambiente):
    ambiente["sincronizados"] = sincronizar_prompts(
        ambiente["prompts_falsos"], ambiente["em_uso"], ambiente["pasta"]
    )


@when("o Miau-ricio carrega o prompt de resposta")
def carregar_prompt_de_resposta(ambiente):
    prompts = PromptsDoLangfuse(ambiente["prompts_falsos"])
    ambiente["prompt_carregado"] = prompts.carregar(
        "miau-ricio", "resposta_com_fontes_v1"
    )


# --- então ------------------------------------------------------------------------


@then(parsers.parse('o Langfuse recebe um registro "{nome}"'))
def recebe_registro(ambiente, exportador, nome):
    assert ambiente["http"].status_code == 200, ambiente["http"].text
    assert len(_spans(exportador, nome)) == 1


@then("o registro tem uma busca com os trechos e os scores")
def registro_tem_busca(exportador):
    [busca] = _spans(exportador, "busca no Qdrant")
    saida = json.loads(busca.attributes["langfuse.observation.output"])
    assert saida and {"titulo", "score"} <= set(saida[0])


@then("o registro tem uma chamada ao LLM com o modelo, os tokens e a latência")
def registro_tem_llm(exportador):
    [geracao] = [
        s
        for s in _spans(exportador)
        if s.attributes.get("langfuse.observation.type") == "generation"
    ]
    atributos = dict(geracao.attributes)
    assert atributos["langfuse.observation.model.name"] == "qwen2.5:7b"
    uso = json.loads(atributos["langfuse.observation.usage_details"])
    assert uso == {"input": 120, "output": 15}
    assert float(atributos["langfuse.observation.metadata.segundos"]) >= 0


@then("o registro tem o identificador anônimo como pessoa")
def registro_tem_pessoa(exportador):
    assert _raiz(exportador)["user.id"] == PESSOA


@then("o registro tem o identificador da conversa como sessão")
def registro_tem_sessao(exportador):
    assert _raiz(exportador)["session.id"] == CONVERSA


@then("o registro não tem pessoa")
def registro_sem_pessoa(exportador):
    assert "user.id" not in _raiz(exportador)


@then("a resposta é a mesma de uma pergunta sem o cabeçalho")
@then("a resposta é a mesma de uma pergunta sem registro")
def resposta_igual(ambiente):
    referencia = dict(ambiente, langfuse=None, ollama=OllamaFalso())
    sem_registro = _perguntar(referencia, observador=ObservadorDePerguntas(None))
    assert ambiente["http"].status_code == sem_registro.status_code == 200
    assert _sem_tempo(ambiente["http"].json()) == _sem_tempo(sem_registro.json())


@then(parsers.parse('a entrada registrada é "{registrada}"'))
def entrada_registrada(exportador, registrada):
    bruta = _raiz(exportador)["langfuse.observation.input"]
    try:
        entrada = json.loads(bruta)["pergunta"]
    except json.JSONDecodeError:  # o marcador de falha vai como texto puro
        entrada = bruta
    assert entrada == registrada


@then("a API responde normalmente")
def responde_normalmente(ambiente):
    assert ambiente["http"].status_code == 200, ambiente["http"].text


@then(parsers.parse('o registro tem o score "{nome}" igual a verdadeiro'))
def score_verdadeiro(scores, nome):
    [score] = [s for s in scores if s["name"] == nome]
    assert (score["value"], score["data_type"]) == (1.0, "BOOLEAN")


@then(parsers.parse('o registro tem o score "{nome}"'))
def tem_score(scores, nome):
    assert any(s["name"] == nome for s in scores)


@then("a API responde 503")
def responde_503(ambiente):
    assert ambiente["http"].status_code == 503


@then("o registro tem nível de erro")
def nivel_de_erro(exportador):
    assert _raiz(exportador)["langfuse.observation.level"] == "ERROR"


@then("nenhum registro é enviado")
def nada_enviado(exportador, scores):
    assert _spans(exportador) == []
    assert scores == []


@then(parsers.parse('o Langfuse tem o prompt "{nome}" com o rótulo "{rotulo}"'))
def tem_prompt(ambiente, nome, rotulo):
    prompt = ambiente["prompts_falsos"].get_prompt(nome, label=rotulo)
    assert prompt.prompt == "Prompt da versão 2"


@then(parsers.parse('o prompt em uso pela configuração tem o rótulo "{rotulo}"'))
def em_uso_tem_rotulo(ambiente, rotulo):
    [em_uso] = [s for s in ambiente["sincronizados"] if s.em_producao]
    prompt = ambiente["prompts_falsos"].get_prompt(em_uso.nome, label=rotulo)
    assert prompt.version == em_uso.versao


@then("nenhuma versão nova é criada no Langfuse")
def nenhuma_versao_nova(ambiente):
    assert ambiente["prompts_falsos"].criados == ambiente["criados_antes"]


@then("o texto é o do arquivo local")
def texto_do_arquivo(ambiente):
    from economia.compartilhado.infraestrutura.prompts import carregar_prompt

    assert ambiente["prompt_carregado"] == carregar_prompt(
        "miau-ricio", "resposta_com_fontes_v1"
    )


@then(
    parsers.parse(
        'a chamada ao LLM registrada está ligada ao prompt "{nome}" e à versão usada'
    )
)
def chamada_ligada_ao_prompt(exportador, nome):
    [geracao] = [
        s
        for s in _spans(exportador)
        if s.attributes.get("langfuse.observation.type") == "generation"
    ]
    atributos = dict(geracao.attributes)
    assert atributos["langfuse.observation.prompt.name"] == nome
    assert atributos["langfuse.observation.prompt.version"] == 1
