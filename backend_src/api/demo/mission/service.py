import json
from typing import Any, Optional

from fastapi import UploadFile
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from pydantic import ValidationError
from shapely.geometry import Point, mapping
from sqlalchemy import select

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.api.shared_schemas import BoundingBox, GeoFeature, GeoJson
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import Mission, FlyingPrivileges, OperationalCategory, MissionStatus
from .schema import ImportedMission, MissionImportFeature, MissionImportReport, MissionProperties


# Statuses check-ins give a mission, PANSA cannot change such a mission any more
_FLOWN_STATUSES = frozenset({
    MissionStatus.ACTIVE, MissionStatus.LATE, MissionStatus.LOSS_OF_CONTROL, MissionStatus.ENDED_INTIME, MissionStatus.LATE_END,
})

_OPEN_PRIVILEGES = frozenset({FlyingPrivileges.A1, FlyingPrivileges.A2, FlyingPrivileges.A3})


async def import_missions(db: AsyncDBSession, file: UploadFile) -> MissionImportReport:
    """Stores the missions of the file as PANSA decided them, all of them or none when one is wrong."""
    features = _load_features(await file.read())

    errors: list[EntityError] = []
    parsed: list[tuple[str, MissionImportFeature]] = []
    for index, feature in enumerate(features):
        label = _label(feature, index)
        try:
            parsed.append((label, MissionImportFeature.model_validate(feature)))
        except ValidationError as exc:
            errors += [_error(label, list(error["loc"]), error["msg"], error["type"], error.get("input")) for error in exc.errors()]

    seen: set[str] = set()
    for label, feature in parsed:
        external_id = feature.properties.external_id
        if external_id in seen:
            errors.append(_error(label, ["properties", "external_id"], "external_id repeats in the file", "duplicate", external_id))
        seen.add(external_id)

    stored = await Queries.Mission.get_by_external_ids(list(seen), db)
    values: list[tuple[Optional[Mission], dict[str, Any]]] = []
    for label, feature in parsed:
        mission = stored.get(feature.properties.external_id)
        row, row_errors = await _mission_values(label, feature, mission, db)
        errors += row_errors
        values.append((mission, row))

    if errors:
        raise APIExceptions.unprocessable(errors)

    created = 0
    missions: list[Mission] = []
    for mission, row in values:
        if mission is None:
            mission = Mission(**row)
            db.add(mission)
            created += 1
        else:
            for field, value in row.items():
                setattr(mission, field, value)
        missions.append(mission)

    await db.flush()
    imported = [ImportedMission(external_id=m.external_id, id=m.id, status=m.status) for m in missions] # type: ignore[arg-type]
    await db.commit()

    return MissionImportReport(created=created, updated=len(missions) - created, missions=imported)


def _load_features(raw: bytes) -> list[Any]:
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


def _label(feature: Any, index: int) -> str:
    """external_id of the feature when it has one, so an error points to the mission, otherwise its position."""
    properties = feature.get("properties") if isinstance(feature, dict) else None
    external_id = properties.get("external_id") if isinstance(properties, dict) else None

    return external_id.strip() if isinstance(external_id, str) and external_id.strip() else f"#{index}"


def _error(label: str, loc: list[Any], msg: str, type: str, input: Any) -> EntityError:
    return {
        "type": f"mission.{type}",
        "loc": ["file", label, *loc],
        "msg": msg,
        "input": input,
    }


async def _mission_values(
    label: str, feature: MissionImportFeature, mission: Optional[Mission], db: AsyncDBSession,
) -> tuple[dict[str, Any], list[EntityError]]:
    """Columns of the mission from the feature, with the errors that keep it from being stored."""
    props = feature.properties
    errors: list[EntityError] = []

    if mission is not None and (mission.status in _FLOWN_STATUSES or await Queries.Mission.has_checkin(mission.id, db)):
        errors.append(_error(label, ["properties", "external_id"], "The mission was flown, it cannot be changed", "flown", props.external_id))

    drone_id = None
    pilot = await Queries.Pilot.get_by_email(props.pilot_email, db)
    if pilot is None:
        errors.append(_error(label, ["properties", "pilot_email"], "No pilot with this email", "pilot_not_found", props.pilot_email))
    else:
        drone = await Queries.Drone.get_pilot_drone_by_serial(props.drone_serial, pilot.id, db)
        if drone is None:
            errors.append(_error(
                label, ["properties", "drone_serial"], "The pilot has no drone with this serial number", "drone_not_found", props.drone_serial,
            ))
        else:
            drone_id = drone.id

    point = feature.geometry.coordinate
    country = await Queries.Country.get_by_coordinates(point.lon, point.lat, db)
    if country is None:
        errors.append(_error(
            label, ["geometry", "coordinates"], "The home point is outside every synced country border", "outside_borders",
            feature.geometry.coordinates,
        ))

    if errors:
        return {}, errors

    return {
        "external_id": props.external_id,
        "pilot_id": pilot.id, # type: ignore[union-attr]
        "drone_id": drone_id,
        "country_id": country.id, # type: ignore[union-attr]
        "flying_privilege": props.flying_privilege,
        "category": OperationalCategory.OPEN if props.flying_privilege in _OPEN_PRIVILEGES else OperationalCategory.SPECIFIC,
        "status": MissionStatus(props.status),
        "decision_reason": props.decision_reason,
        "home_point": Point(point.lon, point.lat),
        "height": props.height,
        "range": props.range,
        "starts_at": props.starts_at,
        "ends_at": props.ends_at,
        "time": props.duration * 60,
        "flight_goal": props.flight_goal,
        "description": props.description,
        "spotter_first_name": props.spotter_first_name,
        "spotter_last_name": props.spotter_last_name,
        "spotter_phone": props.spotter_phone,
    }, []


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
