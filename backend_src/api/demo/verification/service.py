from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import select

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.api.shared_schemas import normalize_email
from backend_src.api.v1.verification import service as live
from backend_src.api.v1.verification.schema import (
    VerificationPreviewRequest, VerificationRequestRead, VerificationTokenResponse
)
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    Pilot, PilotToFlyingPrivileges, VerificationRequest,
    FlyingPrivileges, VerificationRequestStatus
)
from backend_src.storage import ORGANIZER_BUCKET, Storage, VERIFICATION_BUCKET
from backend_src.api.demo.checkin.constants import (
    DEMO_PILOT_EMAIL,
    DEMO_PILOT_FIRST_NAME,
    DEMO_PILOT_LAST_NAME,
    DEMO_PILOT_PHONE,
)


_PRIVILEGE_PREFIX = "privilege_"


async def _resolve_pilot(db: AsyncDBSession, email: Optional[str]) -> Pilot:
    if email is not None:
        pilot = await Queries.Pilot.get_by_email(email, db)
        if pilot is None:
            raise APIExceptions.not_found(f"Pilot {email} not found")
        return pilot

    pilot = await Queries.Pilot.get_by_email(normalize_email(DEMO_PILOT_EMAIL), db)
    if pilot is None:
        pilot = Pilot(
            first_name=DEMO_PILOT_FIRST_NAME,
            last_name=DEMO_PILOT_LAST_NAME,
            email=DEMO_PILOT_EMAIL,
            normalized_email=normalize_email(DEMO_PILOT_EMAIL),
            phone_number=DEMO_PILOT_PHONE,
            password_hash="x"
        )
        db.add(pilot)
        await db.commit()
        await db.refresh(pilot)

    return pilot


async def _pending_request(request_id: int, db: AsyncDBSession) -> VerificationRequest:
    request = await live.get_request(request_id, db)
    if request.status != VerificationRequestStatus.PENDING:
        raise APIExceptions.conflict(f"Only a pending request can be reviewed, this one is {request.status}")

    return request


async def preview_request(data: VerificationPreviewRequest, email: Optional[str], db: AsyncDBSession) -> VerificationTokenResponse:
    pilot = await _resolve_pilot(db, email)
    return await live.preview_request(data, pilot, db)


async def create_request(request: Request, token: str, email: Optional[str], db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    pilot = await _resolve_pilot(db, email)
    return await live.create_request(request, token, pilot, db, storage)


async def list_requests(status: Optional[VerificationRequestStatus], db: AsyncDBSession) -> list[VerificationRequestRead]:
    requests = await Queries.Verification.get_all(status, db)
    return [VerificationRequestRead.model_validate(request) for request in requests]


async def get_request(request_id: int, db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    request = await live.get_request(request_id, db)
    result = VerificationRequestRead.model_validate(request)

    paths = {document.id: document.document_path for document in request.verification_document}
    for document in result.documents:
        document.url = await storage.presigned_get(VERIFICATION_BUCKET, paths[document.id])

    return result


def _check_expiry(privileges: set[FlyingPrivileges], expiry: dict[FlyingPrivileges, date]) -> None:
    today = datetime.now(timezone.utc).date()
    errors: list[EntityError] = []

    for privilege in sorted(privileges - expiry.keys()):
        errors.append(live.verification_error("privilege_expiry", f"Expiry date of {privilege} is required", "expiry_missing", privilege))
    for privilege in sorted(expiry.keys() - privileges):
        errors.append(live.verification_error("privilege_expiry", f"Request has no {privilege} certificate", "expiry_unexpected", privilege))
    for privilege, expires_at in expiry.items():
        if expires_at < today:
            errors.append(live.verification_error("privilege_expiry", f"Certificate {privilege} has already expired", "expiry_in_past", expires_at.isoformat()))

    if errors:
        raise APIExceptions.unprocessable(errors)


async def approve_request(request_id: int, expiry: dict[FlyingPrivileges, date], db: AsyncDBSession, storage: Storage) -> dict[str, Any]:
    request = await _pending_request(request_id, db)

    privileges = {
        FlyingPrivileges(document.document_type.removeprefix(_PRIVILEGE_PREFIX))
        for document in request.verification_document
        if document.document_type.startswith(_PRIVILEGE_PREFIX)
    }
    _check_expiry(privileges, expiry)

    existing = {
        row.flying_privilege: row
        for row in (
            await db.execute(select(PilotToFlyingPrivileges).where(PilotToFlyingPrivileges.pilot_id == request.pilot_id))
        ).scalars().all()
    }
    granted = sorted(privileges - existing.keys())
    renewed = sorted(privileges & existing.keys())
    held = sorted(privileges | existing.keys())

    kept = await live.keep_documents_in_organizer(request, storage) if request.keep_documents else []

    try:
        for privilege in renewed:
            existing[privilege].expires_at = expiry[privilege]
        db.add_all(
            PilotToFlyingPrivileges(pilot_id=request.pilot_id, flying_privilege=privilege, expires_at=expiry[privilege])
            for privilege in granted
        )

        pilot = await Queries.Pilot.get_by_id(request.pilot_id, db)
        pilot.pilot_number = request.pilot_number # type: ignore
        pilot.phone_number = request.phone_number # type: ignore
        pilot.first_name = pilot.first_name or request.first_name # type: ignore
        pilot.last_name = pilot.last_name or request.last_name # type: ignore

        keys = live.detach_documents(request)
        request.status = VerificationRequestStatus.APPROVED
        await db.commit()
    except Exception:
        await db.rollback()
        await storage.delete_objects(ORGANIZER_BUCKET, kept)
        raise

    await storage.delete_objects(VERIFICATION_BUCKET, keys)

    return {
        "request": VerificationRequestRead.model_validate(await live.get_request(request_id, db)),
        "granted": granted,
        "renewed": renewed,
        "privileges": held,
        "kept_documents": kept,
    }


async def reject_request(request_id: int, reason: str, db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    request = await _pending_request(request_id, db)

    keys = live.detach_documents(request)
    request.status = VerificationRequestStatus.REJECTED
    request.reason = reason
    await db.commit()

    await storage.delete_objects(VERIFICATION_BUCKET, keys)

    return VerificationRequestRead.model_validate(await live.get_request(request_id, db))


async def _delete(request: VerificationRequest, db: AsyncDBSession) -> list[str]:
    keys = live.detach_documents(request)
    await db.delete(request)

    return keys


async def delete_request(request_id: int, db: AsyncDBSession, storage: Storage) -> dict[str, Any]:
    request = await live.get_request(request_id, db)
    keys = await _delete(request, db)
    await db.commit()

    await storage.delete_objects(VERIFICATION_BUCKET, keys)

    return {"message": f"Deleted request {request_id} and {len(keys)} document(s)"}


async def delete_all_requests(db: AsyncDBSession, storage: Storage) -> dict[str, Any]:
    requests = await Queries.Verification.get_all(None, db)

    keys: list[str] = []
    for request in requests:
        keys += await _delete(request, db)
    await db.commit()

    await storage.delete_objects(VERIFICATION_BUCKET, keys)

    return {"message": f"Deleted {len(requests)} request(s) and {len(keys)} document(s)"}
