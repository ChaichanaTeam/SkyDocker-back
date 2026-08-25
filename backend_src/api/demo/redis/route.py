from fastapi import APIRouter
from redis_fastapi import AsyncRedisDep

from . import service


router = APIRouter(prefix="/redis", tags=["Redis"])


@router.get("/")
async def redis_get(redis: AsyncRedisDep):
    return await service.redis_get(redis)


@router.post("/")
async def redis_set(redis: AsyncRedisDep):
    return await service.redis_set(redis)