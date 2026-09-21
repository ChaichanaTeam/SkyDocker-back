import random
from datetime import datetime, timedelta, timezone
from typing import Any

from shapely.geometry import Point, mapping
from sqlalchemy import delete, select

from backend_src.api.exceptions import APIExceptions
from backend_src.api.shared_schemas import BoundingBox, GeoFeature, GeoJson
from backend_src.api.v1.checkin.schema import CheckinProperties
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import Checkin, Country, Pilot
from backend_src.models.enum import FlyingPrivileges, MissionStatus
from .schema import CheckinInput
from .constants import (
    DEMO_COUNTRY_NAME,
    DEMO_COUNTRY_TAG,
    DEMO_PILOT_EMAIL,
    DEMO_PILOT_FIRST_NAME,
    DEMO_PILOT_LAST_NAME,
    DEMO_PILOT_PHONE,
    HEIGHT_RANGE,
    RANGE_RANGE,
    TIME_RANGE,
    WARSAW_BBOX,
)


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
            phone_number=DEMO_PILOT_PHONE,
            password_hash="x",
            country_id=country_id,
        )
        db.add(pilot)
        await db.flush()

    return pilot


def _random_checkin(pilot_id: int, country_id: int, now: datetime) -> tuple[Checkin, tuple[float, float]]:
    min_lon, min_lat, max_lon, max_lat = WARSAW_BBOX
    lon = random.uniform(min_lon, max_lon)
    lat = random.uniform(min_lat, max_lat)

    time = random.randint(*TIME_RANGE)

    checkin = Checkin(
        pilot_id=pilot_id,
        country_id=country_id,
        flying_privilege=random.choice(
            [FlyingPrivileges.a1, FlyingPrivileges.a2, FlyingPrivileges.a3]
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

    starts_at = data.starts_at or datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(seconds=data.time)

    checkin = Checkin(
        pilot_id=pilot_id,
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
        "point": [data.lon, data.lat],
        "h3_index": h3_index,
    }


async def create_random_checkins(db: AsyncDBSession, count: int, reset: bool) -> dict[str, Any]:
    country = await _resolve_country(db, DEMO_COUNTRY_NAME, DEMO_COUNTRY_TAG)
    country_id = country.id

    pilot = await _resolve_demo_pilot(db, country_id)
    pilot_id = pilot.id

    if reset:
        await db.execute(delete(Checkin).where(Checkin.pilot_id == pilot_id))

    now = datetime.now(timezone.utc)
    checkins: list[Checkin] = []
    points: list[tuple[float, float]] = []
    for _ in range(count):
        checkin, point = _random_checkin(pilot_id, country_id, now)
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
        "reset": reset,
        "checkins": [
            {"id": cid, "point": [lon, lat], "h3_index": h3_by_id.get(cid)}
            for cid, (lon, lat) in zip(ids, points)
        ],
    }


_TERMINAL_STATUSES = {
    MissionStatus.cancelled,
    MissionStatus.loss_of_control,
    MissionStatus.ended_intime,
    MissionStatus.late_end,
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
        MissionStatus.ended_intime
        if datetime.now(timezone.utc) <= ends_at
        else MissionStatus.late_end
    )
    checkin.status = new_status
    await db.commit()

    return {
        "message": f"Check-in {checkin_id} ended",
        "id": checkin_id,
        "status": new_status,
    }


async def checkins_in_bbox(bbox: BoundingBox, db: AsyncDBSession) -> GeoJson:
    checkins = await Queries.Checkin.get_all_by_bbox(*bbox.unpack(), db)

    features = [
        GeoFeature(
            geometry=mapping(ch.home_point),
            properties=CheckinProperties.from_checkin(ch),
        )
        for ch in checkins
    ]

    return GeoJson(features=features)