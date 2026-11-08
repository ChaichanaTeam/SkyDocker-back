from typing import Optional

from fastapi import APIRouter, Query, Request

from backend_src.api.dependencies import AsyncDBDep, StorageDep
from backend_src.api.shared_schemas import NormalizedEmailStr
from backend_src.api.v1.verification.schema import VerificationPreviewRequest, VerificationToken
from backend_src.models import VerificationRequestStatus
from .schema import VerificationApproval
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
    db: AsyncDBDep, storage: StorageDep,
    email: Optional[NormalizedEmailStr] = _PILOT_EMAIL,
):
    return await service.create_request(request, token, email, db, storage)


@router.get("/", **docs.LIST_REQUESTS)
async def list_requests(db: AsyncDBDep, status: Optional[VerificationRequestStatus] = None):
    return await service.list_requests(status, db)


@router.get("/{request_id}", **docs.GET_REQUEST)
async def get_request(request_id: int, db: AsyncDBDep, storage: StorageDep):
    return await service.get_request(request_id, db, storage)


@router.post("/{request_id}/approve", **docs.APPROVE_REQUEST)
async def approve_request(request_id: int, data: VerificationApproval, db: AsyncDBDep, storage: StorageDep):
    return await service.approve_request(request_id, data.privilege_expiry, db, storage)


@router.post("/{request_id}/reject", **docs.REJECT_REQUEST)
async def reject_request(
    request_id: int, db: AsyncDBDep, storage: StorageDep,
    reason: str = Query(min_length=1, description="Shown to the pilot"),
):
    return await service.reject_request(request_id, reason, db, storage)


@router.delete("/{request_id}", **docs.DELETE_REQUEST)
async def delete_request(request_id: int, db: AsyncDBDep, storage: StorageDep):
    return await service.delete_request(request_id, db, storage)


@router.delete("/", **docs.DELETE_ALL_REQUESTS)
async def delete_all_requests(db: AsyncDBDep, storage: StorageDep):
    return await service.delete_all_requests(db, storage)
