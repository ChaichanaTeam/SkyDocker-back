from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .session import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db: AsyncSession = SessionLocal()
    try:
        yield db
    finally:
        await db.close()