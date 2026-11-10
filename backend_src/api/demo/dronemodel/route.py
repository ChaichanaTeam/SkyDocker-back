from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep
from . import docs
from . import service


router = APIRouter(prefix="/drone-models", tags=["drone-models"])


@router.get("/unverified", **docs.LIST_UNVERIFIED)
async def list_unverified(db: AsyncDBDep):
    return await service.list_unverified(db)
