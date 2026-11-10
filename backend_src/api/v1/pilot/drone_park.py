from typing import Any

from sqlalchemy.exc import IntegrityError

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.db import AsyncDBSession, Queries
from backend_src.dronepark import class_mass_conflict, model_key
from backend_src.models import Drone, Model, OperationalCategory, Pilot
from .schema import CustomDroneModel, DroneCreate


def _drone_error(field: str, msg: str, type: str, input: Any) -> EntityError:
    return {
        "type": f"drone.{type}",
        "loc": ["body", field],
        "msg": msg,
        "input": input,
    }


async def add_drone(data: DroneCreate, pilot: Pilot, db: AsyncDBSession) -> Drone:
    # read before commit, the session expires the pilot afterwards
    pilot_id = pilot.id

    if data.custom_model is not None:
        model = await _new_model(data.custom_model, db)
    else:
        model = await _catalog_model(data.model_id, db) # type: ignore[arg-type]

    mass_g = data.mtom_override if data.mtom_override is not None else model.mtom
    if conflict := class_mass_conflict(data.category, mass_g):
        raise APIExceptions.unprocessable([_drone_error("category", conflict, "class_mass_mismatch", data.category)])

    await _ensure_serial_free(data.serial_number, db)

    drone = Drone(
        pilot_id=pilot_id,
        model=model,
        serial_number=data.serial_number,
        category=data.category,
        is_drone_modified=data.is_drone_modified,
        mtom_override=data.mtom_override,
    )
    db.add(drone)
    drone_id = await _save(drone, db)

    return await Queries.Drone.get_pilot_drone(drone_id, pilot_id, db) # type: ignore[return-value]


async def _catalog_model(model_id: int, db: AsyncDBSession) -> Model:
    model = await Queries.Model.get_verified_by_id(model_id, db)
    if model is None:
        raise APIExceptions.not_found("Drone model not found in the catalog")

    return model


async def _new_model(custom: CustomDroneModel, db: AsyncDBSession) -> Model:
    """Unchecked model typed in by the pilot, a model of the catalog has to be chosen from it instead."""
    key = model_key(custom.manufacturer, custom.model_name)
    for listed in await Queries.Model.get_verified(db):
        if model_key(listed.manufacturer, listed.model_name) == key:
            raise APIExceptions.conflict({
                "msg": f"{listed.manufacturer} {listed.model_name} is in the catalog, choose it by model_id",
                "model_id": listed.id,
            })

    # the operational category is not in drone specifications, a moderator changes it when needed
    return Model(**custom.model_dump(), category=OperationalCategory.OPEN, is_model_verified=False)


async def _ensure_serial_free(serial_number: str, db: AsyncDBSession, except_drone_id: int | None = None) -> None:
    if await Queries.Drone.serial_number_taken(serial_number, db, except_drone_id):
        raise APIExceptions.conflict("A drone with this serial number is already registered")


async def _save(drone: Drone, db: AsyncDBSession) -> int:
    """Id of the stored drone; the unique index still catches a serial number taken at the same moment."""
    try:
        await db.flush()
        drone_id = drone.id
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise APIExceptions.conflict("A drone with this serial number is already registered")

    return drone_id
