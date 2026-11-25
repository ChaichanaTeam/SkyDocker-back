from sqlalchemy import func, select
from typing import Optional

from backend_src.db import AsyncDBSession
from backend_src.models import AfdModerator


async def get_by_email(email: str, db: AsyncDBSession) -> Optional[AfdModerator]:
    # The email is unique ignoring the case (afd_moderator_email_lower_key)
    result = await db.execute(select(AfdModerator).where(func.lower(AfdModerator.email) == email.lower()))
    return result.scalar_one_or_none()


async def get_by_id(id: int, db: AsyncDBSession) -> Optional[AfdModerator]:
    result = await db.execute(select(AfdModerator).where(AfdModerator.id == id))
    return result.scalar_one_or_none()


async def get_by_ids(ids: set[int], db: AsyncDBSession) -> list[AfdModerator]:
    if not ids:
        return []

    result = await db.execute(select(AfdModerator).where(AfdModerator.id.in_(ids)))
    return list(result.scalars().all())
