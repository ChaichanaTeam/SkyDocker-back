from backend_src.db import AsyncDBSession, Queries
from backend_src.models import Model


async def get_catalog(db: AsyncDBSession) -> list[Model]:
    return await Queries.Model.get_verified(db)
