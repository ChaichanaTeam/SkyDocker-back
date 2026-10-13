FROM python:3.11-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group test --frozen


FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd -l -m -u 1000 app && \
    mkdir /app && chown app:app /app

WORKDIR /app
USER app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./tests /app/tests

CMD ["pytest", "tests", "-v", "-x", "--capture=tee-sys"]
