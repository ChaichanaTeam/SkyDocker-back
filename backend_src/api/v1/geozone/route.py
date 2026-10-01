from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep, BoundingBoxQuery
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone")


@router.get("/", **docs.GEOZONE_BBOX)
async def geozone_bbox(bbox: BoundingBoxQuery, db: AsyncDBDep):
    return await service.geozone_bbox(bbox, db)