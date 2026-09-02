import random
from datetime import datetime, timedelta, timezone
from typing import Any

from shapely.geometry import Point
from sqlalchemy import delete, select

from backend_src.db import AsyncDBSession
from backend_src.models import Checkin, Country, Pilot
from backend_src.models.enum import FlyingPrivileges
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
    country = (await db.execute(select(Country).where(Country.country_tag == tag))
               ).scalar_one_or_none()

    if country is None:
        country = Country(name=name, country_tag=tag)
        db.add(country)
        await db.flush()

    return country


async def _resolve_demo_pilot(db: AsyncDBSession, country_id: int) -> Pilot:
    pilot = (await db.execute(select(Pilot).where(Pilot.email == DEMO_PILOT_EMAIL))
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


async def create_random_checkin(db: AsyncDBSession, reset: bool) -> dict[str, Any]:
    country = await _resolve_country(db, DEMO_COUNTRY_NAME, DEMO_COUNTRY_TAG)
    country_id = country.id

    pilot = await _resolve_demo_pilot(db, country_id)
    pilot_id = pilot.id

    if reset:
        await db.execute(delete(Checkin).where(Checkin.pilot_id == pilot_id))

    min_lon, min_lat, max_lon, max_lat = WARSAW_BBOX
    lon = random.uniform(min_lon, max_lon)
    lat = random.uniform(min_lat, max_lat)
    now = datetime.now(timezone.utc)

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
        ends_at=now + timedelta(hours=1),
        time=random.randint(*TIME_RANGE),
    )
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin, attribute_names=["id", "h3_index"])

    return {
        "message": f"Created check-in {checkin.id}",
        "id": checkin.id,
        "pilot_id": pilot_id,
        "point": [lon, lat],
        "h3_index": checkin.h3_index,
        "reset": reset,
    }