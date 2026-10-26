from typing import Annotated

from fastapi import APIRouter, Depends

from backend_src.api.dependencies import AsyncDBDep, CurrentPilot, StorageDep
from backend_src.cache import rate_limit
from . import docs
from . import service
from .constants import RateLimits
from .schema import VerificationForm, verification_form


router = APIRouter(prefix="/verification-requests", **docs.ROUTER)


@router.post("/", dependencies=[Depends(rate_limit(RateLimits.CREATE_REQUEST))], **docs.CREATE_REQUEST)
async def create_request(
    form: Annotated[VerificationForm, Depends(verification_form)],
    pilot: CurrentPilot, db: AsyncDBDep, storage: StorageDep
):
    return await service.create_request(form, pilot, db, storage)


@router.post("/{request_id}/withdraw", dependencies=[Depends(rate_limit(RateLimits.WITHDRAW_REQUEST))], **docs.WITHDRAW_REQUEST)
async def withdraw_request(request_id: int, pilot: CurrentPilot, db: AsyncDBDep, storage: StorageDep):
    return await service.withdraw_request(request_id, pilot, db, storage)
