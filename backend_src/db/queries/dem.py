from sqlalchemy import Integer, LargeBinary, Row, func, insert, literal, select, true
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from backend_src.db import AsyncDBSession
from backend_src.models import Dem, GeoZone


# A 1° tile has up to 1200 x 1200 pixels, smaller rasters keep the spatial index selective
_RASTER_SIZE_PX = 100


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
