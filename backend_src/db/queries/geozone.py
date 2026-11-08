from datetime import datetime
from typing import Collection

from sqlalchemy import Row, cast, select
from sqlalchemy.orm import joinedload
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Intersects, ST_MakeEnvelope, ST_MakePoint, ST_SetSRID

from backend_src.db import AsyncDBSession
from backend_src.models import ActivityTime, GeoZone


async def get_all_by_bbox(x1: float, y1: float, x2: float, y2: float, country_id: int, db: AsyncDBSession) -> list[GeoZone]:
    result = await db.execute(
        select(GeoZone)
        .where(
            GeoZone.country_id == country_id,
            ST_Intersects(GeoZone.zone_polygon, ST_MakeEnvelope(x1, y1, x2, y2, 4326))
        )
        .options(joinedload(GeoZone.country))
    )

    return result.scalars().all() # type: ignore


async def get_all_at_point(lon: float, lat: float, below_ft: int, country_id: int, db: AsyncDBSession) -> list[GeoZone]:
    """Zones over the point whose lower limit is below ``below_ft`` above mean sea level."""
    result = await db.execute(
        select(GeoZone)
        .where(
            GeoZone.country_id == country_id,
            ST_Intersects(GeoZone.zone_polygon, ST_SetSRID(ST_MakePoint(lon, lat), 4326)),
            GeoZone.lower_limit_ft < below_ft,
        )
        .options(joinedload(GeoZone.country))
    )

    return list(result.scalars().all())


async def get_all_in_radius(lon: float, lat: float, radius_m: int, below_ft: int, country_id: int, db: AsyncDBSession) -> list[GeoZone]:
    """Zones within ``radius_m`` of the point whose lower limit is below ``below_ft`` above mean sea level."""
    geography = Geography(srid=4326)
    point = cast(ST_SetSRID(ST_MakePoint(lon, lat), 4326), geography)
    result = await db.execute(
        select(GeoZone)
        .where(
            GeoZone.country_id == country_id,
            ST_DWithin(cast(GeoZone.zone_polygon, geography), point, radius_m),
            GeoZone.lower_limit_ft < below_ft,
        )
        .options(joinedload(GeoZone.country))
    )

    return list(result.scalars().unique().all())


async def get_windows_ending_after(zone_ids: Collection[int], moment: datetime, db: AsyncDBSession) -> list[ActivityTime]:
    if not zone_ids:
        return []

    result = await db.execute(
        select(ActivityTime)
        .where(ActivityTime.geo_zone_id.in_(zone_ids), ActivityTime.ends_at > moment)
        .order_by(ActivityTime.start_at)
    )

    return list(result.scalars().all())


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


async def get_activity_targets(country_id: int, db: AsyncDBSession) -> list[Row]:
    """Zones activity windows can be matched to by name."""
    result = await db.execute(
        select(GeoZone.id, GeoZone.tag, GeoZone.activity_mode, GeoZone.lower_limit_ft, GeoZone.upper_limit_ft)
        .where(GeoZone.country_id == country_id)
    )

    return list(result.all())


async def get_activity_windows(country_id: int, db: AsyncDBSession) -> list[Row]:
    result = await db.execute(
        select(
            ActivityTime.id, ActivityTime.geo_zone_id, ActivityTime.source, ActivityTime.source_ref,
            ActivityTime.start_at, ActivityTime.ends_at, ActivityTime.lower_limit_ft, ActivityTime.upper_limit_ft,
        )
        .join(GeoZone, GeoZone.id == ActivityTime.geo_zone_id)
        .where(GeoZone.country_id == country_id)
    )

    return list(result.all())
