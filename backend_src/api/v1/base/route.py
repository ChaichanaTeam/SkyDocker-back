from fastapi import APIRouter
from redis_fastapi import AsyncRedisDep

from . import docs
from . import service


router = APIRouter(tags=["base"])


@router.get("/health", **docs.HEALTH)
async def health(redis: AsyncRedisDep):
    return await service.health(redis)
