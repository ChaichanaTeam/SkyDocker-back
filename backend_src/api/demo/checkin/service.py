import random
from datetime import datetime, timedelta, timezone
from typing import Any

from shapely.geometry import Point, mapping
from sqlalchemy import delete, select, update

from backend_src.api.exceptions import APIExceptions
from backend_src.api.shared_schemas import BoundingBox, GeoFeature, GeoJson, normalize_email
from backend_src.api.v1.checkin.schema import CheckinProperties
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    Checkin, Country, Drone, Model, Pilot,
    DroneCategory, FlyingPrivileges, MissionStatus, OperationalCategory
)
from .schema import CheckinInput
from .constants import (
    DEMO_COUNTRY_NAME,
    DEMO_COUNTRY_TAG,
    DEMO_DRONE_SERIAL,
    DEMO_MODEL_MANUFACTURER,
    DEMO_MODEL_MAX_HEIGHT,
    DEMO_MODEL_MAX_RANGE,
    DEMO_MODEL_MTOM,
    DEMO_MODEL_NAME,
    DEMO_MODEL_SPEED,
    DEMO_PILOT_EMAIL,
    DEMO_PILOT_FIRST_NAME,
    DEMO_PILOT_LAST_NAME,
    DEMO_PILOT_PHONE,
    HEIGHT_RANGE,
    RANGE_RANGE,
    TIME_RANGE,
    WARSAW_BBOX,
)


_TERMINAL_STATUSES = {
    MissionStatus.CANCELLED,
    MissionStatus.LOSS_OF_CONTROL,
    MissionStatus.ENDED_INTIME,
    MissionStatus.LATE_END,
}


async def _resolve_country(db: AsyncDBSession, name: str, tag: str) -> Country:
    country = (
        await db.execute(select(Country).where(Country.country_tag == tag))
    ).scalar_one_or_none()

    if country is None:
        country = Country(name=name, country_tag=tag)
        db.add(country)
        await db.flush()

    return country


async def _resolve_demo_pilot(db: AsyncDBSession, country_id: int) -> Pilot:
    pilot = (
        await db.execute(select(Pilot).where(Pilot.email == DEMO_PILOT_EMAIL))
    ).scalar_one_or_none()

    if pilot is None:
        pilot = Pilot(
            first_name=DEMO_PILOT_FIRST_NAME,
            last_name=DEMO_PILOT_LAST_NAME,
            email=DEMO_PILOT_EMAIL,
            normalized_email=normalize_email(DEMO_PILOT_EMAIL),
            phone_number=DEMO_PILOT_PHONE,
            password_hash="x"
        )
        db.add(pilot)
        await db.flush()

    return pilot


async def _resolve_demo_model(db: AsyncDBSession) -> Model:
    model = (
        await db.execute(
            select(Model).where(
                Model.manufacturer == DEMO_MODEL_MANUFACTURER,
                Model.model_name == DEMO_MODEL_NAME,
            )
        )
    ).scalar_one_or_none()

    if model is None:
        model = Model(
            manufacturer=DEMO_MODEL_MANUFACTURER,
            model_name=DEMO_MODEL_NAME,
            category=OperationalCategory.OPEN,
            speed=DEMO_MODEL_SPEED,
            mtom=DEMO_MODEL_MTOM,
            max_height=DEMO_MODEL_MAX_HEIGHT,
            max_range=DEMO_MODEL_MAX_RANGE,
        )
        db.add(model)
        await db.flush()

    return model


async def _resolve_demo_drone(db: AsyncDBSession, pilot_id: int) -> Drone:
    drone = (
        await db.execute(
            select(Drone).where(
                Drone.pilot_id == pilot_id,
                Drone.serial_number == DEMO_DRONE_SERIAL,
            )
        )
    ).scalar_one_or_none()

    if drone is None:
        model = await _resolve_demo_model(db)
        drone = Drone(
            pilot_id=pilot_id,
            model_id=model.id,
            category=DroneCategory.C0,
            serial_number=DEMO_DRONE_SERIAL,
        )
        db.add(drone)
        await db.flush()

    return drone


