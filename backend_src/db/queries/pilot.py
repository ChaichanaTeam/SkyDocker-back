from sqlalchemy import select

from backend_src.models import Pilot


async def get_by_email(email: str, db) -> Pilot:
    return await db.execute(select(Pilot).where(Pilot.email == email))


async def get_by_id(id: int, db) -> Pilot:
    return await db.execute(select(Pilot).where(Pilot.id == id))
