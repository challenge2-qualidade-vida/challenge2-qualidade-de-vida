"""Cliente de LLM gratuito, no formato "OpenAI-compatível".

Ollama (local), Groq e Gemini aceitam o mesmo formato de requisição
(/chat/completions com "tools"), então um cliente só atende os três.

Configuração por variáveis de ambiente:
  LLM_PROVEDOR  ollama (padrão) | groq | gemini | nenhum
  LLM_MODELO    opcional; senão usa o padrão do provedor
  LLM_API_KEY   obrigatória para groq e gemini (chave gratuita)
  LLM_URL       opcional; sobrescreve o endereço do provedor
"""

import os
from dataclasses import dataclass

import httpx

PROVEDORES = {
    "ollama": {"url": "http://localhost:11434/v1", "modelo": "qwen2.5:7b", "precisa_chave": False},
    "groq": {"url": "https://api.groq.com/openai/v1", "modelo": "llama-3.3-70b-versatile", "precisa_chave": True},
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/openai", "modelo": "gemini-2.5-flash", "precisa_chave": True},
}


class ErroLLM(Exception):
    pass


@dataclass
class ClienteLLM:
    provedor: str
    url: str
    modelo: str
    chave: str | None = None
    timeout: float = 120

    def conversar(self, mensagens: list[dict], ferramentas: list[dict] | None = None, temperatura: float = 0.2) -> dict:
        """Envia a conversa e devolve a mensagem do assistente (com ou sem tool_calls)."""
        corpo = {"model": self.modelo, "messages": mensagens, "temperature": temperatura}
        if ferramentas:
            corpo["tools"] = ferramentas
        cabecalhos = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        try:
            r = httpx.post(f"{self.url}/chat/completions", json=corpo, headers=cabecalhos, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            raise ErroLLM(f"{self.provedor}: {e}") from e


def cliente_do_ambiente() -> ClienteLLM | None:
    """Cria o cliente a partir das variáveis de ambiente. None = modo sem LLM."""
    provedor = os.environ.get("LLM_PROVEDOR", "ollama").lower()
    if provedor == "nenhum":
        return None
    if provedor not in PROVEDORES:
        raise ValueError(f"LLM_PROVEDOR desconhecido: {provedor}. Use: {', '.join(PROVEDORES)} ou nenhum.")
    config = PROVEDORES[provedor]
    chave = os.environ.get("LLM_API_KEY")
    if config["precisa_chave"] and not chave:
        return None
    return ClienteLLM(
        provedor=provedor,
        url=os.environ.get("LLM_URL", config["url"]).rstrip("/"),
        modelo=os.environ.get("LLM_MODELO", config["modelo"]),
        chave=chave,
    )
