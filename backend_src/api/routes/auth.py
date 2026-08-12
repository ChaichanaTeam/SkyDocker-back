import email
import hashlib
from loguru import logger
from fastapi import APIRouter
from sqlalchemy import select
from redis_fastapi import AsyncRedisDep

from backend_src.api.dependencies import ResetPilot, VerifyPilot
from backend_src.core.config import Settings
from backend_src.core.security import (
    IssuedToken,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    create_verify_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend_src.db import AsyncDBDep
from backend_src.models.model import Pilot
from backend_src.schemas.auth import BearerToken, RefreshTokenRequest, TokenPair
from backend_src.schemas.pilot import (
    PilotLogin,
    PilotRegister,
    RegisterVerifyOTP,
    ForgotPasswordRequest,
    VerifyResetTokenRequest,
    ResetPasswordRequest,
)
from backend_src.db import Queries
from backend_src.core.exceptions import APIExceptions
from backend_src.api.docs import Auth


router = APIRouter(prefix="/auth", tags=["auth"])


REFRESH_TTL_SECONDS = Settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
ACCESS_TTL_SECONDS = Settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
OTP_TTL_SECONDS = Settings.VERIFY_TOKEN_EXPIRE_MINUTES * 60


def _refresh_redis_key(pilot_id: int, jti: str) -> str:
    return f"refresh:{pilot_id}:{jti}"


def _otp_redis_key(purpose: str, pilot_id: int) -> str:
    return f"otp:{purpose}:{pilot_id}"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _store_refresh_session(redis: AsyncRedisDep, pilot_id: int, refresh: IssuedToken) -> None:
    await redis.set(
        _refresh_redis_key(pilot_id, refresh.jti),
        _hash_token(refresh.token),
        ex=REFRESH_TTL_SECONDS,
    )


def _issue_token_pair(access: IssuedToken, refresh: IssuedToken) -> TokenPair:
    return TokenPair(
        access_token=access.token,
        refresh_token=refresh.token,
        expires_in=ACCESS_TTL_SECONDS,
    )


def _generate_otp_code() -> str:
    return Settings.OTP_CODE


async def _issue_otp(redis: AsyncRedisDep, purpose: str, pilot_id: int) -> None:
    code = _generate_otp_code()
    await redis.set(_otp_redis_key(purpose, pilot_id), _hash_token(code), ex=OTP_TTL_SECONDS)
    logger.info("OTP code ({purpose}) for pilot {pilot_id}: {code}")


async def _check_otp(redis: AsyncRedisDep, purpose: str, pilot_id: int, code: str) -> bool:
    stored_hash = await redis.getdel(_otp_redis_key(purpose, pilot_id))
    if stored_hash is None:
        return False
    
    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    return stored_hash == _hash_token(code)


@router.post("/login", **Auth.LOGIN)
async def login(data: PilotLogin, db: AsyncDBDep, redis: AsyncRedisDep):
    result = await Queries.Pilot.get_by_email(data.email, db)
    pilot = result.scalar_one_or_none()

    if pilot is None or not verify_password(data.password, pilot.password_hash):
        raise APIExceptions.unauthorized("Invalid email or password")

    access = create_access_token(pilot.id)
    refresh = create_refresh_token(pilot.id)

    await _store_refresh_session(redis, pilot.id, refresh)

    return _issue_token_pair(access, refresh)


@router.post("/refresh", **Auth.REFRESH)
async def refresh(data: RefreshTokenRequest, db: AsyncDBDep, redis: AsyncRedisDep):
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise APIExceptions.unauthorized("Invalid refresh token")

    pilot_id = int(payload["sub"])
    jti = payload["jti"]

    stored_hash = await redis.getdel(_refresh_redis_key(pilot_id, jti))
    if stored_hash is None:
        raise APIExceptions.unauthorized("Refresh token expired, revoked, or already used")

    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    if stored_hash != _hash_token(data.refresh_token):
        raise APIExceptions.unauthorized("Invalid refresh token")

    result = await Queries.Pilot.get_by_id(pilot_id, db)
    pilot = result.scalar_one_or_none()
    if pilot is None:
        raise APIExceptions.unauthorized("Pilot not found")

    access = create_access_token(pilot.id)
    new_refresh = create_refresh_token(pilot.id)
    await _store_refresh_session(redis, pilot.id, new_refresh)

    return _issue_token_pair(access, new_refresh)


@router.post("/logout", **Auth.LOGOUT)
async def logout(data: RefreshTokenRequest, redis: AsyncRedisDep):
    payload = decode_token(data.refresh_token)

    if payload is not None and payload.get("type") == "refresh":
        pilot_id = payload.get("sub")
        jti = payload.get("jti")

        if pilot_id is not None and jti is not None:
            await redis.delete(_refresh_redis_key(int(pilot_id), jti))

    return {"message": "Logged out"}


@router.post("/register", **Auth.REGISTER)
async def register(data: PilotRegister, db: AsyncDBDep, redis: AsyncRedisDep):
    result = await Queries.Pilot.get_by_email(data.email, db)
    if result.scalar_one_or_none() is not None:
        raise APIExceptions.conflict("Email already registered")

    pilot = Pilot(
        email=data.email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        country_id=1
    )
    db.add(pilot)
    await db.commit()
    await db.refresh(pilot)

    await _issue_otp(redis, "register", pilot.id)
    verify = create_verify_token(pilot.id)

    return BearerToken(token=verify.token)


@router.post("/register/verify-otp", **Auth.VERIFY_OTP)
async def register_verify_otp(data: RegisterVerifyOTP, redis: AsyncRedisDep, pilot: VerifyPilot):
    if not await _check_otp(redis, "register", pilot.id, data.code):
        raise APIExceptions.bad_request("Invalid or expired code")

    pilot_id = pilot.id
    
    access = create_access_token(pilot_id)
    refresh = create_refresh_token(pilot_id)
    await _store_refresh_session(redis, pilot_id, refresh)

    return _issue_token_pair(access, refresh)


@router.post("/forgot-password", **Auth.FORGOT_PASSWORD)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncDBDep, redis: AsyncRedisDep):
    result = await Queries.Pilot.get_by_email(data.email, db)
    pilot = result.scalar_one_or_none()
    if pilot is None:
        raise APIExceptions.not_found("Pilot not found")

    await _issue_otp(redis, "reset", pilot.id)
    verify = create_verify_token(pilot.id)

    return BearerToken(token=verify.token)


@router.post("/verify-reset-token", **Auth.VERIFY_RESET_TOKEN)
async def verify_reset_token(data: VerifyResetTokenRequest, redis: AsyncRedisDep, pilot: VerifyPilot):
    if not await _check_otp(redis, "reset", pilot.id, data.code):
        raise APIExceptions.bad_request("Invalid or expired code")

    reset = create_reset_token(pilot.id)
    return BearerToken(token=reset.token)


@router.patch("/reset-password", **Auth.RESET_PASSWORD)
async def reset_password(data: ResetPasswordRequest, db: AsyncDBDep, redis: AsyncRedisDep, pilot: ResetPilot):
    pilot_id = pilot.id
    pilot.password_hash = hash_password(data.new_password)
    await db.commit()

    access = create_access_token(pilot_id)
    refresh = create_refresh_token(pilot_id)
    await _store_refresh_session(redis, pilot_id, refresh)

    return _issue_token_pair(access, refresh)
