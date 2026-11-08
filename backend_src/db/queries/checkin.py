from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from backend_src.db import AsyncDBSession
from backend_src.models import Checkin, MissionStatus


# Statuses after which a check-in no longer blocks a new one
TERMINAL_STATUSES = frozenset({
    MissionStatus.CANCELLED,
    MissionStatus.LOSS_OF_CONTROL,
    MissionStatus.ENDED_INTIME,
    MissionStatus.LATE_END,
})


async def get_all_by_bbox(x1: float, y1: float, x2: float, y2: float, country_id: int, db: AsyncDBSession) -> list[Checkin]:
    result = await db.execute(
        select(Checkin)
        .where(
            Checkin.country_id == country_id,
            ST_Intersects(Checkin.home_point, ST_MakeEnvelope(x1, y1, x2, y2, 4326)),
            Checkin.status.not_in(TERMINAL_STATUSES)
        )
        .options(joinedload(Checkin.country))
        .options(joinedload(Checkin.pilot))
    )

    return result.scalars().all() # type: ignore


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[Checkin]:
    result = await db.execute(
        select(Checkin)
        .where(Checkin.id == id)
        .options(joinedload(Checkin.country))
        .options(joinedload(Checkin.pilot))
    )

    return result.scalar_one_or_none()


async def get_active_by_pilot(pilot_id: int, db: AsyncDBSession) -> Optional[Checkin]:
    """Check-in of the pilot that is not ended yet, a pilot can have only one."""
    result = await db.execute(
        select(Checkin)
        .where(Checkin.pilot_id == pilot_id, Checkin.status.not_in(TERMINAL_STATUSES))
        .order_by(Checkin.starts_at.desc())
        .limit(1)
        .options(joinedload(Checkin.country))
        .options(joinedload(Checkin.pilot))
    )

    return result.scalar_one_or_none()