async def _cancel_open_checkins(db: AsyncDBSession, pilot_id: int) -> int:
    result = await db.execute(
        update(Checkin)
        .where(Checkin.pilot_id == pilot_id, Checkin.status.not_in(_TERMINAL_STATUSES))
        .values(status=MissionStatus.CANCELLED)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def _random_checkin(pilot_id: int, drone_id: int, country_id: int, now: datetime) -> tuple[Checkin, tuple[float, float]]:
    min_lon, min_lat, max_lon, max_lat = WARSAW_BBOX
    lon = random.uniform(min_lon, max_lon)
    lat = random.uniform(min_lat, max_lat)

    time = random.randint(*TIME_RANGE)

    checkin = Checkin(
        pilot_id=pilot_id,
        drone_id=drone_id,
        country_id=country_id,
        flying_privilege=random.choice(
            [FlyingPrivileges.A1, FlyingPrivileges.A2, FlyingPrivileges.A3]
        ),
        home_point=Point(lon, lat),
        height=random.randint(*HEIGHT_RANGE),
        range=random.randint(*RANGE_RANGE),
        starts_at=now,
        ends_at=now + timedelta(seconds=time),
        time=time,
    )
    return checkin, (lon, lat)


async def create_checkin(db: AsyncDBSession, data: CheckinInput) -> dict[str, Any]:
    country = await _resolve_country(db, DEMO_COUNTRY_NAME, DEMO_COUNTRY_TAG)
    country_id = country.id

    pilot = await _resolve_demo_pilot(db, country_id)
    pilot_id = pilot.id

    drone = await _resolve_demo_drone(db, pilot_id)
    drone_id = drone.id

    cancelled = await _cancel_open_checkins(db, pilot_id)

    starts_at = data.starts_at or datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(seconds=data.time)

    checkin = Checkin(
        pilot_id=pilot_id,
        drone_id=drone_id,
        country_id=country_id,
        flying_privilege=data.flying_privilege,
        home_point=Point(data.lon, data.lat),
        height=data.height,
        range=data.range,
        starts_at=starts_at,
        ends_at=ends_at,
        time=data.time,
        description=data.description,
    )
    db.add(checkin)
    await db.flush()
    checkin_id = checkin.id
    await db.commit()

    h3_index = (
        await db.execute(select(Checkin.h3_index).where(Checkin.id == checkin_id))
    ).scalar_one()

    return {
        "message": f"Created check-in {checkin_id} for pilot {pilot_id}",
        "id": checkin_id,
        "pilot_id": pilot_id,
        "drone_id": drone_id,
        "cancelled": cancelled,
        "point": [data.lon, data.lat],
        "h3_index": h3_index,
    }


async def create_random_checkins(db: AsyncDBSession, count: int, reset: bool) -> dict[str, Any]:
    country = await _resolve_country(db, DEMO_COUNTRY_NAME, DEMO_COUNTRY_TAG)
    country_id = country.id

    pilot = await _resolve_demo_pilot(db, country_id)
    pilot_id = pilot.id

    drone = await _resolve_demo_drone(db, pilot_id)
    drone_id = drone.id

    cancelled = 0
    if reset:
        await db.execute(delete(Checkin).where(Checkin.pilot_id == pilot_id))
    else:
        cancelled = await _cancel_open_checkins(db, pilot_id)

    now = datetime.now(timezone.utc)
    checkins: list[Checkin] = []
    points: list[tuple[float, float]] = []
    for _ in range(count):
        checkin, point = _random_checkin(pilot_id, drone_id, country_id, now)
        checkins.append(checkin)
        points.append(point)

    db.add_all(checkins)
    await db.flush()
    ids = [c.id for c in checkins]
    await db.commit()

    h3_by_id = dict(
        (
            await db.execute(
                select(Checkin.id, Checkin.h3_index).where(Checkin.id.in_(ids))
            )
        ).all()
    )

    return {
        "message": f"Created {len(ids)} check-in(s) for pilot {pilot_id}",
        "created": len(ids),
        "pilot_id": pilot_id,
        "drone_id": drone_id,
        "cancelled": cancelled,
        "reset": reset,
        "checkins": [
            {"id": cid, "point": [lon, lat], "h3_index": h3_by_id.get(cid)}
            for cid, (lon, lat) in zip(ids, points)
        ],
    }


async def end_checkin(db: AsyncDBSession, checkin_id: int) -> dict[str, Any]:
    checkin = (
        await db.execute(select(Checkin).where(Checkin.id == checkin_id))
    ).scalar_one_or_none()

    if checkin is None:
        raise APIExceptions.not_found(f"Check-in {checkin_id} not found")

    if checkin.status in _TERMINAL_STATUSES:
        raise APIExceptions.conflict(
            f"Check-in {checkin_id} is already {checkin.status}"
        )

    ends_at = checkin.ends_at
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)

    new_status = (
        MissionStatus.ENDED_INTIME
        if datetime.now(timezone.utc) <= ends_at
        else MissionStatus.LATE_END
    )
    checkin.status = new_status
    await db.commit()

    return {
        "message": f"Check-in {checkin_id} ended",
        "id": checkin_id,
        "status": new_status,
    }


async def checkins_in_bbox(bbox: BoundingBox, country_id: int, db: AsyncDBSession) -> GeoJson:
    checkins = await Queries.Checkin.get_all_by_bbox(*bbox.unpack(), country_id, db)

    features = [
        GeoFeature(
            geometry=mapping(ch.home_point),
            properties=CheckinProperties.from_checkin(ch),
        )
        for ch in checkins
    ]

    return GeoJson(features=features)