from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis_fastapi import AsyncRedisDep
from loguru import logger

from backend_src.api.shared_schemas import BoundingBox, normalize_email
from backend_src.cache import AsyncRedisSession, get_session_gen
from backend_src.db import Queries, AsyncDBSession, AsyncSessionMaker
from backend_src.core.security import EmailTokenPayload, TokenType, decode_token
from backend_src.models import Pilot
from backend_src.api.exceptions import APIExceptions


bearer_scheme = HTTPBearer()


HeaderAuthorization = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


async def get_db() -> AsyncGenerator[AsyncDBSession, None]:
    db: AsyncDBSession = AsyncSessionMaker()
    try:
        yield db
    finally:
        await db.close()

AsyncDBDep = Annotated[AsyncDBSession, Depends(get_db)]

BoundingBoxQuery = Annotated[BoundingBox, Query(...)]


async def _pilot_from_token(
    db: AsyncDBSession,
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType,
    redis: Optional[AsyncRedisSession] = None,
) -> Pilot:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.type != expected_type.value:
        raise APIExceptions.credentials_exception

    pilot_id = payload.sub
    if pilot_id is None:
        raise APIExceptions.credentials_exception

    # Tokens from before a password reset carry an outdated generation
    if redis is not None and payload.gen != await get_session_gen(redis, pilot_id):
        raise APIExceptions.credentials_exception

    pilot = await Queries.Pilot.get_by_id(int(pilot_id), db)
    if pilot is None:
        raise APIExceptions.credentials_exception

    return pilot


async def _email_from_token(
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType
) -> EmailTokenPayload:
    payload = decode_token(credentials.credentials, EmailTokenPayload)
    
    if payload is None or payload.type != expected_type.value:
        raise APIExceptions.credentials_exception

    if normalize_email(payload.email) != payload.sub:
        raise APIExceptions.credentials_exception

    return payload


async def get_current_pilot(
    db: AsyncDBDep,
    redis: AsyncRedisDep,
    credentials: HeaderAuthorization,
) -> Pilot:
    return await _pilot_from_token(db, credentials, TokenType.ACCESS, redis)


async def get_verify_subject(
    credentials: HeaderAuthorization,
) -> str:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.type != TokenType.VERIFY.value:
        raise APIExceptions.credentials_exception

    return payload.sub


async def get_reset_pilot(
    db: AsyncDBDep,
    redis: AsyncRedisDep,
    credentials: HeaderAuthorization,
) -> Pilot:
    return await _pilot_from_token(db, credentials, TokenType.RESET, redis)


async def get_register_email(
        credentials: HeaderAuthorization
) -> EmailTokenPayload:
    return await _email_from_token(credentials, TokenType.REGISTER)


async def get_verify_email(
        credentials: HeaderAuthorization
) -> EmailTokenPayload:
    return await _email_from_token(credentials, TokenType.VERIFY)


CurrentPilot = Annotated[Pilot, Depends(get_current_pilot)]
VerifySubject = Annotated[str, Depends(get_verify_subject)]
ResetPilot = Annotated[Pilot, Depends(get_reset_pilot)]
RegisterEmail = Annotated[EmailTokenPayload, Depends(get_register_email)]
VerifyEmail = Annotated[EmailTokenPayload, Depends(get_verify_email)]