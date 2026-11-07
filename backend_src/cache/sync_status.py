import json
from datetime import datetime, timezone
from typing import Any, Optional

from .client import AsyncRedisSession
from .keys import sync_status_key, worker_heartbeat_key


async def save_sync_status(redis: AsyncRedisSession, job: str, status: dict[str, Any]) -> None:
    await redis.hset(sync_status_key(), job, json.dumps(status, default=str)) # type: ignore[misc]


async def get_sync_status(redis: AsyncRedisSession, job: str) -> Optional[dict[str, Any]]:
    stored = await redis.hget(sync_status_key(), job) # type: ignore[misc]
    return json.loads(stored) if stored else None


async def get_sync_statuses(redis: AsyncRedisSession) -> dict[str, dict[str, Any]]:
    """Last run of every sync that ran at least once, by job name."""
    stored = await redis.hgetall(sync_status_key()) # type: ignore[misc]
    return {_text(job): json.loads(status) for job, status in stored.items()}


async def beat_worker_heartbeat(redis: AsyncRedisSession, ttl_seconds: int) -> None:
    await redis.set(worker_heartbeat_key(), datetime.now(timezone.utc).isoformat(), ex=ttl_seconds)


async def is_worker_alive(redis: AsyncRedisSession) -> bool:
    return bool(await redis.exists(worker_heartbeat_key()))


def _text(value: Any) -> str:
    # clients without decode_responses return bytes
    return value.decode() if isinstance(value, bytes) else value
