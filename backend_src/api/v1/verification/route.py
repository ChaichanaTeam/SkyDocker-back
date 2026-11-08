from fastapi import APIRouter, Depends, Request

from backend_src.api.dependencies import AsyncDBDep, CurrentPilot, StorageDep
from backend_src.cache import rate_limit
from . import docs
from . import service
from .constants import RateLimits
from .schema import VerificationPreviewRequest, VerificationToken


router = APIRouter(prefix="/verification-requests", **docs.ROUTER)


@router.post("/preview", dependencies=[Depends(rate_limit(RateLimits.PREVIEW_REQUEST))], **docs.PREVIEW_REQUEST)
async def preview_request(data: VerificationPreviewRequest, pilot: CurrentPilot, db: AsyncDBDep):
    return await service.preview_request(data, pilot, db)


# Files are read from the request by hand: a declared File() is parsed before auth and the token check
@router.post("/", dependencies=[Depends(rate_limit(RateLimits.CREATE_REQUEST))], **docs.CREATE_REQUEST)
async def create_request(
    request: Request, token: VerificationToken,
    pilot: CurrentPilot, db: AsyncDBDep, storage: StorageDep
):
    return await service.create_request(request, token, pilot, db, storage)


@router.post("/{request_id}/withdraw", dependencies=[Depends(rate_limit(RateLimits.WITHDRAW_REQUEST))], **docs.WITHDRAW_REQUEST)
async def withdraw_request(request_id: int, pilot: CurrentPilot, db: AsyncDBDep, storage: StorageDep):
    return await service.withdraw_request(request_id, pilot, db, storage)
