from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession, Queries
from backend_src.dronepark import class_mass_conflict, model_key, take_off_mass
from backend_src.models import Drone, Model
from .schema import ClassConflict, ModelCorrection, ModelDroneRead, ModelReplacement, ModelReview, UnverifiedModelRead


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


async def approve(model_id: int, correction: ModelCorrection, db: AsyncDBSession) -> ModelReview:
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


async def replace(model_id: int, replacement: ModelReplacement, db: AsyncDBSession) -> ModelReview:
    await _unverified_model(model_id, db)

    if await Queries.Model.get_verified_by_id(replacement.model_id, db) is None:
        raise APIExceptions.not_found("Catalog drone model not found")

    moved = {drone.id for drone in await Queries.Model.get_drones_of([model_id], db)}
    await Queries.Model.replace(model_id, replacement.model_id, db)
    await db.commit()

    return await _review(replacement.model_id, db, moved)


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
