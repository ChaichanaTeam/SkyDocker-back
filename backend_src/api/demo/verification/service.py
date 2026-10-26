from typing import Any, Optional

from sqlalchemy import select

from backend_src.api.exceptions import APIExceptions
from backend_src.api.shared_schemas import normalize_email
from backend_src.api.v1.verification import service as live
from backend_src.api.v1.verification.schema import VerificationForm, VerificationRequestRead
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    Pilot, PilotToFlyingPrivileges, VerificationRequest,
    FlyingPrivileges, VerificationRequestStatus
)
from backend_src.storage import Storage, VERIFICATION_BUCKET
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

    return pilot


async def _pending_request(request_id: int, db: AsyncDBSession) -> VerificationRequest:
    request = await live.get_request(request_id, db)
    if request.status != VerificationRequestStatus.PENDING:
        raise APIExceptions.conflict(f"Only a pending request can be reviewed, this one is {request.status}")

    return request


async def create_request(form: VerificationForm, email: Optional[str], db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    pilot = await _resolve_pilot(db, email)
    return await live.create_request(form, pilot, db, storage)


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


async def approve_request(request_id: int, db: AsyncDBSession) -> dict[str, Any]:
    request = await _pending_request(request_id, db)

    privileges = {
        FlyingPrivileges(document.document_type.removeprefix(_PRIVILEGE_PREFIX))
        for document in request.verification_document
        if document.document_type.startswith(_PRIVILEGE_PREFIX)
    }
    existing = set((
        await db.execute(
            select(PilotToFlyingPrivileges.flying_privilege)
            .where(PilotToFlyingPrivileges.pilot_id == request.pilot_id)
        )
    ).scalars().all())
    granted = sorted(privileges - existing)

    db.add_all(
        PilotToFlyingPrivileges(pilot_id=request.pilot_id, flying_privilege=privilege) for privilege in granted
    )

    pilot = await Queries.Pilot.get_by_id(request.pilot_id, db)
    pilot.pilot_number = request.pilot_number # type: ignore
    request.status = VerificationRequestStatus.APPROVED
    await db.commit()

    return {
        "request": VerificationRequestRead.model_validate(await live.get_request(request_id, db)),
        "granted": granted,
        "privileges": sorted(existing | privileges),
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
