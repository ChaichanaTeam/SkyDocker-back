from fastapi import FastAPI
from redis_fastapi import AsyncRedisDep, FastAPIRedis

__all__ = ["AsyncRedisDep", "init_redis"]


def init_redis(app: FastAPI) -> None:
    """Attach Redis to the FastAPI app and register its lifespan hooks."""
    redis = FastAPIRedis(app)
    redis.lifespan()
