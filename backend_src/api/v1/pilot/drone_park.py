from typing import Any

from sqlalchemy.exc import IntegrityError

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.db import AsyncDBSession, Queries
from backend_src.dronepark import class_mass_conflict, model_key
from backend_src.models import Drone, DroneCategory, Model, OperationalCategory, Pilot
from .schema import CustomDroneModel, DroneCreate, DroneUpdate


SERIAL_TAKEN = "A drone with this serial number is already registered"


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

    _check_class(data.category, data.mtom_override if data.mtom_override is not None else model.mtom)
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
    try:
        await db.flush()
        drone_id = drone.id
        await db.commit()
    except IntegrityError:
        # the unique index still catches a serial number taken at the same moment
        await db.rollback()
        raise APIExceptions.conflict(SERIAL_TAKEN)

    return await Queries.Drone.get_pilot_drone(drone_id, pilot_id, db) # type: ignore[return-value]


async def update_drone(drone_id: int, data: DroneUpdate, pilot: Pilot, db: AsyncDBSession) -> Drone:
    pilot_id = pilot.id
    drone = await _own_free_drone(drone_id, pilot_id, db)
    passed = data.model_fields_set
    old_model_id = drone.model_id

    if data.custom_model is not None:
        model = await _new_model(data.custom_model, db)
    elif data.model_id is not None:
        model = await _catalog_model(data.model_id, db)
    else:
        model = drone.model

    modified = data.is_drone_modified if "is_drone_modified" in passed else drone.is_drone_modified
    mtom_override = data.mtom_override if "mtom_override" in passed else (drone.mtom_override if modified else None)
    if modified != (mtom_override is not None):
        raise APIExceptions.unprocessable([_drone_error(
            "mtom_override", "A modified drone needs mtom_override, an unmodified one must not have it",
            "mass_required", mtom_override,
        )])

    category = data.category or drone.category
    _check_class(category, mtom_override if mtom_override is not None else model.mtom)
    if data.serial_number is not None:
        await _ensure_serial_free(data.serial_number, db, drone_id)
        drone.serial_number = data.serial_number

    drone.model = model
    drone.category = category
    drone.is_drone_modified = modified
    drone.mtom_override = mtom_override
    try:
        await db.flush()
        if model.id != old_model_id:
            await Queries.Model.delete_if_unused_unverified(old_model_id, db)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise APIExceptions.conflict(SERIAL_TAKEN)

    return await Queries.Drone.get_pilot_drone(drone_id, pilot_id, db) # type: ignore[return-value]


async def delete_drone(drone_id: int, pilot: Pilot, db: AsyncDBSession) -> None:
    """Hides the drone from the drone park, its check-ins and missions keep referring to it."""
    drone = await _own_free_drone(drone_id, pilot.id, db)
    drone.is_deleted = True
    await db.commit()


async def _own_free_drone(drone_id: int, pilot_id: int, db: AsyncDBSession) -> Drone:
    """The pilot's drone that no check-in or mission is using, a flight in progress keeps its drone as planned."""
    drone = await Queries.Drone.get_pilot_drone(drone_id, pilot_id, db)
    if drone is None:
        raise APIExceptions.not_found("Drone not found")

    if await Queries.Drone.is_busy(drone_id, db):
        raise APIExceptions.conflict("The drone has an unfinished check-in or a planned mission, it cannot be changed now")

    return drone


def _check_class(category: DroneCategory, mass_g: int) -> None:
    if conflict := class_mass_conflict(category, mass_g):
        raise APIExceptions.unprocessable([_drone_error("category", conflict, "class_mass_mismatch", category)])


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
        raise APIExceptions.conflict(SERIAL_TAKEN)
