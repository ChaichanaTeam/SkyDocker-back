from fastapi import APIRouter

from backend_src.api.dependencies import AsyncDBDep
from backend_src.api.shared_schemas import  UserGeoData
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone")


@router.get("/", **docs.GEOZONE_BBOX)
async def geozone_bbox(data: UserGeoData, db: AsyncDBDep):
    return await service.geozone_bbox(data, db)