import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import UploadFile
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from shapely.geometry import Point, mapping
from sqlalchemy import delete, select, update

from backend_src.api.exceptions import APIExceptions
from backend_src.api.shared_schemas import BoundingBox, GeoFeature, GeoJson
from backend_src.db import AsyncDBSession
from backend_src.models import (
    Checkin, Country, Drone, Mission, Model, Pilot,
    FlyingPrivileges, OperationalCategory, MissionFlightGoal, MissionStatus,
)
from .schema import MissionProperties
from .constants import (
    DEFAULT_WINDOW_HOURS,
    DEMO_COUNTRY_NAME,
    DEMO_COUNTRY_TAG,
    IMPORT_DRONE_SERIAL,
    IMPORT_MODEL_MANUFACTURER,
    IMPORT_MODEL_MAX_HEIGHT,
    IMPORT_MODEL_MAX_RANGE,
    IMPORT_MODEL_NAME,
    IMPORT_MODEL_SPEED,
    IMPORT_MODEL_WEIGHT,
    IMPORT_PILOT_EMAIL,
    IMPORT_PILOT_FIRST_NAME,
    IMPORT_PILOT_LAST_NAME,
    IMPORT_PILOT_PHONE,
)


def _load_features(raw: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise APIExceptions.bad_request(f"Invalid JSON: {exc}")

    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise APIExceptions.bad_request("Expected a GeoJSON FeatureCollection")

    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise APIExceptions.bad_request("FeatureCollection has no features")

    return features


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _mission_from_feature(
    feature: dict[str, Any],
    now: datetime,
    pilot_id: int,
    drone_id: int,
    country_id: int,
) -> Mission:
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Point":
        raise ValueError(f"unsupported geometry type: {geometry.get('type')}")

    coords = geometry.get("coordinates") or []
    if len(coords) < 2:
        raise ValueError("point has no coordinates")
    lon, lat = float(coords[0]), float(coords[1])

    props = feature.get("properties") or {}

    starts_at = _parse_dt(props.get("starts_at")) or now
    ends_at = _parse_dt(props.get("ends_at")) or (
        starts_at + timedelta(hours=DEFAULT_WINDOW_HOURS)
    )

    return Mission(
        pilot_id=pilot_id,
        drone_id=drone_id,
        country_id=country_id,
        category=OperationalCategory(props["category"]),
        flight_goal=(
            MissionFlightGoal(props["flight_goal"]) if props.get("flight_goal") else None
        ),
        flying_privilege=FlyingPrivileges(props["flying_privilege"]),
        description=props.get("description"),
        home_point=Point(lon, lat),
        height=int(props["height"]),
        range=int(props["range"]),
        starts_at=starts_at,
        ends_at=ends_at,
        time=int(props.get("time") or 0),
        status=MissionStatus.created,
        spotter_first_name=props.get("spotter_first_name"),
        spotter_last_name=props.get("spotter_last_name"),
        spotter_phone=props.get("spotter_phone"),
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


async def _resolve_import_model(db: AsyncDBSession) -> Model:
    model = (
        await db.execute(
            select(Model).where(
                Model.manufacturer == IMPORT_MODEL_MANUFACTURER,
                Model.model_name == IMPORT_MODEL_NAME,
            )
        )
    ).scalar_one_or_none()

    if model is None:
        model = Model(
            manufacturer=IMPORT_MODEL_MANUFACTURER,
            model_name=IMPORT_MODEL_NAME,
            speed=IMPORT_MODEL_SPEED,
            weight=IMPORT_MODEL_WEIGHT,
            max_height=IMPORT_MODEL_MAX_HEIGHT,
            max_range=IMPORT_MODEL_MAX_RANGE,
        )
        db.add(model)
        await db.flush()

    return model


async def _resolve_import_pilot(db: AsyncDBSession, country_id: int) -> Pilot:
    pilot = (
        await db.execute(select(Pilot).where(Pilot.email == IMPORT_PILOT_EMAIL))
    ).scalar_one_or_none()

    if pilot is None:
        pilot = Pilot(
            first_name=IMPORT_PILOT_FIRST_NAME,
            last_name=IMPORT_PILOT_LAST_NAME,
            email=IMPORT_PILOT_EMAIL,
            phone_number=IMPORT_PILOT_PHONE,
            password_hash="x",
            country_id=country_id,
        )
        db.add(pilot)
        await db.flush()

    return pilot


async def _resolve_import_drone(db: AsyncDBSession, pilot_id: int, model_id: int) -> Drone:
    drone = (
        await db.execute(
            select(Drone).where(Drone.serial_number == IMPORT_DRONE_SERIAL)
        )
    ).scalar_one_or_none()

    if drone is None:
        drone = Drone(
            pilot_id=pilot_id,
            model_id=model_id,
            serial_number=IMPORT_DRONE_SERIAL,
        )
        db.add(drone)
        await db.flush()

    return drone


def _serialize(mission: Mission) -> dict[str, Any]:
    return {
        "id": mission.id,
        "category": mission.category,
        "flight_goal": mission.flight_goal,
        "flying_privilege": mission.flying_privilege,
        "status": mission.status,
        "point": [mission.home_point.x, mission.home_point.y],
        "height": mission.height,
        "range": mission.range,
        "starts_at": mission.starts_at,
        "ends_at": mission.ends_at,
        "time": mission.time,
        "h3_index": mission.h3_index,
        "pilot_id": mission.pilot_id,
        "drone_id": mission.drone_id,
        "country_id": mission.country_id,
    }


async def import_missions(db: AsyncDBSession, file: UploadFile, reset: bool) -> dict[str, Any]:
    features = _load_features(await file.read())

    country = await _resolve_country(db, DEMO_COUNTRY_NAME, DEMO_COUNTRY_TAG)
    model = await _resolve_import_model(db)
    pilot = await _resolve_import_pilot(db, country.id)
    drone = await _resolve_import_drone(db, pilot.id, model.id)

    country_id = country.id
    pilot_id = pilot.id
    drone_id = drone.id

    if reset:
        await db.execute(
            update(Checkin).values(mission_id=None).where(Checkin.mission_id.is_not(None))
        )
        await db.execute(delete(Mission))

    now = datetime.now(timezone.utc)
    missions: list[Mission] = []
    errors: list[str] = []

    for index, feature in enumerate(features):
        try:
            missions.append(
                _mission_from_feature(feature, now, pilot_id, drone_id, country_id)
            )
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"feature {index}: {exc}")

    if not missions:
        raise APIExceptions.bad_request("No valid missions to import")

    db.add_all(missions)
    await db.flush()
    imported = len(missions)
    await db.commit()

    return {
        "message": f"Imported {imported} mission(s)",
        "imported": imported,
        "skipped": len(errors),
        "errors": errors[:20],
        "reset": reset,
    }


async def list_missions(db: AsyncDBSession, limit: int, offset: int) -> dict[str, Any]:
    missions = (
        await db.execute(
            select(Mission).order_by(Mission.id).limit(limit).offset(offset)
        )
    ).scalars().all()

    return {"count": len(missions), "missions": [_serialize(m) for m in missions]}


async def missions_in_bbox(bbox: BoundingBox, db: AsyncDBSession) -> GeoJson:
    x1, y1, x2, y2 = bbox.unpack()

    missions = (
        await db.execute(
            select(Mission)
            .where(
                ST_Intersects(
                    Mission.home_point, ST_MakeEnvelope(x1, y1, x2, y2, 4326)
                )
            )
            .order_by(Mission.id)
        )
    ).scalars().all()

    features = [
        GeoFeature(
            geometry=mapping(m.home_point),
            properties=MissionProperties.from_mission(m),
        )
        for m in missions
    ]

    return GeoJson(features=features)
