from typing import Optional

from sqlalchemy import Integer, LargeBinary, Row, func, insert, literal, select, text, true
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope, ST_MakePoint, ST_SetSRID

from backend_src.db import AsyncDBSession
from backend_src.models import Dem, GeoZone


# A 1° tile has up to 1200 x 1200 pixels, smaller rasters keep the spatial index selective
_RASTER_SIZE_PX = 100


async def get_elevation_m(lon: float, lat: float, db: AsyncDBSession) -> Optional[float]:
    """Ground elevation at the point interpolated from the four nearest pixels, None outside the stored tiles."""
    point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    # a point on the edge between rasters touches several of them, the higher value is the safer one
    result = await db.execute(
        select(func.max(func.ST_Value(Dem.rast, 1, point, True, "bilinear")))
        .where(ST_Intersects(Dem.rast, point))
    )

    return result.scalar_one_or_none()


async def measure_zone_terrain(db: AsyncDBSession) -> int:
    """Stores the highest ground of zones that need it and have none yet, returns how many zones got it.

    Only zones starting above ground or with activity windows need it: the rest restrict flights from the ground.
    Every pixel the polygon touches counts, so small zones get a value too; some PANSA polygons
    intersect themselves and are made valid before clipping.
    """
    result = await db.execute(text("""
        UPDATE geo_zone AS z
        SET terrain_max_m = m.terrain_max_m
        FROM (
            SELECT z.id, (ST_SummaryStatsAgg(ST_Clip(d.rast, ST_MakeValid(z.zone_polygon), true, true), 1, true)).max AS terrain_max_m
            FROM geo_zone AS z
            JOIN dem AS d ON ST_Intersects(d.rast, z.zone_polygon)
            WHERE z.terrain_max_m IS NULL
              AND (z.lower_limit_ft > 0 OR z.activity_mode <> 'permanent')
            GROUP BY z.id
        ) AS m
        WHERE z.id = m.id AND m.terrain_max_m IS NOT NULL
    """))

    return result.rowcount # type: ignore


async def get_stored_tiles(db: AsyncDBSession) -> set[str]:
    result = await db.execute(select(Dem.tile).distinct())

    return set(result.scalars().all())


async def add_tile(tile: str, geotiff: bytes, db: AsyncDBSession) -> None:
    """Stores a GeoTIFF tile cut into rasters. PostGIS reads it with GDAL, so its GTiff driver must be enabled."""
    raster = func.ST_FromGDALRaster(literal(geotiff, LargeBinary), 4326)

    await db.execute(
        insert(Dem).from_select(
            ["tile", "rast"],
            select(literal(tile), func.ST_Tile(raster, _RASTER_SIZE_PX, _RASTER_SIZE_PX)),
        )
    )


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
