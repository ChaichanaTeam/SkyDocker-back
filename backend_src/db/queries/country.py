from typing import Optional

from shapely.geometry import MultiPolygon
from sqlalchemy import delete, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend_src.db import AsyncDBSession
from backend_src.models import Country, CountryBorder, CountryBorderPart


# Vertices per border part: fewer make more rows but a cheaper exact check of each
SUBDIVIDE_MAX_VERTICES = 256


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
