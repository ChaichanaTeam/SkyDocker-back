from typing import Optional

from fastapi import HTTPException, Response

from backend_src.cache import AsyncRedisSession, MODERATOR_SCOPE
from backend_src.cache.sessions import (
    get_session_gen,
    pop_refresh_session,
    revoke_refresh_session,
    store_refresh_session,
    verify_refresh_token
)
from backend_src.core import security
from backend_src.core.config import Settings
from backend_src.api.exceptions import APIExceptions
from backend_src.db import Queries, AsyncDBSession
from backend_src.models import AfdModerator
from .constants import REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from .schema import ModeratorLogin, ModeratorAccessToken


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=MODERATOR_SCOPE.refresh_ttl,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=Settings.MODERATOR_COOKIE_SECURE,
        samesite=Settings.MODERATOR_COOKIE_SAMESITE, # type: ignore[arg-type]
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=Settings.MODERATOR_COOKIE_SECURE,
        samesite=Settings.MODERATOR_COOKIE_SAMESITE, # type: ignore[arg-type]
    )


def _decode_refresh(token: Optional[str]) -> Optional[security.TokenPayload]:
    if not token:
        return None

    payload = security.decode_token(token)
    if payload is None or payload.type != security.TokenType.MODERATOR_REFRESH:
        return None

    return payload


def verify_moderator(moderator: Optional[AfdModerator], password: str) -> bool:
    if moderator is None:
        return security.dummy_verify_password()

    return security.verify_password(password, moderator.password_hash)


async def issue_session(subject: str, redis: AsyncRedisSession, response: Response) -> ModeratorAccessToken:
    gen = await get_session_gen(redis, subject, MODERATOR_SCOPE)
    access = security.create_moderator_access_token(subject, gen)
    refresh = security.create_moderator_refresh_token(subject, gen)

    await store_refresh_session(redis, subject, refresh, MODERATOR_SCOPE)
    _set_refresh_cookie(response, refresh.token)

    return ModeratorAccessToken.from_token(access)


async def login(data: ModeratorLogin, db: AsyncDBSession, redis: AsyncRedisSession, response: Response):
    moderator = await Queries.Moderator.get_by_email(data.email, db)

    if not verify_moderator(moderator, data.password):
        raise APIExceptions.unauthorized("Invalid email or password")

    return await issue_session(str(moderator.id), redis, response) # type: ignore


def _reject_refresh(detail: str) -> HTTPException:
    # The cookie is cleared on any failure, so the dashboard falls back to the login page
    response = Response()
    _clear_refresh_cookie(response)
    return APIExceptions.unauthorized(detail, headers={"set-cookie": response.headers["set-cookie"]})


async def refresh(token: Optional[str], db: AsyncDBSession, redis: AsyncRedisSession, response: Response):
    payload = _decode_refresh(token)
    if payload is None or not payload.sub.isdigit():
        raise _reject_refresh("Invalid refresh token")

    stored_hash = await pop_refresh_session(redis, payload.sub, payload.jti, MODERATOR_SCOPE)
    if stored_hash is None:
        raise _reject_refresh("Refresh token expired, revoked, or already used")

    if not verify_refresh_token(stored_hash, token): # type: ignore[arg-type]
        raise _reject_refresh("Invalid refresh token")

    # A bumped generation means every moderator session was revoked
    if payload.gen != await get_session_gen(redis, payload.sub, MODERATOR_SCOPE):
        raise _reject_refresh("Invalid refresh token")

    moderator = await Queries.Moderator.get_by_id(int(payload.sub), db)
    if moderator is None:
        raise _reject_refresh("Moderator not found")

    return await issue_session(payload.sub, redis, response)


async def logout(token: Optional[str], redis: AsyncRedisSession, response: Response):
    payload = _decode_refresh(token)
    if payload is not None:
        await revoke_refresh_session(redis, payload.sub, payload.jti, MODERATOR_SCOPE)

    _clear_refresh_cookie(response)
    return {"message": "Logged out"}

