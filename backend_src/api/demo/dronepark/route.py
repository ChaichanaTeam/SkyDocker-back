from fastapi import APIRouter, Query

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import NormalizedEmailStr
from . import service


router = APIRouter(prefix="/drone-park", tags=["drone-park"])


@router.post("/models/seed")
async def seed_models(db: AsyncDBDep):
    return await service.seed_models(db)


@router.post("/random")
async def create_random_drones(
    db: AsyncDBDep,
    email: NormalizedEmailStr = Query(description="Email of an existing pilot"),
    count: int = Query(default=1, ge=1, le=100),
):
    return await service.create_random_drones(db, email, count)
