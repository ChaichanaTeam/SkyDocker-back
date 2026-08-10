from fastapi import APIRouter
from sqlalchemy import select

from backend_src.api.dependencies import CurrentPilot
from backend_src.db import AsyncDBDep
from backend_src.models.model import Pilot
from backend_src.schemas.pilot import (
    PilotRead,
    PilotPublicRead,
    PilotUpdate,
    ChangePasswordRequest,
)


router = APIRouter(prefix="/pilots", tags=["pilots"])


@router.get("/me", response_model=PilotRead)
async def get_me(pilot: CurrentPilot, db: AsyncDBDep):
    return pilot


@router.patch("/me", response_model=PilotRead)
async def update_me(data: PilotUpdate, pilot: CurrentPilot, db: AsyncDBDep):
    return pilot


@router.patch("/me/change-password")
async def change_password(data: ChangePasswordRequest, pilot: CurrentPilot, db: AsyncDBDep):
    return pilot


@router.get("/{pilot_id}", response_model=PilotPublicRead)
async def get_pilot_public_info(pilot_id: int, pilot: CurrentPilot, db: AsyncDBDep):
    result = await db.execute(select(Pilot).where(Pilot.id == pilot_id))
    target = result.scalar_one_or_none()
    return target