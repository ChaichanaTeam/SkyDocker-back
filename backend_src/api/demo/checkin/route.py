from fastapi import APIRouter, Query

from backend_src.api.dependencies import AsyncDBDep, BoundingBoxQuery, CountryQuery
from . import docs
from . import service
from .schema import CheckinInput


router = APIRouter(prefix="/check-in", tags=["check-in"])


@router.post("/", **docs.CREATE_CHECKIN)
async def create_checkin(data: CheckinInput, db: AsyncDBDep):
    return await service.create_checkin(db, data)


@router.post("/random", **docs.CREATE_RANDOM_CHECKINS)
async def create_random_checkins(
    db: AsyncDBDep,
    count: int = Query(default=1, ge=1, le=500),
    reset: bool = False,
):
    return await service.create_random_checkins(db, count, reset)


@router.post("/{checkin_id}/end", **docs.END_CHECKIN)
async def end_checkin(checkin_id: int, db: AsyncDBDep):
    return await service.end_checkin(db, checkin_id)


@router.get("/bbox", **docs.CHECKIN_BBOX)
async def checkins_in_bbox(bbox: BoundingBoxQuery, country: CountryQuery, db: AsyncDBDep):
    return await service.checkins_in_bbox(bbox, country.id, db)
