from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from backend_src.api.dependencies import AsyncDBDep, CurrentPilot, StorageDep
from .constants import BIGINT_MAX, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .schema import DroneCreate, DroneUpdate, PilotUpdate
from . import docs
from . import drone_park
from . import service


router = APIRouter(prefix="/pilots", **docs.ROUTER)


EntityId = Annotated[int, Path(ge=1, le=BIGINT_MAX)]
Limit = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Query(ge=0, le=BIGINT_MAX)]


@router.get("/me", **docs.GET_ME)
async def get_me(pilot: CurrentPilot):
    return pilot


@router.patch("/me", **docs.UPDATE_ME)
async def update_me(data: PilotUpdate, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.update_me(data, pilot, db)


@router.get("/me/privileges", **docs.GET_PRIVILEGES)
async def get_privileges(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_privileges(pilot, db)


@router.get("/me/drones", **docs.GET_DRONES)
async def get_drones(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_drones(pilot, db)


@router.post("/me/drones", status_code=status.HTTP_201_CREATED, **docs.ADD_DRONE)
async def add_drone(data: DroneCreate, pilot: CurrentPilot, db: AsyncDBDep):
    return await drone_park.add_drone(data, pilot, db)


@router.get("/me/drones/{drone_id}", **docs.GET_DRONE)
async def get_drone(drone_id: EntityId, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_drone(drone_id, pilot, db)


@router.patch("/me/drones/{drone_id}", **docs.UPDATE_DRONE)
async def update_drone(drone_id: EntityId, data: DroneUpdate, pilot: CurrentPilot, db: AsyncDBDep):
    return await drone_park.update_drone(drone_id, data, pilot, db)


@router.get("/me/missions", **docs.GET_MISSIONS)
async def get_missions(pilot: CurrentPilot, db: AsyncDBDep, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0):
    return await service.get_missions(pilot, limit, offset, db)


@router.get("/me/missions/{mission_id}", **docs.GET_MISSION)
async def get_mission(mission_id: EntityId, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_mission(mission_id, pilot, db)


@router.get("/me/check-ins", **docs.GET_CHECKINS)
async def get_checkins(pilot: CurrentPilot, db: AsyncDBDep, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0):
    return await service.get_checkins(pilot, limit, offset, db)


@router.get("/me/check-ins/active", **docs.GET_ACTIVE_CHECKIN)
async def get_active_checkin(pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_active_checkin(pilot, db)


@router.get("/me/documents", **docs.GET_DOCUMENTS)
async def get_documents(pilot: CurrentPilot, storage: StorageDep):
    return await service.get_documents(pilot, storage)


@router.get("/{pilot_id}", **docs.GET_PUBLIC)
async def get_public(pilot_id: EntityId, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.get_public(pilot_id, pilot, db)
