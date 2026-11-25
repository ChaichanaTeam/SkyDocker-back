import secrets
from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, Query
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic_extra_types.country import CountryAlpha2
from redis_fastapi import AsyncRedisDep
from loguru import logger

from backend_src.api.shared_schemas import BoundingBox, Coordinate, normalize_email
from backend_src.cache import AsyncRedisSession, get_session_gen, MODERATOR_SCOPE
from backend_src.db import Queries, AsyncDBSession, AsyncSessionMaker
from backend_src.core.config import Settings
from backend_src.core.security import EmailTokenPayload, TokenType, decode_token
from backend_src.models import Pilot, Country, AfdModerator
from backend_src.storage import Storage, get_storage
from backend_src.api.exceptions import APIExceptions


bearer_scheme = HTTPBearer()
moderator_bearer_scheme = HTTPBearer(scheme_name="ModeratorBearer")
admin_key_scheme = APIKeyHeader(name="X-Admin-Key", auto_error=False)


HeaderAuthorization = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
ModeratorAuthorization = Annotated[HTTPAuthorizationCredentials, Depends(moderator_bearer_scheme)]


async def get_db() -> AsyncGenerator[AsyncDBSession, None]:
    db: AsyncDBSession = AsyncSessionMaker()
    try:
        yield db
    finally:
        await db.close()

AsyncDBDep = Annotated[AsyncDBSession, Depends(get_db)]

StorageDep = Annotated[Storage, Depends(get_storage)]

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


async def get_current_moderator(
    db: AsyncDBDep,
    redis: AsyncRedisDep,
    credentials: ModeratorAuthorization,
) -> AfdModerator:
    # Only moderator access tokens pass, pilot tokens carry another type
    payload = decode_token(credentials.credentials)
    if payload is None or payload.type != TokenType.MODERATOR_ACCESS.value:
        raise APIExceptions.credentials_exception

    if not payload.sub.isdigit():
        raise APIExceptions.credentials_exception

    if payload.gen != await get_session_gen(redis, payload.sub, MODERATOR_SCOPE):
        raise APIExceptions.credentials_exception

    moderator = await Queries.Moderator.get_by_id(int(payload.sub), db)
    if moderator is None:
        raise APIExceptions.credentials_exception

    return moderator


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


async def verify_admin_key(key: Annotated[Optional[str], Depends(admin_key_scheme)]) -> None:
    # Admin endpoints stay closed while ADMIN_API_KEY is not configured
    if not Settings.ADMIN_API_KEY or key is None or not secrets.compare_digest(key, Settings.ADMIN_API_KEY):
        raise APIExceptions.unauthorized("Invalid admin key")


async def get_country_from_tag(
        db: AsyncDBDep,
        country_tag: Annotated[CountryAlpha2, Query()]
) -> Country:
    country = await Queries.Country.get_by_tag(country_tag, db)
    if country is None:
        raise APIExceptions.not_found("Unsupported country")
    return country


CoordinateQuery = Annotated[Coordinate, Query()]
CountryQuery = Annotated[Country, Depends(get_country_from_tag)]
CurrentPilot = Annotated[Pilot, Depends(get_current_pilot)]
CurrentModerator = Annotated[AfdModerator, Depends(get_current_moderator)]
AdminKey = Depends(verify_admin_key)
VerifySubject = Annotated[str, Depends(get_verify_subject)]
ResetPilot = Annotated[Pilot, Depends(get_reset_pilot)]
RegisterEmail = Annotated[EmailTokenPayload, Depends(get_register_email)]
VerifyEmail = Annotated[EmailTokenPayload, Depends(get_verify_email)]