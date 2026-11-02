from typing import Optional

from sqlalchemy import select

from backend_src.db import AsyncDBSession
from backend_src.models import Mission


async def get_pilot_mission(mission_id: int, pilot_id: int, db: AsyncDBSession) -> Optional[Mission]:
    result = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.pilot_id == pilot_id)
    )

    return result.scalar_one_or_none()
