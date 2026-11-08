from datetime import datetime, timezone
from shapely.geometry import mapping
from sqlalchemy.exc import IntegrityError

from backend_src.api.shared_schemas import GeoJson, GeoFeature, BoundingBox
from backend_src.api.exceptions import APIExceptions
from backend_src.core import security
from backend_src.core.config import Settings
from backend_src.db import Queries, AsyncDBSession
from backend_src.models import Checkin, MissionStatus, Pilot, Country
from . import verification
from .schema import (
    CheckinCreateRequest, CheckinPreviewRequest, CheckinProperties,
    CheckinTokenPayload, CheckinTokenResponse
)


def _checkin_feature(checkin: Checkin) -> GeoFeature:
    return GeoFeature(geometry=mapping(checkin.home_point), properties=CheckinProperties.from_checkin(checkin))


async def _ensure_no_active(pilot_id: int, db: AsyncDBSession) -> None:
    if await Queries.Checkin.get_active_by_pilot(pilot_id, db) is not None:
        raise APIExceptions.conflict("Check-in already started. End it to start a new one")


async def checkin_bbox(bbox: BoundingBox, country: Country, db: AsyncDBSession):
    checkins = await Queries.Checkin.get_all_by_bbox(*bbox.unpack(), country.id, db)

    if len(checkins) == 0:
        raise APIExceptions.not_found("No checkins in this region")

    return GeoJson(
        features=[_checkin_feature(ch) for ch in checkins]
    )


async def checkin_preview(data: CheckinPreviewRequest, pilot: Pilot, db: AsyncDBSession) -> CheckinTokenResponse:
    pilot_id = pilot.id
    await _ensure_no_active(pilot_id, db)
    country_id = (await verification.check_jurisdiction(data, db)).id

    plan, errors = await verification.resolve_plan(data, pilot_id, db)
    if plan is None:
        raise APIExceptions.unprocessable(errors)

    drone, drone_errors = await verification.check_drone(plan.drone_id, pilot_id, db)
    errors += drone_errors
    errors += verification.check_privilege(data, plan, await Queries.Pilot.get_privileges(pilot_id, db))
    if drone is not None:
        errors += await verification.check_airspace(data, plan, drone, country_id, datetime.now(timezone.utc), db)

    if errors:
        raise APIExceptions.unprocessable(errors)

    token = security.create_checkin_token(str(pilot_id), CheckinTokenPayload, checkin=plan)
    return CheckinTokenResponse(checkin_token=token.token, expires_in=Settings.CHECKIN_TOKEN_EXPIRE_SECONDS)


async def checkin_create(data: CheckinCreateRequest, pilot: Pilot, db: AsyncDBSession) -> GeoFeature:
    pilot_id = pilot.id
    payload = security.decode_token(data.checkin_token, CheckinTokenPayload)
    if payload is None or payload.sub != str(pilot_id):
        raise APIExceptions.not_found("No verified check-in. Run the preview again")

    await _ensure_no_active(pilot_id, db)

    # the plan was verified by the preview and is signed, only the country row is needed
    plan = payload.checkin
    country = await Queries.Country.get_by_tag(plan.country_tag, db)
    if country is None:
        raise APIExceptions.not_found("Cannot verify fly zone. Unsupported country")

    checkin = plan.to_model(pilot_id, country.id, datetime.now(timezone.utc))
    try:
        db.add(checkin)
        await db.flush()
        checkin_id = checkin.id
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise APIExceptions.conflict("Check-in could not be started, its drone or mission is gone")

    created = await Queries.Checkin.get_by_id(checkin_id, db)
    return _checkin_feature(created)  # type: ignore[arg-type]


async def checkin_end(pilot: Pilot, db: AsyncDBSession) -> GeoFeature:
    checkin = await Queries.Checkin.get_active_by_pilot(pilot.id, db)
    if checkin is None:
        raise APIExceptions.not_found("No check-in in progress")

    ends_at = checkin.ends_at
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)

    checkin_id = checkin.id
    checkin.status = MissionStatus.ENDED_INTIME if datetime.now(timezone.utc) <= ends_at else MissionStatus.LATE_END
    await db.commit()

    ended = await Queries.Checkin.get_by_id(checkin_id, db)
    return _checkin_feature(ended)  # type: ignore[arg-type]
