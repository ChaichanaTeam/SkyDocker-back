from typing import Optional

from sqlalchemy import delete, exists, select

from backend_src.db import AsyncDBSession
from backend_src.models import Drone, Model


async def get_verified(db: AsyncDBSession) -> list[Model]:
    """The drone model catalog, sorted for a manufacturer -> model choice."""
    result = await db.execute(
        select(Model)
        .where(Model.is_model_verified.is_(True))
        .order_by(Model.manufacturer, Model.model_name, Model.id)
    )

    return list(result.scalars().all())



async def get_verified_by_id(model_id: int, db: AsyncDBSession) -> Optional[Model]:
    result = await db.execute(select(Model).where(Model.id == model_id, Model.is_model_verified.is_(True)))

    return result.scalar_one_or_none()


async def delete_if_unused_unverified(model_id: int, db: AsyncDBSession) -> None:
    """Removes a model a pilot typed in once no drone, deleted ones included, refers to it any more."""
    await db.execute(
        delete(Model).where(
            Model.id == model_id,
            Model.is_model_verified.is_(False),
            ~exists().where(Drone.model_id == Model.id),
        )
    )
