from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend_src.db import AsyncDBSession
from backend_src.models import Drone


async def get_pilot_drone(drone_id: int, pilot_id: int, db: AsyncDBSession) -> Optional[Drone]:
    result = await db.execute(
        select(Drone)
        .where(Drone.id == drone_id, Drone.pilot_id == pilot_id)
        .options(joinedload(Drone.model))
    )

    return result.scalar_one_or_none()
