from typing import Union

from shapely.geometry import mapping

from backend_src.api.exceptions import APIExceptions
from backend_src.api.shared_schemas import FeatureProperties, GeoFeature, GeoJson
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import Checkin, Drone, Mission, Pilot, PilotToFlyingPrivileges, VerificationDocumentType
from backend_src.storage import ORGANIZER_BUCKET, Storage, organizer_prefix
from .schema import OrganizerDocumentRead, PilotCheckinProperties, PilotMissionProperties, PilotUpdate


def _feature(flight: Union[Mission, Checkin], properties: FeatureProperties) -> GeoFeature:
    return GeoFeature(geometry=mapping(flight.home_point), properties=properties)


def _mission_feature(mission: Mission) -> GeoFeature:
    return _feature(mission, PilotMissionProperties.from_mission(mission))


def _checkin_feature(checkin: Checkin) -> GeoFeature:
    return _feature(checkin, PilotCheckinProperties.from_checkin(checkin))


async def update_me(data: PilotUpdate, pilot: Pilot, db: AsyncDBSession) -> Pilot:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pilot, field, value)

    await db.commit()
    await db.refresh(pilot)

    return pilot


async def get_public(pilot_id: int, viewer: Pilot, db: AsyncDBSession) -> Pilot:
    target = await Queries.Pilot.get_by_id(pilot_id, db)

    # A hidden profile looks the same as a missing one
    if target is None or not (target.show_to_public or target.id == viewer.id):
        raise APIExceptions.not_found("Pilot not found")

    return target


async def get_privileges(pilot: Pilot, db: AsyncDBSession) -> list[PilotToFlyingPrivileges]:
    return await Queries.Pilot.get_privilege_rows(pilot.id, db)


async def get_drones(pilot: Pilot, db: AsyncDBSession) -> list[Drone]:
    return await Queries.Drone.get_pilot_drones(pilot.id, db)


async def get_drone(drone_id: int, pilot: Pilot, db: AsyncDBSession) -> Drone:
    drone = await Queries.Drone.get_pilot_drone(drone_id, pilot.id, db)
    if drone is None:
        raise APIExceptions.not_found("Drone not found")

    return drone


async def get_missions(pilot: Pilot, limit: int, offset: int, db: AsyncDBSession) -> GeoJson:
    missions = await Queries.Mission.get_pilot_missions(pilot.id, limit, offset, db)

    return GeoJson(features=[_mission_feature(mission) for mission in missions])


async def get_mission(mission_id: int, pilot: Pilot, db: AsyncDBSession) -> GeoFeature:
    mission = await Queries.Mission.get_pilot_mission(mission_id, pilot.id, db)
    if mission is None:
        raise APIExceptions.not_found("Mission not found")

    return _mission_feature(mission)


async def get_checkins(pilot: Pilot, limit: int, offset: int, db: AsyncDBSession) -> GeoJson:
    checkins = await Queries.Checkin.get_pilot_checkins(pilot.id, limit, offset, db)

    return GeoJson(features=[_checkin_feature(checkin) for checkin in checkins])


async def get_documents(pilot: Pilot, storage: Storage) -> list[OrganizerDocumentRead]:
    objects = await storage.list_objects(ORGANIZER_BUCKET, organizer_prefix(pilot.id))
    objects.sort(key=lambda stored: stored.last_modified, reverse=True)

    return [
        OrganizerDocumentRead(
            # pilots/{pilot_id}/{document_type}/{uuid}.{ext}
            document_type=VerificationDocumentType(stored.key.split("/")[2]),
            size=stored.size,
            uploaded_at=stored.last_modified,
            url=await storage.presigned_get(ORGANIZER_BUCKET, stored.key),
        )
        for stored in objects
    ]


async def get_active_checkin(pilot: Pilot, db: AsyncDBSession) -> GeoFeature:
    checkin = await Queries.Checkin.get_active_by_pilot(pilot.id, db)
    if checkin is None:
        raise APIExceptions.not_found("No check-in in progress")

    return _checkin_feature(checkin)
