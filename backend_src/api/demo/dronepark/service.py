import random
from string import ascii_uppercase, digits
from typing import Any

from sqlalchemy import select

from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import Drone, Model
from backend_src.models.enum import DroneCategory
from .constants import DEMO_MODELS, SERIAL_LENGTH, SERIAL_PREFIX


def _model_title(manufacturer: str, model_name: str) -> str:
    return f"{manufacturer} {model_name}"


def _random_serial() -> str:
    return SERIAL_PREFIX + ''.join(random.choices(ascii_uppercase + digits, k=SERIAL_LENGTH))


async def _verified_models(db: AsyncDBSession) -> list[Model]:
    result = await db.execute(select(Model).where(Model.is_model_verified.is_(True)))
    return list(result.scalars().all())


async def seed_models(db: AsyncDBSession) -> dict[str, Any]:
    existing = set(
        (await db.execute(select(Model.manufacturer, Model.model_name))).tuples().all()
    )

    missing = [
        spec for spec in DEMO_MODELS
        if (spec["manufacturer"], spec["model_name"]) not in existing
    ]

    if missing:
        db.add_all(Model(**spec, is_model_verified=True) for spec in missing)
        await db.commit()

    return {
        "message": f"Created {len(missing)} of {len(DEMO_MODELS)} drone models",
        "added": [_model_title(spec["manufacturer"], spec["model_name"]) for spec in missing],
        "skipped": [
            _model_title(spec["manufacturer"], spec["model_name"])
            for spec in DEMO_MODELS
            if (spec["manufacturer"], spec["model_name"]) in existing
        ],
        "total": len(DEMO_MODELS),
    }


def _map_category_by_mtom(mtom: int) -> DroneCategory:
    if mtom < 250:
        return DroneCategory.C0

    if mtom < 900:
        return DroneCategory.C1
    
    if mtom < 4000:
        return DroneCategory.C2
    
    return DroneCategory.C5


async def create_random_drones(db: AsyncDBSession, email: str, count: int) -> dict[str, Any]:
    pilot = await Queries.Pilot.get_by_email(email, db)
    if pilot is None:
        raise APIExceptions.not_found(f"Pilot {email} not found")
    pilot_id = pilot.id

    models = await _verified_models(db)
    if not models:
        await seed_models(db)
        models = await _verified_models(db)

    drones: list[tuple[Drone, Model]] = []
    for _ in range(count):
        model = random.choice(models)
        drone = Drone(pilot_id=pilot_id, category=_map_category_by_mtom(model.mtom), model_id=model.id, serial_number=_random_serial())
        drones.append((drone, model))

    db.add_all(drone for drone, _ in drones)
    await db.flush()

    created = [
        {
            "id": drone.id,
            "serial_number": drone.serial_number,
            "model_id": model.id,
            "model": _model_title(model.manufacturer, model.model_name),
        }
        for drone, model in drones
    ]
    await db.commit()

    return {
        "message": f"Created {len(created)} drone(s) for {email}",
        "created": len(created),
        "pilot_id": pilot_id,
        "drones": created,
    }
