import math
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.api.v1.geozone.activity import reachable, schedule_owner, valid_between
from backend_src.api.v1.geozone.constants import FEET_PER_METRE
from backend_src.api.v1.geozone.elevation import ground_elevation
from backend_src.api.v1.geozone.schema import ActivityWindow
from backend_src.db import Queries, AsyncDBSession
from backend_src.db.queries.checkin import TERMINAL_STATUSES
from backend_src.integrations.pansa import height_rule
from backend_src.models import ActivityTime, Country, Drone, FlyingPrivileges, GeoZone
from .schema import CheckinPlan, CheckinPreviewRequest


CheckinError = EntityError


def _checkin_error(field: str, msg: str, type: str, input: Any) -> CheckinError:
    return {
        "type": f"checkin.{type}",
        "loc": ["body", field],
        "msg": msg,
        "input": input,
    }


def _plan_field(data: CheckinPreviewRequest, field: str) -> str:
    return "mission_id" if data.is_mission_related else field


async def check_jurisdiction(data: CheckinPreviewRequest, db: AsyncDBSession) -> Country:
    country = await Queries.Country.get_by_tag(data.country_tag, db)
    if country is None:
        raise APIExceptions.not_found("Cannot verify fly zone. Unsupported country")

    # a flight from outside the country airspace cannot follow its rules
    point = data.home_point
    if not await Queries.GeoZone.exists_at_point(point.lon, point.lat, country.id, db):
        raise APIExceptions.not_found(f"Cannot verify fly zone. Home point is outside {country.name} airspace")

    return country


async def resolve_plan(
    data: CheckinPreviewRequest, pilot_id: int, db: AsyncDBSession,
) -> tuple[Optional[CheckinPlan], list[CheckinError]]:
    if not data.is_mission_related:
        return CheckinPlan(
            country_tag=data.country_tag,
            home_point=data.home_point,
            drone_id=data.drone_id,
            mission_id=None,
            category=data.category,  # type: ignore[arg-type]
            height=data.height,  # type: ignore[arg-type]
            range=data.range,  # type: ignore[arg-type]
            duration=data.duration,  # type: ignore[arg-type]
        ), []

    mission = await Queries.Mission.get_pilot_mission(data.mission_id, pilot_id, db)  # type: ignore[arg-type]
    if mission is None:
        return None, [_checkin_error("mission_id", "No mission of the pilot found", "mission_not_found", data.mission_id)]

    errors: list[CheckinError] = []
    if mission.status in TERMINAL_STATUSES:
        errors.append(_checkin_error("mission_id", f"Mission is already {mission.status}", "mission_closed", data.mission_id))

    if mission.drone_id != data.drone_id:
        errors.append(_checkin_error("drone_id", "Drone differs from the mission drone", "drone_mismatch", data.drone_id))

    plan = CheckinPlan(
        country_tag=data.country_tag,
        home_point=data.home_point,
        drone_id=data.drone_id,
        mission_id=mission.id,
        category=mission.flying_privilege,
        height=mission.height,
        range=mission.range,
        duration=math.ceil(mission.time / 60),
    )
    return plan, errors


async def check_drone(drone_id: int, pilot_id: int, db: AsyncDBSession) -> tuple[Optional[Drone], list[CheckinError]]:
    drone = await Queries.Drone.get_pilot_drone(drone_id, pilot_id, db)
    if drone is None:
        return None, [_checkin_error("drone_id", "No drone of the pilot found", "drone_not_found", drone_id)]

    return drone, []


def check_privilege(data: CheckinPreviewRequest, plan: CheckinPlan, privileges: set[FlyingPrivileges]) -> list[CheckinError]:
    if plan.category in privileges:
        return []

    return [_checkin_error(
        _plan_field(data, "category"), f"Pilot has no {plan.category} privilege to fly", "no_privilege", plan.category,
    )]


async def check_airspace(
    data: CheckinPreviewRequest, plan: CheckinPlan, drone: Drone, starts_at: datetime, db: AsyncDBSession,
) -> list[CheckinError]:
    """Height of the flight against the rules of every zone it reaches while the flight lasts."""
    point = plan.home_point
    try:
        ground = await ground_elevation(point.lon, point.lat, db)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        raise APIExceptions.bad_gateway(f"Ground elevation is unavailable: {exc}")

    if ground is None:
        raise APIExceptions.not_found("Cannot verify fly zone. No ground elevation data for the home point")

    ends_at = starts_at + timedelta(minutes=plan.duration)
    ceiling_ft = math.ceil((ground.metres + plan.height) * FEET_PER_METRE)
    zones = await Queries.GeoZone.get_all_in_radius(point.lon, point.lat, plan.range, ceiling_ft, db)

    owners = {schedule_owner(zone) for zone in zones} - {None}
    windows: dict[int, list[ActivityTime]] = {}
    for window in await Queries.GeoZone.get_windows_ending_after(owners, starts_at, db):
        windows.setdefault(window.geo_zone_id, []).append(window)

    mass_g = drone.mtom_override if drone.mtom_override is not None else drone.model.mtom
    field = _plan_field(data, "height")

    errors: list[CheckinError] = []
    for zone in zones:
        if not _active_during(zone, windows, starts_at, ends_at, ceiling_ft):
            continue

        rule = height_rule(zone.type, zone.source_type, zone.tag, zone.description_en)
        free_m = rule.free_m if rule.free_max_mass_g is None or mass_g <= rule.free_max_mass_g else 0

        if plan.height > rule.max_m:
            errors.append(_checkin_error(
                field, f"Flight above {rule.max_m} m is not allowed in zone {zone.tag}", "zone_prohibited", plan.height,
            ))
        elif not data.is_mission_related and plan.height > free_m:
            errors.append(_checkin_error(
                field, f"Zone {zone.tag} needs the zone manager consent or a mission above {free_m} m",
                "zone_needs_consent", plan.height,
            ))

    return errors


def _active_during(
    zone: GeoZone, windows: dict[int, list[ActivityTime]], starts_at: datetime, ends_at: datetime, ceiling_ft: int,
) -> bool:
    if not valid_between(zone, starts_at, ends_at):
        return False

    owner = schedule_owner(zone)
    if owner is None:
        return True

    return any(
        window.starts_at < ends_at and window.ends_at > starts_at and reachable(window.lower_limit_ft, ceiling_ft)
        for window in (ActivityWindow.from_activity_time(w, zone) for w in windows.get(owner, []))
    )
