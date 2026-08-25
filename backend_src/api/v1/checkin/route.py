from fastapi import APIRouter

from backend_src.api.shared_schemas import UserGeoData
from backend_src.api.dependencies import AsyncDBDep
from . import docs
from . import service


router = APIRouter(prefix="/check-in")


@router.get("/", **docs.CHECKIN_BBOX)
async def checkin_bbox(data: UserGeoData, db: AsyncDBDep):
    return await service.checkin_bbox(data, db)