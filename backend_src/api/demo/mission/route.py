from fastapi import APIRouter, File, Query, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import BoundingBox
from . import docs
from . import service


router = APIRouter(prefix="/mission", tags=["mission"])


@router.post("/", **docs.IMPORT_MISSIONS)
async def import_missions(
    db: AsyncDBDep,
    file: UploadFile = File(...),
    reset: bool = False,
):
    return await service.import_missions(db, file, reset)


@router.get("/", **docs.LIST_MISSIONS)
async def list_missions(
    db: AsyncDBDep,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_missions(db, limit, offset)


@router.get("/bbox", **docs.MISSION_BBOX)
async def missions_in_bbox(data: BoundingBox, db: AsyncDBDep):
    return await service.missions_in_bbox(data, db)
