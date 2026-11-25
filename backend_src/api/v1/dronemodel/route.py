from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep, CurrentModerator, CurrentPilot
from .schema import ModelCorrection, ModelReplacement
from . import docs
from . import service


router = APIRouter(prefix="/drone-models", **docs.ROUTER)


@router.get("/", **docs.GET_CATALOG)
async def get_catalog(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_catalog(db)


@router.get("/unverified", **docs.LIST_UNVERIFIED)
async def list_unverified(moderator: CurrentModerator, db: AsyncDBDep):
    return await service.list_unverified(db)


@router.post("/{model_id}/approve", **docs.APPROVE)
async def approve(model_id: int, correction: ModelCorrection, moderator: CurrentModerator, db: AsyncDBDep):
    return await service.approve(model_id, correction, db)


@router.post("/{model_id}/replace", **docs.REPLACE)
async def replace(model_id: int, replacement: ModelReplacement, moderator: CurrentModerator, db: AsyncDBDep):
    return await service.replace(model_id, replacement, db)


@router.delete("/{model_id}", **docs.DELETE)
async def delete(model_id: int, moderator: CurrentModerator, db: AsyncDBDep):
    return await service.delete(model_id, db)
