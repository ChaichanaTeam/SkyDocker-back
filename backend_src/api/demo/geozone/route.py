from fastapi import APIRouter, File, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from . import docs
from . import service


router = APIRouter(prefix="/geo-zone", tags=["geo-zone"])


@router.post("/", **docs.IMPORT_GEOZONES)
async def import_geozones(
    db: AsyncDBDep,
    file: UploadFile = File(...),
    reset: bool = False,
):
    return await service.import_geozones(db, file, reset)
