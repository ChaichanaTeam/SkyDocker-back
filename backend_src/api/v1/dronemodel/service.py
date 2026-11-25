from contextlib import asynccontextmanager
from typing import AsyncIterator

from backend_src.api.exceptions import APIExceptions
from backend_src.api.v1.verification.schema import ReviewHolder
from backend_src.cache import AsyncRedisSession, REVIEW_LOCK_TTL_SECONDS, acquire_review_lock, release_review_lock
from backend_src.db import AsyncDBSession, Queries
from backend_src.dronepark import class_mass_conflict, model_key, take_off_mass
from backend_src.models import AfdModerator, Drone, Model
from .schema import ClassConflict, ModelCorrection, ModelDroneRead, ModelReplacement, ModelReview, UnverifiedModelRead


async def get_catalog(db: AsyncDBSession) -> list[Model]:
    return await Queries.Model.get_verified(db)


async def list_unverified(db: AsyncDBSession) -> list[UnverifiedModelRead]:
    models = await Queries.Model.get_unverified(db)
    drones = await Queries.Model.get_drones_of([model.id for model in models], db)

    return [
        UnverifiedModelRead.model_validate({
            **{field: getattr(model, field) for field in UnverifiedModelRead.model_fields if field != "drones"},
            "drones": [ModelDroneRead.from_drone(drone) for drone in drones if drone.model_id == model.id],
        })
        for model in models
    ]


_REVIEW_LOCK_KIND = "drone_model"


@asynccontextmanager
async def _deciding(model_id: int, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession) -> AsyncIterator[None]:
    """Holds the model for the moderator while the decision runs, so two moderators never decide on it at once."""
    moderator_id = moderator.id
    lock = await acquire_review_lock(redis, _REVIEW_LOCK_KIND, model_id, moderator_id, REVIEW_LOCK_TTL_SECONDS)
    if not lock.taken:
        holder = await Queries.Moderator.get_by_id(lock.holder_id, db)
        raise APIExceptions.conflict({
            "msg": "Another moderator decides on the drone model",
            "moderator": ReviewHolder.model_validate(holder).model_dump() if holder is not None else None,
            "expires_in": lock.expires_in,
        })

    try:
        yield
    finally:
        await release_review_lock(redis, _REVIEW_LOCK_KIND, model_id, moderator_id)


async def approve(
    model_id: int, correction: ModelCorrection, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession,
) -> ModelReview:
    async with _deciding(model_id, moderator, db, redis):
        return await _approve(model_id, correction, db)


async def _approve(model_id: int, correction: ModelCorrection, db: AsyncDBSession) -> ModelReview:
    model = await _unverified_model(model_id, db)

    for field, value in correction.model_dump(exclude_unset=True).items():
        setattr(model, field, value)

    key = model_key(model.manufacturer, model.model_name)
    for listed in await Queries.Model.get_verified(db):
        if model_key(listed.manufacturer, listed.model_name) == key:
            raise APIExceptions.conflict({
                "msg": f"{listed.manufacturer} {listed.model_name} is in the catalog already, replace the model with it",
                "model_id": listed.id,
            })

    model.is_model_verified = True
    await db.commit()

    return await _review(model_id, db)


async def replace(
    model_id: int, replacement: ModelReplacement, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession,
) -> ModelReview:
    async with _deciding(model_id, moderator, db, redis):
        return await _replace(model_id, replacement, db)


async def _replace(model_id: int, replacement: ModelReplacement, db: AsyncDBSession) -> ModelReview:
    await _unverified_model(model_id, db)

    if await Queries.Model.get_verified_by_id(replacement.model_id, db) is None:
        raise APIExceptions.not_found("Catalog drone model not found")

    moved = {drone.id for drone in await Queries.Model.get_drones_of([model_id], db)}
    await Queries.Model.replace(model_id, replacement.model_id, db)
    await db.commit()

    return await _review(replacement.model_id, db, moved)


async def delete(model_id: int, db: AsyncDBSession) -> dict[str, str]:
    if await Queries.Model.get_by_id(model_id, db) is None:
        raise APIExceptions.not_found("Drone model not found")

    if not await Queries.Model.delete_unused(model_id, db):
        raise APIExceptions.conflict("A drone in a drone park or a check-in or mission uses the drone model")

    await db.commit()
    return {"message": f"Drone model {model_id} deleted"}


async def _unverified_model(model_id: int, db: AsyncDBSession) -> Model:
    model = await Queries.Model.get_by_id(model_id, db)
    if model is None:
        raise APIExceptions.not_found("Drone model not found")

    if model.is_model_verified:
        raise APIExceptions.conflict("The drone model is in the catalog already")

    return model


async def _review(model_id: int, db: AsyncDBSession, drone_ids: set[int] | None = None) -> ModelReview:
    """The model with the class conflicts of its drones, only of the given ones when passed."""
    model = await Queries.Model.get_by_id(model_id, db)
    drones = [
        drone for drone in await Queries.Model.get_drones_of([model_id], db)
        if drone_ids is None or drone.id in drone_ids
    ]

    return ModelReview(model=model, class_conflicts=[c for drone in drones if (c := _class_conflict(drone))]) # type: ignore[arg-type]


def _class_conflict(drone: Drone) -> ClassConflict | None:
    mass_g = take_off_mass(drone)
    msg = class_mass_conflict(drone.category, mass_g)
    if msg is None:
        return None

    return ClassConflict(drone_id=drone.id, pilot_email=drone.pilot.email, category=drone.category, mass_g=mass_g, msg=msg)
