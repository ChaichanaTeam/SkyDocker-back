from typing import Any, Awaitable, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from .config import WorkerSettings
from .constants import MISFIRE_GRACE_SECONDS


def create_scheduler() -> AsyncIOScheduler:
    return AsyncIOScheduler(
        timezone=WorkerSettings.TIMEZONE,
        job_defaults={
            # runs missed while the worker was down or busy happen once, not once per missed time
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": MISFIRE_GRACE_SECONDS,
        },
    )


def cron(expression: Optional[str]) -> Optional[CronTrigger]:
    """Trigger of a cron job, None when the job is disabled."""
    return CronTrigger.from_crontab(expression, timezone=WorkerSettings.TIMEZONE) if expression else None


def every(minutes: int) -> Optional[IntervalTrigger]:
    """Trigger of an interval job, None when the job is disabled."""
    return IntervalTrigger(minutes=minutes, timezone=WorkerSettings.TIMEZONE) if minutes > 0 else None


def schedule(
    scheduler: AsyncIOScheduler, name: str, job: Callable[..., Awaitable[Any]], trigger: Optional[BaseTrigger], *args: Any,
) -> None:
    if trigger is None:
        logger.info(f"Job {name} is disabled")
        return

    scheduler.add_job(job, trigger, args=args, id=name, name=name)
    logger.info(f"Job {name} scheduled: {trigger}")
