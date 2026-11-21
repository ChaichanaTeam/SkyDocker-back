from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep, CurrentPilot
from . import docs
from . import service


router = APIRouter(prefix="/drone-models", **docs.ROUTER)


@router.get("/", **docs.GET_CATALOG)
async def get_catalog(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_catalog(db)
