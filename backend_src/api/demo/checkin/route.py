from fastapi import APIRouter, Query

from backend_src.api.dependencies import AsyncDBDep
from . import service

router = APIRouter(prefix="/check-in", tags=["check-in"])

@router.post("/")
async def create_checkin(
    db: AsyncDBDep, count: int = Query(default=1, ge=1, le=100), reset: bool = False):
    return await service.create_random_checkins(db, count, reset)