from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend_src.db.dependencies import get_db
from backend_src.models.model import Pilot
from backend_src.schemas.pilot import (
    PilotLogin,
    PilotRegister,
    RegisterVerifyOTP,
    ForgotPasswordRequest,
    VerifyResetTokenRequest,
    ResetPasswordRequest,
)


router = APIRouter(tags=["auth"])


@router.post("/login")
async def login(data: PilotLogin, db: AsyncSession = Depends(get_db)):
    pass


@router.post("/refresh")
async def refresh(pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    pass


@router.post("/register")
async def register(data: PilotRegister, db: AsyncSession = Depends(get_db)):
    pass


@router.post("/register/verify-otp")
async def register_verify_otp(data: RegisterVerifyOTP, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    pass


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    pass


@router.post("/verify-reset-token")
async def verify_reset_token(data: VerifyResetTokenRequest, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    pass


@router.patch("/reset-password")
async def reset_password(data: ResetPasswordRequest, pilot: Pilot = Depends(), db: AsyncSession = Depends(get_db)):
    pass