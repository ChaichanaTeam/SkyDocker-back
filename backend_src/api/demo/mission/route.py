from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import BoundingBox
from . import service


router = APIRouter(prefix="/mission", tags=["mission"])


@router.post("/")
async def import_missions(
    db: AsyncDBDep,
    file: Optional[UploadFile] = File(default=None),
    reset: bool = False,
):
    if file is None:
        return await service.import_bundled_missions(db, reset)

    return await service.import_missions(db, await file.read(), reset)


@router.get("/")
async def list_missions(
    db: AsyncDBDep,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_missions(db, limit, offset)


@router.get("/bbox")
async def missions_in_bbox(data: BoundingBox, db: AsyncDBDep):
    return await service.missions_in_bbox(data, db)
