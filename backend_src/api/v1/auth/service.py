from typing import Optional

from sqlalchemy.exc import IntegrityError

from backend_src.cache import AsyncRedisSession
from backend_src.cache.otp import check_otp, issue_otp
from backend_src.cache.sessions import (
    get_session_gen,
    pop_refresh_session,
    revoke_all_sessions,
    revoke_refresh_session,
    store_refresh_session,
    verify_refresh_token
)
from backend_src.core import security
from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from .schema import (
    ForgotPasswordRequest, PilotLogin, PilotRegister,
    RefreshTokenRequest, RegisterRequestOTP, RegisterVerifyOTP,
    ResetPasswordRequest, VerifyResetTokenRequest,
    TokenPair, BearerToken
)
from backend_src.models import Pilot
from backend_src.api.shared_schemas import normalize_email


def verify_pilot(pilot: Optional[Pilot], password: str) -> bool:
    return pilot is not None and \
        security.verify_password(password, pilot.password_hash)


def verify_token(payload: Optional[security.TokenPayload], type: security.TokenType) -> bool:
    return payload is not None and \
        payload.type == type


async def issue_token_pair(subject: str, redis: AsyncRedisSession) -> TokenPair:
    gen = await get_session_gen(redis, subject)
    access = security.create_access_token(subject, gen)
    refresh = security.create_refresh_token(subject, gen)

    await store_refresh_session(redis, subject, refresh)

    return TokenPair.from_tokens(access, refresh)


async def login(data: PilotLogin, db: AsyncDBSession, redis: AsyncRedisSession):
    pilot = await Queries.Pilot.get_by_email(data.email, db)

    if not verify_pilot(pilot, data.password):
        raise APIExceptions.unauthorized("Invalid email or password")

    return await issue_token_pair(str(pilot.id), redis) # type: ignore


async def refresh(data: RefreshTokenRequest, db: AsyncDBSession, redis: AsyncRedisSession):
    payload = security.decode_token(data.refresh_token)
    if not verify_token(payload, security.TokenType.REFRESH):
        raise APIExceptions.unauthorized("Invalid refresh token")

    pilot_id, jti = payload.sub, payload.jti # type: ignore

    stored_hash = await pop_refresh_session(redis, pilot_id, jti)
    if stored_hash is None:
        raise APIExceptions.unauthorized("Refresh token expired, revoked, or already used")

    if not verify_refresh_token(stored_hash, data.refresh_token):
        raise APIExceptions.unauthorized("Invalid refresh token")

    pilot = await Queries.Pilot.get_by_id(int(pilot_id), db)
    if pilot is None:
        raise APIExceptions.unauthorized("Pilot not found")

    return await issue_token_pair(pilot_id, redis)


async def logout(data: RefreshTokenRequest, redis: AsyncRedisSession):
    payload = security.decode_token(data.refresh_token)

    if verify_token(payload, security.TokenType.REFRESH):
        await revoke_refresh_session(redis, payload.sub, payload.jti) # type: ignore

    return {"message": "Logged out"}


async def register_request_otp(data: RegisterRequestOTP, redis: AsyncRedisSession, db: AsyncDBSession):
    normalized = normalize_email(data.email)
    pilot = await Queries.Pilot.get_by_email(normalized, db)
    if pilot is not None:
        raise APIExceptions.conflict("Email already registered")

    await issue_otp(redis, "verify", normalized)
    verify = security.create_register_verify_token(normalized, data.email)

    return BearerToken(token=verify.token)


async def register_verify_otp(data: RegisterVerifyOTP, redis: AsyncRedisSession, email_payload: security.EmailTokenPayload):
    if not await check_otp(redis, "verify", email_payload.sub, data.code):
        raise APIExceptions.bad_request("Invalid or expired code")

    register = security.create_register_token(email_payload.sub, email_payload.email)

    return BearerToken(token=register.token)


async def register(data: PilotRegister, db: AsyncDBSession, redis: AsyncRedisSession, email_payload: security.EmailTokenPayload):
    result = await Queries.Pilot.get_by_email(email_payload.sub, db)

    if result is not None:
        raise APIExceptions.conflict("Email already registered")

    pilot = Pilot(
        normalized_email=email_payload.sub,
        email=email_payload.email,
        phone_number=data.phone_number,
        password_hash=security.hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name
    )

    try:
        db.add(pilot)
        await db.commit()
        await db.refresh(pilot)
    except IntegrityError:
        await db.rollback()
        raise APIExceptions.conflict("Email already registered")

    return await issue_token_pair(str(pilot.id), redis)


async def forgot_password(data: ForgotPasswordRequest, db: AsyncDBSession, redis: AsyncRedisSession):
    pilot = await Queries.Pilot.get_by_email(data.email, db)
    if pilot is None:
        raise APIExceptions.not_found("Pilot not found")

    pilot_id = str(pilot.id)

    await issue_otp(redis, "reset", pilot_id)
    verify = security.create_verify_token(pilot_id)

    return BearerToken(token=verify.token)


async def verify_reset_token(data: VerifyResetTokenRequest, redis: AsyncRedisSession, pilot: Pilot):
    pilot_id = str(pilot.id)

    if not await check_otp(redis, "reset", pilot_id, data.code):
        raise APIExceptions.bad_request("Invalid or expired code")

    gen = await get_session_gen(redis, pilot_id)
    reset = security.create_reset_token(pilot_id, gen)
    return BearerToken(token=reset.token)


async def reset_password(data: ResetPasswordRequest, db: AsyncDBSession, redis: AsyncRedisSession, pilot: Pilot):
    pilot.password_hash = security.hash_password(data.new_password)
    pilot_id = str(pilot.id)
    await db.commit()

    await revoke_all_sessions(redis, pilot_id)
    return await issue_token_pair(pilot_id, redis)
