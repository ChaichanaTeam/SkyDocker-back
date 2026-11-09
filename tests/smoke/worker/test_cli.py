import asyncio
from types import SimpleNamespace

import pytest
from fakeredis import FakeAsyncRedis, FakeServer

from backend_src import sync
from backend_src.cache import acquire_sync_lock
from backend_src.worker import cli


def _terrain_report() -> sync.TerrainSyncReport:
    return sync.TerrainSyncReport(cells=1, stored=1, loaded=0, sea=[], terrain_measured=0, attribution="test")


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> FakeServer:
    """Redis of the CLI runs, without a log file."""
    server = FakeServer()
    monkeypatch.setattr(cli, "Redis", SimpleNamespace(from_url=lambda url: FakeAsyncRedis(server=server)))
    monkeypatch.setattr(cli, "setup_logging", lambda log_file: None)
    return server


def _use_terrain(monkeypatch: pytest.MonkeyPatch, action) -> None:
    monkeypatch.setitem(cli._SYNCS, "terrain", (sync.GEO_ZONE_LOCK, 60, action))


def test_successful_run(monkeypatch: pytest.MonkeyPatch, server: FakeServer):
    async def ok(db):
        return _terrain_report()

    _use_terrain(monkeypatch, ok)
    assert asyncio.run(cli.run_once("terrain")) == 0, "A successful run must exit with 0"


def test_failed_run(monkeypatch: pytest.MonkeyPatch, server: FakeServer):
    async def failing(db):
        raise sync.UpstreamUnavailable("Copernicus DEM request failed: timeout")

    _use_terrain(monkeypatch, failing)
    assert asyncio.run(cli.run_once("terrain")) == 1, "A failed run must exit with 1"


def test_busy_run(monkeypatch: pytest.MonkeyPatch, server: FakeServer):
    async def ok(db):
        return _terrain_report()

    _use_terrain(monkeypatch, ok)

    async def scenario():
        await acquire_sync_lock(FakeAsyncRedis(server=server), sync.GEO_ZONE_LOCK, 60)
        return await cli.run_once("terrain")

    assert asyncio.run(scenario()) == 2, "A run that did not start because of a held lock must exit with 2"


def test_catalog_is_followed_by_terrain():
    assert cli.RUN_ORDER["catalog"] == ("catalog", "terrain"), "A manual catalog sync must also load the terrain"
    assert cli.RUN_ORDER["all"][-1] == "activity", "Activity windows are matched to zones, so they go last"
