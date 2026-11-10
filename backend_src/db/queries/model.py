from typing import Optional

from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import joinedload

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


async def get_unverified(db: AsyncDBSession) -> list[Model]:
    """Models pilots typed in, the oldest first, as a moderator's queue."""
    result = await db.execute(
        select(Model)
        .where(Model.is_model_verified.is_(False))
        .order_by(Model.created_at, Model.id)
    )

    return list(result.scalars().all())


async def get_drones_of(model_ids: list[int], db: AsyncDBSession) -> list[Drone]:
    """Drones in drone parks that use the models, with their pilots."""
    result = await db.execute(
        select(Drone)
        .where(Drone.model_id.in_(model_ids), Drone.is_deleted.is_(False))
        .order_by(Drone.id)
        .options(joinedload(Drone.pilot), joinedload(Drone.model))
    )

    return list(result.scalars().all())


async def get_by_id(model_id: int, db: AsyncDBSession) -> Optional[Model]:
    result = await db.execute(select(Model).where(Model.id == model_id))

    return result.scalar_one_or_none()


async def replace(model_id: int, by_model_id: int, db: AsyncDBSession) -> None:
    """Moves every drone, deleted ones included, to the other model and removes this one."""
    await db.execute(update(Drone).where(Drone.model_id == model_id).values(model_id=by_model_id))
    await db.execute(delete(Model).where(Model.id == model_id))
