# Skydocker (backend)

Infrastructure consists of these sevices:
- `db` - PostGIS/Postgres image with extensions
- `redis` - caching server
- `storage` - SeaweedFS object storage (S3 API), see [docker/storage](docker/storage/README.md)
- `app` - main ASGI server
- `worker` - scheduled data syncs (geo-zones, terrain, country borders), same image as `app`

Testing environment:
- `test` - isolated tool for testing endpoints

### Structure

Each service lives in its own folder with `compose.yml`, `Dockerfile` and init files

```
docker-compose.yml            # includes services, declares networks
docker-compose.override.yml   # local dev overrides, applied automatically
docker/
  db/       # Postgres image, init/ - baseline schema scripts (run on empty volume only)
  redis/    # Redis image, ACL template rendered by entrypoint.sh at start
  storage/  # SeaweedFS image, S3 identities rendered at start, init.sh sets up buckets
  app/      # backend image
  worker/   # sync worker, built from the backend image
  test/     # pytest image
```

Networks:
- `backend` - `db`, `redis`, `storage`, `app`, `worker`. Storages are reachable only by services that use them
- `edge` - `app`, `storage`, `test`. Public facing layer, place for a CDN / reverse proxy

### Adding a service

1. Create `docker/<service>/` with `compose.yml` (and `Dockerfile` if needed)
2. Add it to `include` in [docker-compose.yml](./docker-compose.yml) with `env_file: .env`
3. Attach it to `backend` and / or `edge` networks
4. Dev-only settings (ports, mounts) go to [docker-compose.override.yml](./docker-compose.override.yml)


## Dependencies

For local runs recommended to use `Docker`      \
Backend application uses `uv` project manager   \
Install it before run in non-docker environment

```bash
pip install uv
```

### Database - Postgres 17
With extensions:
- PostGIS
- Uber H3
- PgChron

### Database migrations

For non-core developers:
Use Tasks in VS Code to migrate your DB to head 

For core developers:
> [!IMPORTANT]
> Schema scripts in `docker/db/init` are frozen as revision `0001_baseline`        \
> Every further schema change is a revision in `alembic/versions`, don't edit init scripts

`Alembic` is present as Python->SQL migration

- New volume: init scripts stamp database with `0001_baseline` automatically
- Existing volume (created before migrations): stamp it once

```bash
uv run alembic stamp 0001_baseline
```

Apply migrations (from host set `DB_HOST=localhost`, `.env` points to `db` container):

```bash
uv run alembic upgrade head
```

**!! To read !!** \
How to write a revision: [alembic/README.md](./alembic/README.md)

> [!CAUTION]
> Using *sqlacodegen* migration now will make no changes and can lead to destructive behaviour!

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

Docker run (dev: `db` / `redis` ports on `127.0.0.1`, hot reload of `backend_src` in `app`):

```bash
docker compose up --build app worker
```

Docker run without dev overrides (no published `db` / `redis` ports, no reload):

```bash
docker compose -f docker-compose.yml up --build app worker
```

Local run:

```bash
uv run uvicorn backend_src.main:app --host 0.0.0.0 --port 8000 --reload --log-config ./backend_src/logging.json
```

Can run with VS Code tasks:
`Ctrl + Shift + P` -> `Tasks: Run task`

Local run:
- Uvicorn: Run server app
- Worker: Run scheduled syncs
- Pytest: Run tests
- Alembic: Upgrade to head

Docker run:
- Docker: Run app and worker containers with build
- Docker: Run app and worker containers cached
- Docker: Run test environment

### Sync worker

`worker` keeps geo-zones, their activity, terrain and country borders up to date on a schedule, see `SYNC_*` in [.env.example](./.env.example). An empty cron or `0` minutes disables a job

Without the variables the PANSA syncs run on the normal schedule. `.env.example` disables them, so dev machines do not load the official PANSA API

The worker does not reload code: after a change run `docker compose restart worker`

Run a sync right away, without retries (`catalog`, `terrain`, `activity`, `border` or `all`, e.g. to fill a new database):

```bash
docker compose exec worker python -m backend_src.worker run all
```

Exit code: `0` ok, `1` the sync failed, `2` it did not start because another sync of the same data is running. `GET /api/v1/health` shows whether the worker is up and the last run of every sync

### Tests

Tests are split into suites: `smoke`, `e2e`, `integration`      \
Smoke tests always run first and stop the run on failure       \
By default only `smoke` is run, pick another one with `--suite` or `TEST_SUITE`

Inside a suite tests can be filtered by module (`tests/<suite>/<module>`) \
with `--module` / `--exclude-module` or `TEST_MODULES` / `TEST_EXCLUDE_MODULES`

```bash
uv run pytest --suite e2e
uv run pytest --suite integration --module auth
uv run pytest --suite e2e --exclude-module auth
TEST_SUITE=integration TEST_MODULES=auth docker compose run --build --rm test
```

## API Docs

Swagger UI: on `docs/` endpoint

## LICENSE

[MIT License](./LICENSE)
