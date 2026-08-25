from fastapi import APIRouter, Depends

from backend_src.api.dependencies import RegisterEmail, VerifyEmail, ResetPilot, VerifyPilot, AsyncDBDep, AsyncRedisDep
from backend_src.cache import rate_limit
from . import docs
from .schema import (
    RefreshTokenRequest,
    PilotLogin, PilotRegister,
    RegisterRequestOTP, RegisterVerifyOTP,
    ForgotPasswordRequest, VerifyResetTokenRequest, ResetPasswordRequest, ChangePasswordRequest
)
from . import service
from .constants import RateLimits


router = APIRouter(prefix="/auth", **docs.ROUTER)


@router.post("/login", dependencies=[Depends(rate_limit(RateLimits.LOGIN))], **docs.LOGIN)
async def login(data: PilotLogin, db: AsyncDBDep, redis: AsyncRedisDep):
    return await service.login(data, db, redis)


@router.post("/refresh", dependencies=[Depends(rate_limit(RateLimits.REFRESH))], **docs.REFRESH)
async def refresh(data: RefreshTokenRequest, db: AsyncDBDep, redis: AsyncRedisDep):
    return await service.refresh(data, db, redis)


@router.post("/logout", dependencies=[Depends(rate_limit(RateLimits.LOGOUT))], **docs.LOGOUT)
async def logout(data: RefreshTokenRequest, redis: AsyncRedisDep):
    return await service.logout(data, redis)


@router.post("/register/request-otp", dependencies=[Depends(rate_limit(RateLimits.REGISTER_REQUEST_OTP))], **docs.REGISTER_REQUEST_OTP)
async def register_request_otp(data: RegisterRequestOTP, redis: AsyncRedisDep, db: AsyncDBDep):
    return await service.register_request_otp(data, redis, db)


@router.post("/register/verify-otp", dependencies=[Depends(rate_limit(RateLimits.REGISTER_VERIFY_OTP))], **docs.VERIFY_OTP)
async def register_verify_otp(data: RegisterVerifyOTP, redis: AsyncRedisDep, email: VerifyEmail):
    return await service.register_verify_otp(data, redis, email)


@router.post("/register", dependencies=[Depends(rate_limit(RateLimits.REGISTER))], **docs.REGISTER)
async def register(data: PilotRegister, db: AsyncDBDep, redis: AsyncRedisDep, email: RegisterEmail):
    return await service.register(data, db, redis, email)


@router.post("/forgot-password", dependencies=[Depends(rate_limit(RateLimits.FORGOT_PASSWORD))], **docs.FORGOT_PASSWORD)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncDBDep, redis: AsyncRedisDep):
    return await service.forgot_password(data, db, redis)


@router.post("/verify-reset-token", dependencies=[Depends(rate_limit(RateLimits.VERIFY_RESET_TOKEN))], **docs.VERIFY_RESET_TOKEN)
async def verify_reset_token(data: VerifyResetTokenRequest, redis: AsyncRedisDep, pilot: VerifyPilot):
    return await service.verify_reset_token(data, redis, pilot)


@router.patch("/reset-password", dependencies=[Depends(rate_limit(RateLimits.RESET_PASSWORD))], **docs.RESET_PASSWORD)
async def reset_password(data: ResetPasswordRequest, db: AsyncDBDep, redis: AsyncRedisDep, pilot: ResetPilot):
    return await service.reset_password(data, db, redis, pilot)
