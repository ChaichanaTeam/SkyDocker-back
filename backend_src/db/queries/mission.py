from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend_src.db import AsyncDBSession
from backend_src.models import Mission


async def get_pilot_missions(pilot_id: int, limit: int, offset: int, db: AsyncDBSession) -> list[Mission]:
    result = await db.execute(
        select(Mission)
        .where(Mission.pilot_id == pilot_id)
        .order_by(Mission.starts_at.desc(), Mission.id.desc())
        .limit(limit)
        .offset(offset)
        .options(joinedload(Mission.country))
    )

    return list(result.scalars().all())


async def get_pilot_mission(mission_id: int, pilot_id: int, db: AsyncDBSession) -> Optional[Mission]:
    result = await db.execute(
        select(Mission)
        .where(Mission.id == mission_id, Mission.pilot_id == pilot_id)
        .options(joinedload(Mission.country))
    )

    return result.scalar_one_or_none()
