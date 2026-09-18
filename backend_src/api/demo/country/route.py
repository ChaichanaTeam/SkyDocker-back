from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep
from . import docs
from . import service


router = APIRouter(prefix="/country", tags=["country"])


@router.get("/", **docs.CREATE_COUNTRIES)
async def create(db: AsyncDBDep):
    return await service.create_countries(db)
