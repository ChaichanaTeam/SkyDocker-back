from fastapi import APIRouter, Query
from pydantic import EmailStr

from backend_src.api.dependencies import AsyncDBDep
from . import service


router = APIRouter(prefix="/drone-park", tags=["drone-park"])


@router.post("/models/seed")
async def seed_models(db: AsyncDBDep):
    return await service.seed_models(db)


@router.post("/random")
async def create_random_drones(
    db: AsyncDBDep,
    email: EmailStr = Query(description="Email of an existing pilot"),
    count: int = Query(default=1, ge=1, le=100),
):
    return await service.create_random_drones(db, email, count)
