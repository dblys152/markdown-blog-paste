FROM ghcr.io/astral-sh/uv:0.12.3 AS uv
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --locked --no-dev

EXPOSE 8080

CMD ["sh", "-c", "uvicorn md2blog.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
