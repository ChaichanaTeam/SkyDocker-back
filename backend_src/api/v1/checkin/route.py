from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep, BoundingBoxQuery
from . import docs
from . import service


router = APIRouter(prefix="/check-in")


@router.get("/", **docs.CHECKIN_BBOX)
async def checkin_bbox(bbox: BoundingBoxQuery, db: AsyncDBDep):
    return await service.checkin_bbox(bbox, db)