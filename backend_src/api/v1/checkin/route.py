from fastapi import APIRouter, status

from backend_src.api.dependencies import AsyncDBDep, BoundingBoxQuery, CountryQuery, CurrentPilot
from .schema import CheckinCreateRequest, CheckinPreviewRequest
from . import docs
from . import service


router = APIRouter(prefix="/check-in", **docs.ROUTER)


@router.get("/", **docs.CHECKIN_BBOX)
async def checkin_bbox(bbox: BoundingBoxQuery, country: CountryQuery,  db: AsyncDBDep, pilot: CurrentPilot):
    return await service.checkin_bbox(bbox, country, db)


@router.post("/preview", **docs.CHECKIN_PREVIEW)
async def checkin_preview(data: CheckinPreviewRequest, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.checkin_preview(data, pilot, db)


@router.post("/", status_code=status.HTTP_201_CREATED, **docs.CHECKIN_CREATE)
async def checkin_create(data: CheckinCreateRequest, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.checkin_create(data, pilot, db)


@router.post("/end", **docs.CHECKIN_END)
async def checkin_end(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.checkin_end(pilot, db)
