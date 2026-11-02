from sqlalchemy import select
from typing import Optional

from backend_src.db import AsyncDBSession
from backend_src.models import Pilot, PilotToFlyingPrivileges, FlyingPrivileges


async def get_by_email(email: str, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.normalized_email == email))
    return result.scalar_one_or_none()


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.id == id))
    return result.scalar_one_or_none()


async def get_privileges(pilot_id: int, db: AsyncDBSession) -> set[FlyingPrivileges]:
    result = await db.execute(
        select(PilotToFlyingPrivileges.flying_privilege)
        .where(PilotToFlyingPrivileges.pilot_id == pilot_id)
    )
    return set(result.scalars().all())
