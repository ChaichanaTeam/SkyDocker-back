from typing import Optional

from sqlalchemy import Row, select
from sqlalchemy.orm import joinedload
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from backend_src.db import AsyncDBSession
from backend_src.models import Country, GeoZone


async def get_all_by_bbox(x1: float, y1: float, x2: float, y2: float, db: AsyncDBSession) -> list[GeoZone]:
    result = await db.execute(
        select(GeoZone)
        .where(ST_Intersects(GeoZone.zone_polygon, ST_MakeEnvelope(x1, y1, x2, y2, 4326)))
        .options(joinedload(GeoZone.country))
    )

    return result.scalars().all() # type: ignore


async def get_country_by_tag(tag: str, db: AsyncDBSession) -> Optional[Country]:
    result = await db.execute(select(Country).where(Country.country_tag == tag))

    return result.scalar_one_or_none()


async def get_sync_states(country_id: int, db: AsyncDBSession) -> list[Row]:
    """Fields the sync compares, without geometry and descriptions."""
    result = await db.execute(
        select(
            GeoZone.id, GeoZone.external_id, GeoZone.parent_id, GeoZone.tag, GeoZone.type,
            GeoZone.source_type, GeoZone.activity_mode, GeoZone.source_modified_at,
        )
        .where(GeoZone.country_id == country_id)
    )

    return list(result.all())
