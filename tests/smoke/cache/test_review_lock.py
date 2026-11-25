import asyncio

from fakeredis import FakeAsyncRedis

from backend_src.cache import acquire_review_lock, release_review_lock


KIND = "verification"
FIRST, SECOND = 1, 2


def test_free_lock_is_taken():
    lock = asyncio.run(acquire_review_lock(FakeAsyncRedis(), KIND, 10, FIRST, 300))

    assert lock.taken, "A free request must be locked to the moderator who opens it"
    assert lock.holder_id == FIRST
    assert lock.expires_in == 300


def test_own_lock_is_extended():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_review_lock(redis, KIND, 10, FIRST, 60)
        return await acquire_review_lock(redis, KIND, 10, FIRST, 300), await redis.ttl("review:lock:verification:10")

    lock, ttl = asyncio.run(scenario())
    assert lock.taken, "The moderator who holds the lock must be able to open the request again"
    assert 60 < ttl <= 300, f"Opening the request again must extend the lock: ttl {ttl}"


def test_another_moderator_is_refused():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_review_lock(redis, KIND, 10, FIRST, 300)
        return await acquire_review_lock(redis, KIND, 10, SECOND, 300), await redis.get("review:lock:verification:10")

    lock, holder = asyncio.run(scenario())
    assert not lock.taken, "A request locked by one moderator must not be opened by another"
    assert lock.holder_id == FIRST, "The refused moderator must learn who reviews the request"
    assert 0 < lock.expires_in <= 300, f"The refused moderator must learn when the lock runs out: {lock.expires_in}"
    assert holder == str(FIRST).encode(), "A refused attempt must not take over the lock"


def test_only_holder_releases():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_review_lock(redis, KIND, 10, FIRST, 300)

        foreign = await release_review_lock(redis, KIND, 10, SECOND)
        taken_after_foreign = (await acquire_review_lock(redis, KIND, 10, SECOND, 300)).taken

        own = await release_review_lock(redis, KIND, 10, FIRST)
        taken_after_own = (await acquire_review_lock(redis, KIND, 10, SECOND, 300)).taken
        return foreign, taken_after_foreign, own, taken_after_own

    foreign, after_foreign, own, after_own = asyncio.run(scenario())
    assert not foreign and not after_foreign, "A moderator must not release the lock of another one"
    assert own and after_own, "The holder must be able to release the lock for others"


def test_releasing_free_lock_succeeds():
    assert asyncio.run(release_review_lock(FakeAsyncRedis(), KIND, 10, FIRST)), "Releasing a free request must succeed"


def test_locks_are_separate():
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_review_lock(redis, KIND, 10, FIRST, 300)
        return (
            await acquire_review_lock(redis, KIND, 11, SECOND, 300),
            await acquire_review_lock(redis, "drone_model", 10, SECOND, 300),
        )

    other_request, other_kind = asyncio.run(scenario())
    assert other_request.taken, "A lock must hold only its own request"
    assert other_kind.taken, "A request lock must not hold an item of another kind with the same id"
