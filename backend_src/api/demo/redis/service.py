from redis_fastapi import AsyncRedisDep


async def redis_get(redis: AsyncRedisDep):
    result = await redis.get("test_key")
    return {
        "message": f"Redis returned {result}" if result else "To get the result, please set the value first using the POST method."
    }


async def redis_set(redis: AsyncRedisDep):
    result = await redis.set("test_key", "test_value", nx=True)

    return {
        "message": "Redis set the value successfully" if result else "Redis already has a value for this key. Please use the GET method to retrieve it."
    }