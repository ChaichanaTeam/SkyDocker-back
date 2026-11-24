from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload

from backend_src.db import AsyncDBSession
from backend_src.db.queries.checkin import TERMINAL_STATUSES
from backend_src.models import Checkin, Drone, Mission, MissionStatus


# Missions that still book the drone until they end
_PLANNED_MISSION_STATUSES = (MissionStatus.PENDING, MissionStatus.ACCEPTED, MissionStatus.ACTIVE)


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


async def is_busy(drone_id: int, db: AsyncDBSession) -> bool:
    """Whether a check-in of the drone is not finished or a mission of it is planned and not over yet."""
    unfinished_checkin = exists().where(Checkin.drone_id == drone_id, Checkin.status.not_in(TERMINAL_STATUSES))
    planned_mission = exists().where(
        Mission.drone_id == drone_id,
        Mission.status.in_(_PLANNED_MISSION_STATUSES),
        Mission.ends_at > datetime.now(timezone.utc),
    )
    result = await db.execute(select(unfinished_checkin | planned_mission))

    return bool(result.scalar())
