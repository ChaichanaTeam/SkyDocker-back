from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, Response

from backend_src.api.dependencies import AsyncDBDep, AsyncRedisDep, CurrentModerator
from backend_src.cache import rate_limit
from . import docs
from . import service
from .constants import RateLimits, REFRESH_COOKIE_NAME
from .schema import ModeratorLogin, ModeratorProfile


router = APIRouter(prefix="/moderator", **docs.ROUTER)

RefreshCookie = Annotated[Optional[str], Cookie(alias=REFRESH_COOKIE_NAME)]


@router.post("/auth/login", dependencies=[Depends(rate_limit(RateLimits.LOGIN))], **docs.LOGIN)
async def login(data: ModeratorLogin, db: AsyncDBDep, redis: AsyncRedisDep, response: Response):
    return await service.login(data, db, redis, response)


@router.post("/auth/refresh", dependencies=[Depends(rate_limit(RateLimits.REFRESH))], **docs.REFRESH)
async def refresh(db: AsyncDBDep, redis: AsyncRedisDep, response: Response, token: RefreshCookie = None):
    return await service.refresh(token, db, redis, response)


@router.post("/auth/logout", dependencies=[Depends(rate_limit(RateLimits.LOGOUT))], **docs.LOGOUT)
async def logout(redis: AsyncRedisDep, response: Response, token: RefreshCookie = None):
    return await service.logout(token, redis, response)


@router.get("/me", **docs.GET_ME)
async def get_me(moderator: CurrentModerator):
    return ModeratorProfile.model_validate(moderator)
