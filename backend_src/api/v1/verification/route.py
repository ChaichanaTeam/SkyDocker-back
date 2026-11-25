from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request
from redis_fastapi import AsyncRedisDep

from backend_src.api.dependencies import AsyncDBDep, CurrentModerator, CurrentPilot, StorageDep
from backend_src.cache import rate_limit
from . import docs
from . import service
from backend_src.models import VerificationRequestStatus
from .constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, RateLimits
from .schema import VerificationPreviewRequest, VerificationToken


router = APIRouter(prefix="/verification-requests", **docs.ROUTER)


@router.post("/preview", dependencies=[Depends(rate_limit(RateLimits.PREVIEW_REQUEST))], **docs.PREVIEW_REQUEST)
async def preview_request(data: VerificationPreviewRequest, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.preview_request(data, pilot, db)


# Files are read from the request by hand: a declared File() is parsed before auth and the token check
@router.post("/", dependencies=[Depends(rate_limit(RateLimits.CREATE_REQUEST))], **docs.CREATE_REQUEST)
async def create_request(
    request: Request, token: VerificationToken,
    pilot: CurrentPilot, db: AsyncDBDep, redis: AsyncRedisDep, storage: StorageDep
):
    return await service.create_request(request, token, pilot, db, redis, storage)


@router.post("/{request_id}/withdraw", dependencies=[Depends(rate_limit(RateLimits.WITHDRAW_REQUEST))], **docs.WITHDRAW_REQUEST)
async def withdraw_request(request_id: int, pilot: CurrentPilot, db: AsyncDBDep, storage: StorageDep):
    return await service.withdraw_request(request_id, pilot, db, storage)


Limit = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Query(ge=0)]


@router.get("/", **docs.LIST_REQUESTS)
async def list_requests(
    moderator: CurrentModerator, db: AsyncDBDep, redis: AsyncRedisDep,
    status: Optional[VerificationRequestStatus] = None, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0,
):
    return await service.list_requests(status, limit, offset, db, redis)


@router.get("/{request_id}", **docs.GET_REQUEST)
async def open_for_review(request_id: int, moderator: CurrentModerator, db: AsyncDBDep, redis: AsyncRedisDep, storage: StorageDep):
    return await service.open_for_review(request_id, moderator, db, redis, storage)


@router.delete("/{request_id}/review", **docs.RELEASE_REVIEW)
async def release_review(request_id: int, moderator: CurrentModerator, db: AsyncDBDep, redis: AsyncRedisDep):
    return await service.release_review(request_id, moderator, db, redis)
