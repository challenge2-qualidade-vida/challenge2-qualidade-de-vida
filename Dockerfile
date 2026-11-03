# Imagem da EconoMIA para publicar em hospedagem gratuita (Render, Hugging Face Spaces).
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data ./data

# Na nuvem não há Ollama: use Groq ou Gemini (plano gratuito) definindo
# LLM_PROVEDOR e LLM_API_KEY como segredos no painel da hospedagem.
# Sem chave, o app funciona no modo sem LLM.
ENV LLM_PROVEDOR=nenhum \
    PORT=8000

RUN useradd --create-home economia && chown -R economia /app
USER economia

EXPOSE 8000
CMD ["sh", "-c", "uvicorn economia.api:app --app-dir src --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
