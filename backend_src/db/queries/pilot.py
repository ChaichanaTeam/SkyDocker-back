from sqlalchemy import select
from typing import Optional

from backend_src.db import AsyncDBSession
from backend_src.models import Pilot


async def get_by_email(email: str, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.normalized_email == email))
    return result.scalar_one_or_none()


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[Pilot]:
    result = await db.execute(select(Pilot).where(Pilot.id == id))
    return result.scalar_one_or_none()
