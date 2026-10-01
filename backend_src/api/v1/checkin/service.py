from shapely.geometry import mapping

from backend_src.api.shared_schemas import GeoJson, GeoFeature, BoundingBox
from backend_src.db import Queries, AsyncDBSession
from backend_src.api.exceptions import APIExceptions
from .schema import CheckinProperties


async def checkin_bbox(bbox: BoundingBox, db: AsyncDBSession):
    checkins = await Queries.Checkin.get_all_by_bbox(*bbox.unpack(), db)
    
    if len(checkins) == 0:
        raise APIExceptions.not_found("No checkins in this region")

    features: list[GeoFeature] = [
        GeoFeature(geometry=mapping(ch.home_point), properties=CheckinProperties.from_checkin(ch)) for ch in checkins
    ]

    return GeoJson(
        features=features
    )