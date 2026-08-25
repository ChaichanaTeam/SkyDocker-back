from shapely.geometry import mapping

from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from backend_src.api.shared_schemas import GeoJson, GeoFeature
from backend_src.api.shared_schemas import UserGeoData
from .schema import GeozoneProperties


async def geozone_bbox(data: UserGeoData, db: AsyncDBSession):
    geozones = await Queries.GeoZone.get_all_by_bbox(*data.bounding_box.unpack(), db)

    if len(geozones) == 0:
        raise APIExceptions.not_found("No zones in this region")

    features: list[GeoFeature] = [
        GeoFeature(geometry=mapping(gz.zone_polygon), properties=GeozoneProperties.from_geozone(gz)) for gz in geozones
    ]

    return GeoJson(
        features=features
    )