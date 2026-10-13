FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN useradd -l -m app

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    gcc \
    curl && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./uv.lock /app/

RUN uv sync --group backend --frozen --no-cache

COPY ./backend_src /app/backend_src

RUN chown -R app:app /app
RUN chmod -R u+rwx /app

USER app

CMD [\
    "uv", "run", "uvicorn", "backend_src.main:app", \
    "--log-config", "./backend_src/logging.json" \
]