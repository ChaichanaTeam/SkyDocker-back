from typing import Union
from fastapi import FastAPI
from redis_fastapi import FastAPIRedis
from redis.asyncio import Redis, RedisCluster


def init_redis(app: FastAPI) -> None:
    redis = FastAPIRedis(app)
    redis.lifespan().rate_limiting()


AsyncRedisSession = Union[Redis, RedisCluster]