from typing import Optional

from fastapi import APIRouter, Query, Request
from redis_fastapi import AsyncRedisDep

from backend_src.api.dependencies import AsyncDBDep, StorageDep
from backend_src.api.shared_schemas import NormalizedEmailStr
from backend_src.api.v1.verification.schema import VerificationPreviewRequest, VerificationToken
from . import docs
from . import service


router = APIRouter(prefix="/verification-requests", tags=["verification"])


_PILOT_EMAIL = Query(None, description="Email of an existing pilot. Defaults to the demo pilot")


@router.post("/preview", **docs.PREVIEW_REQUEST)
async def preview_request(data: VerificationPreviewRequest, db: AsyncDBDep, email: Optional[NormalizedEmailStr] = _PILOT_EMAIL):
    return await service.preview_request(data, email, db)


@router.post("/", **docs.CREATE_REQUEST)
async def create_request(
    request: Request, token: VerificationToken,
    db: AsyncDBDep, redis: AsyncRedisDep, storage: StorageDep,
    email: Optional[NormalizedEmailStr] = _PILOT_EMAIL,
):
    return await service.create_request(request, token, email, db, redis, storage)


@router.delete("/{request_id}", **docs.DELETE_REQUEST)
async def delete_request(request_id: int, db: AsyncDBDep, storage: StorageDep):
    return await service.delete_request(request_id, db, storage)


@router.delete("/", **docs.DELETE_ALL_REQUESTS)
async def delete_all_requests(db: AsyncDBDep, storage: StorageDep):
    return await service.delete_all_requests(db, storage)
