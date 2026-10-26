from fastapi import APIRouter

from backend_src.api.dependencies import AdminKey, AsyncDBDep, BoundingBoxQuery
from . import service
from . import docs


router = APIRouter(prefix="/geo-zone")


@router.get("/", **docs.GEOZONE_BBOX)
async def geozone_bbox(bbox: BoundingBoxQuery, db: AsyncDBDep):
    return await service.geozone_bbox(bbox, db)


@router.post("/sync", dependencies=[AdminKey], **docs.GEOZONE_SYNC)
async def geozone_sync(db: AsyncDBDep):
    return await service.sync_catalog(db)


@router.post("/activity/sync", dependencies=[AdminKey], **docs.GEOZONE_ACTIVITY_SYNC)
async def geozone_activity_sync(db: AsyncDBDep):
    return await service.sync_activity(db)
