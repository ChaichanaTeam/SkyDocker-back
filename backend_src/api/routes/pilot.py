from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend_src.db.dependencies import get_db
from backend_src.models.model import Pilot
from backend_src.api.utils.auth import get_current_user_cookie
from backend_src.schemas.pilot import(
    PilotLogin,
    PilotRegister,
    PilotVerifyCode,
    PilotRead,
    PilotPublicRead,
    PilotUpdate,
    ChangePasswordRequest
)


router = APIRouter(prefix="/pilots", tags=["pilots"])


# def get_user_base_data(user: User = Depends(get_current_user_cookie), db: Session = Depends(get_db)):
#     return UserService.get_user_base_data(user, db)

@router.get("/me", response_model=PilotRead)
async def get_me(pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot


@router.patch("/me", response_model=PilotRead)
async def update_me(data: PilotUpdate, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot


@router.post("/register", responce_model=PilotRegister)
async def pilot_register(data: PilotRegister, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot


@router.post("/verify")
async def pilot_verify(data: PilotVerifyCode, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot

@router.get("/login", responce_model=Pilot)
async def pilot_login(data: PilotLogin, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot


@router.patch("/me/change-password")
async def change_password(data: ChangePasswordRequest, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot


@router.get("/{pilot_id}", responce_model=PilotPublicRead)
async def get_pilot_public_info(data: id, pilot: Pilot = Depends(get_current_user_cookie), db: AsyncSession = Depends(get_db)):
    return pilot