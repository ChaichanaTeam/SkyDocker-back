from sqlalchemy import select

from backend_src.db import AsyncDBSession
from backend_src.models import Model


async def get_verified(db: AsyncDBSession) -> list[Model]:
    """The drone model catalog, sorted for a manufacturer -> model choice."""
    result = await db.execute(
        select(Model)
        .where(Model.is_model_verified.is_(True))
        .order_by(Model.manufacturer, Model.model_name, Model.id)
    )

    return list(result.scalars().all())

