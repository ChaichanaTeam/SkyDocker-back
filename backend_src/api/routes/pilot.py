from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend_src.db.dependencies import get_db
from backend_src.models.model import Pilot
from backend_src.schemas.pilot import (
    PilotRead,
    PilotPublicRead,
    PilotUpdate,
    ChangePasswordRequest,
)


router = APIRouter(prefix="/pilots", tags=["pilots"])


@router.get("/me", response_model=PilotRead)
async def get_me(pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    return pilot


@router.patch("/me", response_model=PilotRead)
async def update_me(data: PilotUpdate, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    return pilot


@router.patch("/me/change-password")
async def change_password(data: ChangePasswordRequest, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    return pilot


@router.get("/{pilot_id}", response_model=PilotPublicRead)
async def get_pilot_public_info(pilot_id: int, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    return pilot