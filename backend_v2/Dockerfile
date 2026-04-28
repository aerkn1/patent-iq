FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install "poetry>=2.1.0,<3.0.0"

COPY pyproject.toml ./
RUN poetry install --no-root --without dev

COPY . .
RUN chmod +x scripts/start_container.sh

EXPOSE 8000

ENTRYPOINT ["./scripts/start_container.sh"]
