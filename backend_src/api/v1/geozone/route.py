from fastapi import APIRouter, Query

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import BoundingBox
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone")


@router.get("/", **docs.GEOZONE_BBOX)
async def geozone_bbox(db: AsyncDBDep, bbox: BoundingBox = Query(...)):
    return await service.geozone_bbox(bbox, db)