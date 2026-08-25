from fastapi import APIRouter

from . import docs
from . import service


router = APIRouter(tags=["base"])


@router.get("/health", **docs.HEALTH)
async def health():
    return await service.health()
