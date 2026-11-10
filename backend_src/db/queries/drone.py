from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload

from backend_src.db import AsyncDBSession
from backend_src.models import Drone


async def get_pilot_drones(pilot_id: int, db: AsyncDBSession) -> list[Drone]:
    result = await db.execute(
        select(Drone)
        .where(Drone.pilot_id == pilot_id, Drone.is_deleted.is_(False))
        .order_by(Drone.id)
        .options(joinedload(Drone.model))
    )

    return list(result.scalars().all())


async def get_pilot_drone(drone_id: int, pilot_id: int, db: AsyncDBSession) -> Optional[Drone]:
    result = await db.execute(
        select(Drone)
        .where(Drone.id == drone_id, Drone.pilot_id == pilot_id, Drone.is_deleted.is_(False))
        .options(joinedload(Drone.model))
    )

    return result.scalar_one_or_none()


async def serial_number_taken(serial_number: str, db: AsyncDBSession, except_drone_id: Optional[int] = None) -> bool:
    """Whether a drone in a drone park already has the serial number, compared without case and edge spaces."""
    statement = exists().where(
        func.lower(func.btrim(Drone.serial_number)) == serial_number.strip().lower(),
        Drone.is_deleted.is_(False),
    )
    if except_drone_id is not None:
        statement = statement.where(Drone.id != except_drone_id)

    result = await db.execute(select(statement))

    return bool(result.scalar())
