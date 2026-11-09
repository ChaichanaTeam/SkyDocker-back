import asyncio

from fakeredis import FakeAsyncRedis

from backend_src.cache import acquire_sync_lock, release_sync_lock


def test_lock_is_taken_once():
    async def scenario():
        redis = FakeAsyncRedis()
        return await acquire_sync_lock(redis, "geo-zone", 60), await acquire_sync_lock(redis, "geo-zone", 60)

    first, second = asyncio.run(scenario())
    assert first is not None, "A free lock must be taken"
    assert second is None, "A held lock must not be taken again"


def test_locks_are_separate():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_sync_lock(redis, "geo-zone", 60)
        return await acquire_sync_lock(redis, "border:PL", 60)

    assert asyncio.run(scenario()) is not None, "A border sync must not wait for a geo-zone sync"


def test_only_owner_releases():
    async def scenario():
        redis = FakeAsyncRedis()
        token = await acquire_sync_lock(redis, "geo-zone", 60)
        assert token is not None

        await release_sync_lock(redis, "geo-zone", "token-of-another-run")
        taken_after_foreign_release = await acquire_sync_lock(redis, "geo-zone", 60)

        await release_sync_lock(redis, "geo-zone", token)
        taken_after_own_release = await acquire_sync_lock(redis, "geo-zone", 60)
        return taken_after_foreign_release, taken_after_own_release

    after_foreign, after_own = asyncio.run(scenario())
    assert after_foreign is None, "A run must not release a lock it does not hold, e.g. after its TTL ran out"
    assert after_own is not None, "The owner must be able to release its lock"


def test_lock_expires():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_sync_lock(redis, "geo-zone", 60)
        return await redis.ttl("sync:lock:geo-zone")

    ttl = asyncio.run(scenario())
    assert 0 < ttl <= 60, f"A lock must expire, so a crashed run does not block syncs forever: ttl {ttl}"
