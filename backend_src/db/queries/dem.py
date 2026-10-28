from sqlalchemy import Integer, Row, func, select, true
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from backend_src.db import AsyncDBSession
from backend_src.models import GeoZone


async def get_cells_covering_geo_zones(db: AsyncDBSession) -> list[Row]:
    """South-west corners (lat, lon) of the 1° x 1° DEM cells that intersect at least one geo-zone."""
    extent = select(func.ST_Extent(GeoZone.zone_polygon)).scalar_subquery()
    lat = select(
        func.generate_series(func.floor(func.ST_YMin(extent)).cast(Integer), func.ceil(func.ST_YMax(extent)).cast(Integer) - 1)
        .label("lat")
    ).subquery()
    lon = select(
        func.generate_series(func.floor(func.ST_XMin(extent)).cast(Integer), func.ceil(func.ST_XMax(extent)).cast(Integer) - 1)
        .label("lon")
    ).subquery()

    cell = ST_MakeEnvelope(lon.c.lon, lat.c.lat, lon.c.lon + 1, lat.c.lat + 1, 4326)
    result = await db.execute(
        select(lat.c.lat, lon.c.lon)
        .select_from(lat.join(lon, true()))
        .where(select(GeoZone.id).where(ST_Intersects(GeoZone.zone_polygon, cell)).exists())
        .order_by(lat.c.lat, lon.c.lon)
    )

    return list(result.all())
