from fastapi import FastAPI
from redis_fastapi import AsyncRedisDep, FastAPIRedis


def init_redis(app: FastAPI) -> None:
    redis = FastAPIRedis(app)
    redis.lifespan().rate_limiting()
