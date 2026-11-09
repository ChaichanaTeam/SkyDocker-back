import asyncio

import pytest
from fakeredis import FakeAsyncRedis

from backend_src import sync
from backend_src.cache import get_sync_status
from backend_src.worker.config import WorkerSettings
from backend_src.worker.jobs import SyncJobs
from backend_src.worker.scheduler import create_scheduler


def _pending_retries(jobs: SyncJobs) -> list[str]:
    return [job.id for job in jobs._scheduler.get_jobs() if job.id.startswith("retry:")]


async def _until(condition, seconds: float = 3) -> None:
    for _ in range(int(seconds / 0.05)):
        if condition():
            return
        await asyncio.sleep(0.05)


def test_retryable_failure_is_retried_until_delays_run_out(monkeypatch: pytest.MonkeyPatch):
    calls = []

    async def failing(db):
        calls.append(1)
        raise sync.UpstreamUnavailable("PANSA request failed: timeout")

    monkeypatch.setattr(sync, "sync_activity", failing)
    monkeypatch.setattr(WorkerSettings, "ACTIVITY_RETRY_DELAYS_MINUTES", [0, 0])

    async def scenario():
        scheduler = create_scheduler()
        scheduler.start()
        jobs = SyncJobs(scheduler, FakeAsyncRedis())
        await jobs.activity()
        await _until(lambda: len(calls) >= 3 and not _pending_retries(jobs))
        scheduler.shutdown(wait=False)

    asyncio.run(scenario())
    assert len(calls) == 3, f"A run and two retries were expected, got {len(calls)} runs"


def test_retry_waits_and_is_cancelled_by_regular_run(monkeypatch: pytest.MonkeyPatch):
    async def failing(db):
        raise sync.UpstreamUnavailable("PANSA request failed: timeout")

    monkeypatch.setattr(sync, "sync_activity", failing)
    monkeypatch.setattr(WorkerSettings, "ACTIVITY_RETRY_DELAYS_MINUTES", [30])

    async def scenario():
        scheduler = create_scheduler()
        scheduler.start()
        redis = FakeAsyncRedis()
        jobs = SyncJobs(scheduler, redis)

        await jobs.activity()
        pending, status = _pending_retries(jobs), await get_sync_status(redis, "activity")

        async def ok(db):
            return sync.ActivitySyncReport(
                activations=0, notams=0, windows=0, inserted=0, deleted=0, unchanged=0,
                zones_with_windows=0, ignored=0, unmatched=[],
            )
        monkeypatch.setattr(sync, "sync_activity", ok)
        await jobs.activity()
        pending_after, status_after = _pending_retries(jobs), await get_sync_status(redis, "activity")

        scheduler.shutdown(wait=False)
        return pending, status, pending_after, status_after

    pending, status, pending_after, status_after = asyncio.run(scenario())
    assert pending == ["retry:activity:1"], f"A failed run must be retried later: {pending}"
    assert status is not None and status["status"] == "retrying", f"A run waiting for its retry must say so: {status}"
    assert status["retry_at"] is not None, f"The time of the retry must be kept: {status}"
    assert pending_after == [], f"A regular run must replace the pending retry: {pending_after}"
    assert status_after is not None and status_after["status"] == "ok", f"The regular run must be kept: {status_after}"


def test_non_retryable_failure_is_not_retried(monkeypatch: pytest.MonkeyPatch):
    async def aborted(db):
        raise sync.SyncAborted("PANSA returned 10 zones while 3159 are stored, sync aborted")

    monkeypatch.setattr(sync, "sync_catalog", aborted)
    monkeypatch.setattr(WorkerSettings, "RETRY_DELAYS_MINUTES", [5])

    async def scenario():
        scheduler = create_scheduler()
        scheduler.start()
        redis = FakeAsyncRedis()
        jobs = SyncJobs(scheduler, redis)
        succeeded = await jobs.catalog()
        pending, status = _pending_retries(jobs), await get_sync_status(redis, "catalog")
        scheduler.shutdown(wait=False)
        return succeeded, pending, status

    succeeded, pending, status = asyncio.run(scenario())
    assert not succeeded, "An aborted catalog sync must not count as done"
    assert pending == [], f"Retrying a broken PANSA response would not help: {pending}"
    assert status is not None and status["status"] == "failed", f"The aborted run must be kept as failed: {status}"


def test_failed_catalog_skips_terrain(monkeypatch: pytest.MonkeyPatch):
    terrain_runs = []

    async def aborted(db):
        raise sync.SyncAborted("PANSA returned 10 zones while 3159 are stored, sync aborted")

    async def terrain(db):
        terrain_runs.append(1)
        return sync.TerrainSyncReport(cells=0, stored=0, loaded=0, sea=[], terrain_measured=0, attribution="test")

    monkeypatch.setattr(sync, "sync_catalog", aborted)
    monkeypatch.setattr(sync, "sync_terrain", terrain)

    async def scenario():
        scheduler = create_scheduler()
        scheduler.start()
        await SyncJobs(scheduler, FakeAsyncRedis()).catalog()
        scheduler.shutdown(wait=False)

    asyncio.run(scenario())
    assert terrain_runs == [], "The terrain sync follows only a successful catalog sync"
