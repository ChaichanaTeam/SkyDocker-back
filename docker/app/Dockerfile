FROM python:3.11-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    gcc && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /bin/

WORKDIR /app

COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group backend --frozen


FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y \
    libpq5 && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

RUN useradd -l -m -u 1000 app && \
    mkdir /app && chown app:app /app

WORKDIR /app
USER app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./backend_src ./backend_src

CMD [\
    "uvicorn", "backend_src.main:app", \
    "--log-config", "./backend_src/logging.json" \
]
