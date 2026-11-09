from typing import Any

from fastapi.responses import JSONResponse
from loguru import logger

from backend_src.cache import AsyncRedisSession, get_sync_statuses, is_worker_alive
from backend_src.core.healthcheck import BackendHealthMixin

# Fields of a sync run shown publicly, the summary may hold error details and stays in the logs
_PUBLIC_SYNC_FIELDS = ("status", "trigger", "started_at", "finished_at", "retry_at")


async def health(redis: AsyncRedisSession) -> JSONResponse:
    status = BackendHealthMixin.get_health()

    response = JSONResponse(
        {**status[0], **await _worker_health(redis)},
        status_code=status[1]
    )

    return response


async def _worker_health(redis: AsyncRedisSession) -> dict[str, Any]:
    """Worker state for people reading /health, it never changes the status of the app itself."""
    try:
        alive = await is_worker_alive(redis)
        syncs = await get_sync_statuses(redis)
    except Exception as exc:
        logger.warning(f"Worker state is unavailable: {exc}")
        return {}

    return {
        "worker": "up" if alive else "down",
        "syncs": {
            job: {field: run[field] for field in _PUBLIC_SYNC_FIELDS if run.get(field) is not None}
            for job, run in sorted(syncs.items())
        },
    }
