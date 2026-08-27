from typing import Optional

from fastapi import APIRouter, File, UploadFile

from backend_src.api.dependencies import AsyncDBDep
from . import service


router = APIRouter(prefix="/geo-zone", tags=["geo-zone"])


@router.post("/")
async def import_geozones(
    db: AsyncDBDep,
    file: Optional[UploadFile] = File(default=None),
    reset: bool = False,
):

    if file is None:
        return await service.import_bundled_geozones(db, reset)

    return await service.import_geozones(db, await file.read(), reset)
