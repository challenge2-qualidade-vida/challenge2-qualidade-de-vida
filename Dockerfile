FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.5.1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY README.md pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction

COPY src ./src

RUN poetry install --only-root --no-interaction

EXPOSE 8000

CMD ["uvicorn", "economia.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
