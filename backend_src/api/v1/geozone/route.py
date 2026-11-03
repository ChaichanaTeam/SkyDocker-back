from typing import Annotated
from fastapi import APIRouter, Query

from backend_src.api.dependencies import AdminKey, AsyncDBDep, CountryQuery, CoordinateQuery, CurrentPilot
from .schema import FlightPoint, MapArea
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone", tags=["geo-zone"])

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


@router.post("/border/sync", dependencies=[AdminKey], **docs.GEOZONE_BORDER_SYNC)
async def geozone_border_sync(country: CountryQuery, db: AsyncDBDep):
    return await service.sync_border(country, db)


@router.get("/country", **docs.GEOZONE_GET_COUNTRY)
async def geozone_get_country(coordinates: CoordinateQuery, db: AsyncDBDep, pilot: CurrentPilot):
    return await service.geozone_get_country(coordinates, db)


@router.get("/country/supported", **docs.GEOZONE_GET_COUNTRY_SUPPORTED)
async def geozone_get_country_supported(db: AsyncDBDep, pilot: CurrentPilot):
    return await service.geozone_get_country_supported(db)
