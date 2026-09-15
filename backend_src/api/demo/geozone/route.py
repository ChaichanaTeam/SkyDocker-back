from fastapi import APIRouter, File, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from . import service


router = APIRouter(prefix="/geo-zone", tags=["geo-zone"])


@router.post("/")
async def import_geozones(
    db: AsyncDBDep,
    file: UploadFile = File(...),
    reset: bool = False,
):
    return await service.import_geozones(db, await file.read(), reset)
