from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from backend_src.core.security import TokenType, decode_token
from backend_src.db import AsyncDBDep
from backend_src.models import Pilot
from backend_src.core.exceptions import APIExceptions


bearer_scheme = HTTPBearer()


HeaderAuthorization = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


async def _pilot_from_token(
    db: AsyncDBDep,
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType,
) -> Pilot:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != expected_type.value:
        raise APIExceptions.credentials_exception

    pilot_id = payload.get("sub")
    if pilot_id is None:
        raise APIExceptions.credentials_exception

    result = await db.execute(select(Pilot).where(Pilot.id == int(pilot_id)))
    pilot = result.scalar_one_or_none()
    if pilot is None:
        raise APIExceptions.credentials_exception

    return pilot

async def _email_from_token(
    credentials: HTTPAuthorizationCredentials,
    expected_type: TokenType
) -> str:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != expected_type.value:
        raise APIExceptions.credentials_exception

    email = payload.get("sub")
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