FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN useradd -l -m app

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --group test --frozen --no-cache

COPY ./tests /app/tests

RUN chown -R app:app /app
RUN chmod -R u+rwx /app

USER app

CMD ["uv", "run", "pytest", "tests", "-v", "-x", "--capture=tee-sys"]