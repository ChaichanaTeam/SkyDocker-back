from fastapi import APIRouter, Query

from backend_src.api.shared_schemas import BoundingBox
from backend_src.api.dependencies import AsyncDBDep
from . import docs
from . import service


router = APIRouter(prefix="/check-in")


@router.get("/", **docs.CHECKIN_BBOX)
async def checkin_bbox(db: AsyncDBDep, bbox: BoundingBox = Query(...)):
    return await service.checkin_bbox(bbox, db)