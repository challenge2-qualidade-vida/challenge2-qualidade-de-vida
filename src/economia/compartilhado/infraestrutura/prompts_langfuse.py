"""Prompts no prompt management do Langfuse (#28, spec 29).

Os prompts ficam só no Langfuse, como `<agente>/<nome>` (ex.: `miau-ricio/resposta_com_fontes`).
O código pede cada um por uma referência: `<nome>` lê o rótulo `production`; `<nome>@<rótulo>`
lê outro rótulo (ex.: `resposta_com_fontes@v2`, `resposta_com_fontes@latest`).

A cada leitura, o texto e a versão ficam numa cópia local em `data/cache/prompts/` (fora do
git). Sem as chaves ou com o Langfuse fora do ar, o prompt vem dessa cópia. Sem cópia, o
prompt está indisponível (`PromptIndisponivel`).

O prompt lido fica guardado para a geração do LLM ser vinculada a ele (`RegistroDeGeracoes`).
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PRODUCAO = "production"
PASTA_DO_CACHE = Path(__file__).resolve().parents[4] / "data" / "cache" / "prompts"
# o SDK guarda o prompt em memória e confere de novo em segundo plano depois desse tempo
CACHE_EM_SEGUNDOS = 300
# referência antiga, do tempo dos arquivos: resposta_com_fontes_v2 → rótulo v2
_NOME_COM_VERSAO = re.compile(r"^(?P<base>.+)_(?P<versao>v\d+)$")


class PromptIndisponivel(RuntimeError):
    """O prompt não veio do Langfuse e não há cópia local."""


def resolver(agente: str, referencia: str) -> tuple[str, str]:
    """Nome do prompt no Langfuse e rótulo a ler."""
    if "@" in referencia:
        nome, rotulo = referencia.split("@", 1)
    elif encontrado := _NOME_COM_VERSAO.match(referencia):
        nome, rotulo = encontrado["base"], encontrado["versao"]
    else:
        nome, rotulo = referencia, PRODUCAO
    return f"{agente}/{nome}", rotulo


@dataclass(frozen=True)
class PromptLido:
    nome: str
    rotulo: str
    versao: int
    texto: str
    lido_em: str


class PromptsDoLangfuse:
    """Lê os prompts do Langfuse, com a cópia local quando ele não responde.

    `prompts_lidos` liga o texto de cada prompt ao prompt do Langfuse, para o
    `RegistroDeGeracoes` vincular cada geração à versão usada. `versoes` diz qual versão
    de cada referência foi lida, para o registro de uma execução da avaliação.
    """

    def __init__(self, cliente: Any | None, cache: Path | None = None):
        self._cliente = cliente
        self._cache = cache or PASTA_DO_CACHE
        self.prompts_lidos: dict[str, Any] = {}
        self.versoes: dict[str, int] = {}

    def _arquivo(self, nome: str, rotulo: str) -> Path:
        return self._cache / f"{nome}@{rotulo}.json"

    def _do_langfuse(self, nome: str, rotulo: str) -> PromptLido | None:
        if self._cliente is None:
            return None
        try:
            prompt = self._cliente.get_prompt(
                nome, label=rotulo, cache_ttl_seconds=CACHE_EM_SEGUNDOS
            )
        except Exception:
            logger.warning(
                "Prompt %s@%s não veio do Langfuse; usando a cópia local",
                nome,
                rotulo,
                exc_info=True,
            )
            return None
        self.prompts_lidos[prompt.prompt] = prompt
        lido = PromptLido(
            nome=nome,
            rotulo=rotulo,
            versao=prompt.version,
            texto=prompt.prompt,
            lido_em=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self._guardar(lido)
        return lido

    def _guardar(self, lido: PromptLido) -> None:
        arquivo = self._arquivo(lido.nome, lido.rotulo)
        try:
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_text(
                json.dumps(asdict(lido), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            logger.warning(
                "Não foi possível guardar a cópia de %s", lido.nome, exc_info=True
            )

    def _da_copia(self, nome: str, rotulo: str) -> PromptLido | None:
        arquivo = self._arquivo(nome, rotulo)
        if not arquivo.is_file():
            return None
        return PromptLido(**json.loads(arquivo.read_text(encoding="utf-8")))

    def ler(self, agente: str, referencia: str) -> PromptLido:
        nome, rotulo = resolver(agente, referencia)
        lido = self._do_langfuse(nome, rotulo) or self._da_copia(nome, rotulo)
        if lido is None:
            raise PromptIndisponivel(
                f"O prompt {nome}@{rotulo} não veio do Langfuse e não há cópia local. "
                "Configure LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY no .env e confira "
                "se o prompt e o rótulo existem no Langfuse."
            )
        self.versoes[f"{agente}/{referencia}"] = lido.versao
        return lido

    def carregar(self, agente: str, referencia: str) -> str:
        return self.ler(agente, referencia).texto
