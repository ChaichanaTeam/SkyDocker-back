# Skydocker (backend)

Infrastructure consists of these sevices:
- `db` - PostGIS/Postgres image with extensions
- `redis` - caching server
- `app` - main ASGI server

Testing environment:
- `test` - isolated tool for testing endpoints


## Dependencies

For local runs recommended to use `Docker`      \
Backend application uses `uv` project manager   \
Install it before run in non-docker environment

```bash
pip install uv
```

### Database - Postgres
- PostGIS image
- Uber H3
- PgChron

### Database migrations

`Alembic` is present as Python->SQL migration

If want to easily migrate in another (SQL->Python) way, use `sqlacodegen`:

```powershell
$env:DB = (uv run python -c 'from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv(\"SQLACODEGEN_URL\"))')
sqlacodegen $env:DB > output/model.py
```

### Backend

Using Python 3.11

Dependencies separated into 2 dependency groups:
- `backend`
- `test`

and one global `all` - for non-docker local runs

To satisfy dependencies write:

```bash
uv sync --group group_name
```

Check [pyproject.toml](./pyproject.toml) for more


## Launching

To run project you must setup .env file or export environment variables
List of variables described in [.env.example](./.env.example)

If running in non-docker environment - before local run setup database and redis

### Once all set

Docker run:

```bash
docker compose up --build app
```

Local run:

```bash
uv run uvicorn backend_src.main:app --host 0.0.0.0 --port 8000 --reload --log-config ./backend_src/logging.json
```

Can run with VS Code tasks:
`Ctrl + Shift + P` -> `Tasks: Run task`

Local run:
- Uvicorn: Run server app
- Pytest: Run tests

Docker run:
- Docker: Run app container with build
- Docker: Run app container cached
- Docker: Run test environment

### Tests

Tests are split into suites: `smoke`, `e2e`, `integration`      \
Smoke tests always run first and stop the run on failure       \
By default only `smoke` is run, pick another one with `--suite` or `TEST_SUITE`

```bash
uv run pytest --suite e2e
TEST_SUITE=integration docker compose run --build --rm test
```

## API Docs

Swagger UI: on `docs/` endpoint

## LICENSE

[MIT License](./LICENSE)
