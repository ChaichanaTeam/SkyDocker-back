from typing import Annotated, AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis_fastapi import AsyncRedisDep

from backend_src.db import Queries, AsyncDBSession, AsyncSessionMaker
from backend_src.core.security import TokenType, decode_token
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



async def _pilot_from_token(
    db: AsyncDBSession,
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType,
) -> Pilot:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.type != expected_type.value:
        raise APIExceptions.credentials_exception

    pilot_id = payload.sub
    if pilot_id is None:
        raise APIExceptions.credentials_exception

    pilot = await Queries.Pilot.get_by_id(int(pilot_id), db)
    if pilot is None:
        raise APIExceptions.credentials_exception

    return pilot

async def _email_from_token(
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType
) -> str:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.type != expected_type.value:
        raise APIExceptions.credentials_exception

    email = payload.sub
    if email is None:
        raise APIExceptions.credentials_exception

    return email


async def get_current_pilot(
    db: AsyncDBDep,
    credentials: HeaderAuthorization,
) -> Pilot:
    return await _pilot_from_token(db, credentials, TokenType.ACCESS)


async def get_verify_pilot(
    db: AsyncDBDep,
    credentials: HeaderAuthorization,
) -> Pilot:
    return await _pilot_from_token(db, credentials, TokenType.VERIFY)


async def get_reset_pilot(
    db: AsyncDBDep,
    credentials: HeaderAuthorization,
) -> Pilot:
    return await _pilot_from_token(db, credentials, TokenType.RESET)


async def get_register_email(
        credentials: HeaderAuthorization
) -> str:
    return await _email_from_token(credentials, TokenType.REGISTER)


async def get_verify_email(
        credentials: HeaderAuthorization
) -> str:
    return await _email_from_token(credentials, TokenType.VERIFY)


CurrentPilot = Annotated[Pilot, Depends(get_current_pilot)]
VerifyPilot = Annotated[Pilot, Depends(get_verify_pilot)]
ResetPilot = Annotated[Pilot, Depends(get_reset_pilot)]
RegisterEmail = Annotated[str, Depends(get_register_email)]
VerifyEmail = Annotated[str, Depends(get_verify_email)]