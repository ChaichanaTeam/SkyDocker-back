import asyncio

import pytest
from fakeredis import FakeAsyncRedis
from pydantic import BaseModel

from backend_src import sync
from backend_src.cache import acquire_sync_lock, get_sync_status
from backend_src.sync.runner import summarize


def _report() -> sync.TerrainSyncReport:
    return sync.TerrainSyncReport(cells=2, stored=1, loaded=1, sea=[], terrain_measured=5, attribution="test")


async def _ok() -> sync.TerrainSyncReport:
    return _report()


async def _failing() -> sync.TerrainSyncReport:
    raise sync.UpstreamUnavailable("Copernicus DEM request failed: timeout")


def test_successful_run():
    async def scenario():
        redis = FakeAsyncRedis()
        report = await sync.run_sync("terrain", "geo-zone", 60, _ok, redis, "schedule")
        return report, await get_sync_status(redis, "terrain"), await acquire_sync_lock(redis, "geo-zone", 60)

    report, status, lock_after = asyncio.run(scenario())
    assert report == _report(), "The report of the sync must be returned"
    assert status is not None and status["status"] == "ok", f"A successful run must be kept as ok: {status}"
    assert status["trigger"] == "schedule", f"The trigger of the run must be kept: {status}"
    assert status["finished_at"] is not None, f"A finished run must have its end time: {status}"
    assert "terrain_measured 5" in status["summary"], f"The counts of the report must be kept: {status}"
    assert lock_after is not None, "The lock must be released after the run"


def test_busy_lock_skips_run():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_sync_lock(redis, "geo-zone", 60)
        with pytest.raises(sync.SyncBusy):
            await sync.run_sync("activity", "geo-zone", 60, _ok, redis, "admin")
        return await get_sync_status(redis, "activity")

    status = asyncio.run(scenario())
    assert status is not None and status["status"] == "skipped", f"A run that did not start must be kept as skipped: {status}"
    assert status["trigger"] == "admin", f"The trigger of the run must be kept: {status}"


def test_failed_run_releases_lock():
    async def scenario():
        redis = FakeAsyncRedis()
        with pytest.raises(sync.UpstreamUnavailable):
            await sync.run_sync("terrain", "geo-zone", 60, _failing, redis, "cli")
        return await get_sync_status(redis, "terrain"), await acquire_sync_lock(redis, "geo-zone", 60)

    status, lock_after = asyncio.run(scenario())
    assert status is not None and status["status"] == "failed", f"A failed run must be kept as failed: {status}"
    assert "timeout" in status["summary"], f"Why the run failed must be kept for the logs: {status}"
    assert lock_after is not None, "A failed run must release its lock"


def test_summary_of_nested_reports():
    class Combined(BaseModel):
        terrain: sync.TerrainSyncReport
        sea: list[str]

    summary = summarize(Combined(terrain=_report(), sea=["N55_00_E016_00"]))
    assert summary == "terrain (cells 2, stored 1, loaded 1, sea 0, terrain_measured 5), sea 1", summary
