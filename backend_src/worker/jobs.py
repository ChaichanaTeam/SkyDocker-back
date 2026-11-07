from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from pydantic import BaseModel

from backend_src import sync
from backend_src.cache import AsyncRedisSession
from backend_src.db import AsyncDBSession, AsyncSessionMaker, Queries
from .config import WorkerSettings
from .scheduler import cron, every, schedule


class SyncJobs:
    """Scheduled syncs; one whose data source failed is tried again after the retry delays."""

    def __init__(self, scheduler: AsyncIOScheduler, redis: AsyncRedisSession) -> None:
        self._scheduler = scheduler
        self._redis = redis

    def register(self) -> None:
        schedule(self._scheduler, "catalog", self.catalog, cron(WorkerSettings.CATALOG_CRON))
        schedule(self._scheduler, "activity", self.activity, every(WorkerSettings.ACTIVITY_INTERVAL_MINUTES))
        schedule(self._scheduler, "border", self.border, cron(WorkerSettings.BORDER_CRON))

        if WorkerSettings.RUN_ON_START:
            # without a trigger the job runs once right away
            self._scheduler.add_job(self.startup, id="startup", name="startup")

    async def startup(self) -> None:
        """Syncs what the database lacks, so a new database fills up without manual runs."""
        async with AsyncSessionMaker() as db:
            has_zones = await Queries.GeoZone.any_stored(db)

        if has_zones:
            # skips stored tiles and measures only zones without a value, cheap when nothing is missing
            await self.terrain(trigger="startup")
        elif WorkerSettings.CATALOG_CRON:
            has_zones = await self.catalog(trigger="startup")

        if has_zones and WorkerSettings.BORDER_CRON:
            async with AsyncSessionMaker() as db:
                countries = await Queries.Country.get_with_geo_zones(db, without_border=True)
            for country in countries:
                await self.country_border(country.country_tag, trigger="startup")

        # activity windows are matched to stored zones
        if has_zones and WorkerSettings.ACTIVITY_INTERVAL_MINUTES:
            await self.activity(trigger="startup")

    async def catalog(self, attempt: int = 0, trigger: sync.Trigger = "schedule") -> bool:
        """Catalog sync, then the terrain sync loads tiles for zones in new places and measures new zones."""
        if not await self._run(
            "catalog", sync.GEO_ZONE_LOCK, sync.CATALOG_LOCK_TTL_SECONDS, sync.sync_catalog,
            trigger, WorkerSettings.RETRY_DELAYS_MINUTES, attempt, self.catalog,
        ):
            return False

        await self.terrain(trigger=trigger)
        return True

    async def terrain(self, attempt: int = 0, trigger: sync.Trigger = "schedule") -> None:
        await self._run(
            "terrain", sync.GEO_ZONE_LOCK, sync.TERRAIN_LOCK_TTL_SECONDS, sync.sync_terrain,
            trigger, WorkerSettings.RETRY_DELAYS_MINUTES, attempt, self.terrain,
        )

    async def activity(self, attempt: int = 0, trigger: sync.Trigger = "schedule") -> None:
        await self._run(
            "activity", sync.GEO_ZONE_LOCK, sync.ACTIVITY_LOCK_TTL_SECONDS, sync.sync_activity,
            trigger, WorkerSettings.ACTIVITY_RETRY_DELAYS_MINUTES, attempt, self.activity,
        )

    async def border(self) -> None:
        """Borders of the countries that have geo-zones, check-ins there are verified against them."""
        async with AsyncSessionMaker() as db:
            countries = await Queries.Country.get_with_geo_zones(db)

        for country in countries:
            await self.country_border(country.country_tag)

    async def country_border(self, country_tag: str, attempt: int = 0, trigger: sync.Trigger = "schedule") -> None:
        async def action(db: AsyncDBSession) -> sync.BorderSyncReport:
            country = await Queries.Country.get_by_tag(country_tag, db)
            if country is None:
                raise sync.NothingToSync(f"Country {country_tag} is not in the database")
            return await sync.sync_border(country, db)

        lock = sync.border_lock(country_tag)
        await self._run(
            lock, lock, sync.BORDER_LOCK_TTL_SECONDS, action,
            trigger, WorkerSettings.RETRY_DELAYS_MINUTES, attempt, self.country_border, country_tag,
        )

    async def _run(
        self, job: str, lock: str, lock_ttl_seconds: int, action: Callable[[AsyncDBSession], Awaitable[BaseModel]],
        trigger: sync.Trigger, retry_delays: list[int], attempt: int, rerun: Callable[..., Awaitable[Any]], *rerun_args: Any,
    ) -> bool:
        """Whether the sync succeeded; run_sync logs a failed one, a retryable failure is tried again later."""
        if attempt == 0:
            # a regular run replaces a pending retry
            self._cancel_retry(job)

        async with AsyncSessionMaker() as db:
            try:
                await sync.run_sync(
                    job, lock, lock_ttl_seconds, lambda: action(db), self._redis, "retry" if attempt else trigger,
                )
            except sync.SyncError as exc:
                if exc.retryable:
                    await self._retry_later(job, retry_delays, attempt, rerun, *rerun_args)
                return False
            except Exception:
                return False

        return True

    async def _retry_later(
        self, job: str, retry_delays: list[int], attempt: int, rerun: Callable[..., Awaitable[Any]], *rerun_args: Any,
    ) -> None:
        if attempt >= len(retry_delays):
            logger.error(f"Sync {job} failed {attempt + 1} times, waiting for its next scheduled run")
            return

        delay = retry_delays[attempt]
        retry_at = datetime.now(timezone.utc) + timedelta(minutes=delay)
        # own id per attempt, the retry being scheduled from may still be running
        retry_id = f"{_retry_prefix(job)}{attempt + 1}"
        self._scheduler.add_job(rerun, "date", run_date=retry_at, args=[*rerun_args, attempt + 1], id=retry_id, name=retry_id)
        await sync.record_retry(self._redis, job, retry_at)
        logger.info(f"Sync {job} will be tried again in {delay} min, retry {attempt + 1} of {len(retry_delays)}")

    def _cancel_retry(self, job: str) -> None:
        for scheduled in self._scheduler.get_jobs():
            if scheduled.id.startswith(_retry_prefix(job)):
                scheduled.remove()
                logger.info(f"Pending retry of sync {job} cancelled by a new run")


def _retry_prefix(job: str) -> str:
    return f"retry:{job}:"
