from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep
from . import service

router = APIRouter(prefix="/check-in", tags=["check-in"])

@router.post("/")
async def create_checkin(db: AsyncDBDep, reset: bool = False):
    return await service.create_random_checkin(db, reset)