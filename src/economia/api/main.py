"""Aplicação principal da API EconoMIA."""

from fastapi import FastAPI

app = FastAPI(
    title="EconoMIA API",
    description="API do projeto EconoMIA.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def healthcheck() -> dict[str, str]:
    """Verifica se a aplicação está funcionando."""
    return {"status": "ok"}
