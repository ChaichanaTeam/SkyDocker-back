from typing import Annotated
from fastapi import APIRouter, Query

from backend_src.api.dependencies import AdminKey, AsyncDBDep
from .schema import FlightPoint, MapArea
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone")

MapAreaQuery = Annotated[MapArea, Query()]
FlightPointQuery = Annotated[FlightPoint, Query()]


@router.get("/", **docs.GEOZONE_BBOX)
async def geozone_bbox(area: MapAreaQuery, db: AsyncDBDep):
    return await service.geozone_bbox(area, db)


@router.get("/point", **docs.GEOZONE_POINT)
async def geozone_point(point: FlightPointQuery, db: AsyncDBDep):
    return await service.geozone_point(point, db)


@router.post("/sync", dependencies=[AdminKey], **docs.GEOZONE_SYNC)
async def geozone_sync(db: AsyncDBDep):
    return await service.sync_catalog(db)


@router.post("/activity/sync", dependencies=[AdminKey], **docs.GEOZONE_ACTIVITY_SYNC)
async def geozone_activity_sync(db: AsyncDBDep):
    return await service.sync_activity(db)


@router.post("/terrain/sync", dependencies=[AdminKey], **docs.GEOZONE_TERRAIN_SYNC)
async def geozone_terrain_sync(db: AsyncDBDep):
    return await service.sync_terrain(db)
