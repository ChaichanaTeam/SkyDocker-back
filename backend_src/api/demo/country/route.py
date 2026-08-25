from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep
from . import service


router = APIRouter(prefix="/country", tags=["country"])


@router.get("/")
async def create(db: AsyncDBDep):
    return await service.create_country(db)