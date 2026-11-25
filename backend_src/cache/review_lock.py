from dataclasses import dataclass

from .client import AsyncRedisSession
from .keys import review_lock_key


# Takes a free lock or extends the caller's own one, otherwise reports who holds it and for how long
_ACQUIRE_SCRIPT = """
local holder = redis.call("get", KEYS[1])
if not holder or holder == ARGV[1] then
    redis.call("set", KEYS[1], ARGV[1], "EX", ARGV[2])
    return {1, ARGV[1], tonumber(ARGV[2])}
end
return {0, holder, redis.call("ttl", KEYS[1])}
"""

# Deletes the lock only while the caller holds it, a lock of another moderator stays
_RELEASE_SCRIPT = """
local holder = redis.call("get", KEYS[1])
if not holder or holder == ARGV[1] then
    redis.call("del", KEYS[1])
    return 1
end
return 0
"""


@dataclass(frozen=True)
class ReviewLock:
    taken: bool
    holder_id: int
    expires_in: int


async def acquire_review_lock(
    redis: AsyncRedisSession, kind: str, item_id: int, moderator_id: int, ttl_seconds: int
) -> ReviewLock:
    """Takes or extends the moderator's lock on the item; taken is False while another moderator holds it."""
    taken, holder, ttl = await redis.eval( # type: ignore[misc]
        _ACQUIRE_SCRIPT, 1, review_lock_key(kind, item_id), str(moderator_id), ttl_seconds
    )

    return ReviewLock(taken=bool(taken), holder_id=int(holder), expires_in=int(ttl))


async def release_review_lock(redis: AsyncRedisSession, kind: str, item_id: int, moderator_id: int) -> bool:
    """False when another moderator holds the lock, a missing lock counts as released."""
    released = await redis.eval(_RELEASE_SCRIPT, 1, review_lock_key(kind, item_id), str(moderator_id)) # type: ignore[misc]

    return bool(released)


async def get_review_holds(redis: AsyncRedisSession, kind: str, item_ids: list[int]) -> dict[int, ReviewLock]:
    """Locks of the items held by a moderator right now, a free item is left out."""
    if not item_ids:
        return {}

    async with redis.pipeline(transaction=False) as pipe:
        for item_id in item_ids:
            pipe.get(review_lock_key(kind, item_id))
            pipe.ttl(review_lock_key(kind, item_id))
        values = await pipe.execute()

    return {
        item_id: ReviewLock(taken=True, holder_id=int(holder), expires_in=int(ttl))
        for item_id, holder, ttl in zip(item_ids, values[0::2], values[1::2])
        if holder is not None and ttl > 0
    }
