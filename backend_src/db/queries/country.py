from typing import Optional

from shapely.geometry import MultiPolygon
from geoalchemy2.functions import ST_Intersects, ST_MakePoint, ST_SetSRID
from sqlalchemy import delete, exists, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend_src.db import AsyncDBSession
from backend_src.models import Country, CountryBorder, CountryBorderPart, GeoZone


# Vertices per border part: fewer make more rows but a cheaper exact check of each
SUBDIVIDE_MAX_VERTICES = 256


async def get_supported_countries(db: AsyncDBSession) -> list[Country]:
    """Countries with a synced border and geo-zones, i.e. where a check-in can be verified."""
    result = await db.execute(
        select(Country)
        .join(CountryBorder, CountryBorder.country_id == Country.id)
        .where(exists().where(GeoZone.country_id == Country.id))
        .order_by(Country.id)
    )

    return list(result.scalars().all())


async def get_by_coordinates(lon: float, lat: float, db: AsyncDBSession) -> Optional[Country]:
    """Country whose synced border covers the point, None outside every synced border."""
    # neighbour borders may overlap by a few metres, the lowest id keeps the answer stable there
    result = await db.execute(
        select(Country)
        .join(CountryBorderPart, CountryBorderPart.country_id == Country.id)
        .where(
            ST_Intersects(CountryBorderPart.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
        )
        .order_by(Country.id)
        .limit(1)
    )

    return result.scalars().first()


async def get_by_tag(tag: str, db: AsyncDBSession) -> Optional[Country]:
    result = await db.execute(select(Country).where(Country.country_tag == tag))

    return result.scalar_one_or_none()


async def upsert_border(country_id: int, border: MultiPolygon, source: str, db: AsyncDBSession) -> None:
    statement = pg_insert(CountryBorder).values(country_id=country_id, border_polygon=border, source=source)

    await db.execute(
        statement.on_conflict_do_update(
            index_elements=[CountryBorder.country_id],
            set_={
                "border_polygon": statement.excluded.border_polygon,
                "source": statement.excluded.source,
                "uploaded_at": func.now(),
            },
        )
    )


async def rebuild_parts(country_id: int, db: AsyncDBSession) -> int:
    """Cuts the stored border into parts for the point lookup, returns how many parts were made."""
    await db.execute(delete(CountryBorderPart).where(CountryBorderPart.country_id == country_id))

    parts = (
        select(
            CountryBorder.country_id,
            func.ST_Multi(func.ST_Subdivide(CountryBorder.border_polygon, SUBDIVIDE_MAX_VERTICES)),
        )
        .where(CountryBorder.country_id == country_id)
    )
    result = await db.execute(
        insert(CountryBorderPart).from_select([CountryBorderPart.country_id, CountryBorderPart.geom], parts)
    )

    return result.rowcount # type: ignore
