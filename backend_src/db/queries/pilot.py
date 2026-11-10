from sqlalchemy import func, or_, select
from typing import Optional

from backend_src.db import AsyncDBSession
from backend_src.models import Pilot, PilotToFlyingPrivileges, FlyingPrivileges


async def get_by_email(email: str, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.normalized_email == email))
    return result.scalar_one_or_none()


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.id == id))
    return result.scalar_one_or_none()


async def get_privilege_rows(pilot_id: int, db: AsyncDBSession) -> list[PilotToFlyingPrivileges]:
    """Privileges that are still valid, an expired row may live until the daily removal."""
    result = await db.execute(
        select(PilotToFlyingPrivileges)
        .where(
            PilotToFlyingPrivileges.pilot_id == pilot_id,
            or_(
                PilotToFlyingPrivileges.expires_at.is_(None),
                PilotToFlyingPrivileges.expires_at >= func.current_date(),
            ),
        )
        .order_by(PilotToFlyingPrivileges.flying_privilege)
    )
    return list(result.scalars().all())


async def get_privileges(pilot_id: int, db: AsyncDBSession) -> set[FlyingPrivileges]:
    return {row.flying_privilege for row in await get_privilege_rows(pilot_id, db)}
