from typing import Optional
from uuid import uuid4

from .client import AsyncRedisSession
from .keys import sync_lock_key


# Deletes the lock only while it still holds our token: after its TTL ran out it may belong to another run
_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


async def acquire_sync_lock(redis: AsyncRedisSession, name: str, ttl_seconds: int) -> Optional[str]:
    """Token of the taken lock, None while another run holds it."""
    token = uuid4().hex
    taken = await redis.set(sync_lock_key(name), token, nx=True, ex=ttl_seconds)

    return token if taken else None


async def release_sync_lock(redis: AsyncRedisSession, name: str, token: str) -> None:
    await redis.eval(_RELEASE_SCRIPT, 1, sync_lock_key(name), token) # type: ignore[misc]
