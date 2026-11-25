from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from backend_src.models import MissionStatus
from . import docs
from . import service


router = APIRouter(prefix="/mission", tags=["mission"])


@router.post("/", **docs.IMPORT_MISSIONS)
async def import_missions(db: AsyncDBDep, file: UploadFile = File(...)):
    return await service.import_missions(db, file)


@router.get("/", **docs.LIST_MISSIONS)
async def list_missions(
    db: AsyncDBDep,
    status: Optional[MissionStatus] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_missions(db, status, limit, offset)

