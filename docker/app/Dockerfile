FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    gcc \
    curl && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /bin/

RUN useradd -l -m -u 1000 app && \
    mkdir /app && chown app:app /app

WORKDIR /app
USER app

COPY --chown=app:app ./pyproject.toml ./uv.lock ./

RUN --mount=type=cache,target=/home/app/.cache/uv,uid=1000 \
    uv sync --group backend --frozen

COPY --chown=app:app ./backend_src ./backend_src

CMD [\
    "uvicorn", "backend_src.main:app", \
    "--log-config", "./backend_src/logging.json" \
]
