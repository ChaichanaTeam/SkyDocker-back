from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .session import SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db: AsyncSession = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

AsyncDBDep = Annotated[AsyncSession, Depends(get_db)]