from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import Request, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.datastructures import FormData, UploadFile as StarletteUploadFile

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.cache import (
    AsyncRedisSession, REVIEW_LOCK_TTL_SECONDS, acquire_review_lock, claim_verification_token, get_review_holds,
    is_verification_token_used, release_review_lock, release_verification_token
)
from backend_src.core import security
from backend_src.core.config import Settings
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    AfdModerator, FlyingPrivileges, Pilot, PilotToFlyingPrivileges, VerificationDocument, VerificationRequest,
    VerificationDocumentType, VerificationRequestStatus
)
from backend_src.storage import (
    Document, DocumentTooLarge, Storage, UnsupportedDocument,
    MAX_DOCUMENTS, MAX_DOCUMENT_SIZE, MULTIPART_OVERHEAD, ORGANIZER_BUCKET, VERIFICATION_BUCKET,
    check_document_size, detect_document_format, organizer_key, verification_key
)
from .schema import (
    ReviewHolder, ReviewState, VerificationApprovalResult, VerificationPlan, VerificationPreviewRequest, VerificationQueueItem,
    VerificationRequestRead, VerificationReviewRead,
    VerificationTokenPayload, VerificationTokenResponse
)


_REVIEW_LOCK_KIND = "verification"
_PRIVILEGE_PREFIX = "privilege_"


def verification_error(field: str, msg: str, type: str, input: Any) -> EntityError:
    return {
        "type": f"verification.{type}",
        "loc": ["body", field],
        "msg": msg,
        "input": input,
    }


async def _ensure_no_pending(pilot_id: int, db: AsyncDBSession) -> None:
    if await Queries.Verification.get_pending_by_pilot(pilot_id, db) is not None:
        raise APIExceptions.conflict("Pilot already has a pending verification request")


def _resolve_pilot_number(data: VerificationPreviewRequest, pilot: Pilot) -> tuple[Optional[str], list[EntityError]]:
    has_document = VerificationDocumentType.OPERATOR_NUMBER in data.document_types
    errors: list[EntityError] = []

    if pilot.pilot_number is None:
        if data.pilot_number is None:
            errors.append(verification_error("pilot_number", "Pilot has no number yet, it is required", "pilot_number_required", None))
        if not has_document:
            errors.append(verification_error("document_types", "Pilot has no number yet, operator_number document is required", "operator_number_required", data.document_types))
        return data.pilot_number, errors

    if data.pilot_number is not None:
        errors.append(verification_error("pilot_number", "Pilot already has a number", "pilot_number_already_set", data.pilot_number))
    if has_document:
        errors.append(verification_error("document_types", "Pilot already has a number, operator_number document is not accepted", "operator_number_already_set", data.document_types))
    return pilot.pilot_number, errors


async def preview_request(data: VerificationPreviewRequest, pilot: Pilot, db: AsyncDBSession) -> VerificationTokenResponse:
    pilot_id = pilot.id
    await _ensure_no_pending(pilot_id, db)

    pilot_number, errors = _resolve_pilot_number(data, pilot)
    if errors:
        raise APIExceptions.unprocessable(errors)

    plan = VerificationPlan(**data.model_dump(exclude={"pilot_number"}), pilot_number=pilot_number)
    token = security.create_verification_token(str(pilot_id), VerificationTokenPayload, plan=plan)

    return VerificationTokenResponse(verification_token=token.token, expires_in=Settings.VERIFICATION_TOKEN_EXPIRE_MINUTES * 60)


def _no_verified_request():
    return APIExceptions.not_found("No verified request. Run the preview again")


async def _load_token(token: str, pilot_id: int, redis: AsyncRedisSession) -> VerificationTokenPayload:
    payload = security.decode_token(token, VerificationTokenPayload)
    if payload is None or payload.sub != str(pilot_id) or await is_verification_token_used(redis, payload.jti):
        raise _no_verified_request()

    return payload


def _check_content_length(request: Request, plan: VerificationPlan) -> None:
    limit = len(plan.document_types) * MAX_DOCUMENT_SIZE + MULTIPART_OVERHEAD

    # A chunked body has no length to trust, the limit is enforced before reading it
    if int(request.headers.get("content-length") or limit + 1) > limit:
        raise APIExceptions.content_too_large("Upload is larger than the declared documents allow")


def _match_files(form: FormData, plan: VerificationPlan) -> dict[VerificationDocumentType, UploadFile]:
    types = form.getlist("document_types")
    files = form.getlist("files")
    errors: list[EntityError] = []

    if sorted(types) != sorted(plan.document_types):
        errors.append(verification_error("document_types", "Document types differ from the preview", "document_types_mismatch", types))
    if len(files) != len(types) or not all(isinstance(file, StarletteUploadFile) for file in files):
        errors.append(verification_error("files", "Pass exactly one file for every document type", "files_mismatch", len(files)))

    if errors:
        raise APIExceptions.unprocessable(errors)

    return {VerificationDocumentType(doc_type): file for doc_type, file in zip(types, files)}  # type: ignore[misc]


async def _read_documents(uploads: dict[VerificationDocumentType, UploadFile]) -> dict[VerificationDocumentType, Document]:
    for doc_type, upload in uploads.items():
        try:
            check_document_size(upload)
        except DocumentTooLarge as e:
            raise APIExceptions.content_too_large(f"{doc_type}: {e}")

    formats = {}
    errors: list[EntityError] = []
    for doc_type, upload in uploads.items():
        try:
            formats[doc_type] = await detect_document_format(upload)
        except UnsupportedDocument as e:
            errors.append(verification_error("files", f"{doc_type}: {e}", "unsupported_file", upload.filename))

    if errors:
        raise APIExceptions.unprocessable(errors)

    return {
        doc_type: Document(body=await upload.read(), content_type=formats[doc_type].content_type, ext=formats[doc_type].ext)
        for doc_type, upload in uploads.items()
    }


async def get_request(request_id: int, db: AsyncDBSession) -> VerificationRequest:
    request = await Queries.Verification.get_by_id(request_id, db)
    if request is None:
        raise APIExceptions.not_found("Verification request not found")

    return request


def detach_documents(request: VerificationRequest) -> list[str]:
    # Rows go first: a failed storage delete leaves only files, the bucket TTL removes them
    keys = [document.document_path for document in request.verification_document]
    request.verification_document.clear()

    return keys


async def keep_documents_in_organizer(request: VerificationRequest, storage: Storage) -> list[str]:
    copied: list[str] = []

    try:
        for document in request.verification_document:
            ext = document.document_path.rsplit(".", 1)[-1]
            key = organizer_key(request.pilot_id, document.document_type, ext)
            await storage.copy_object(VERIFICATION_BUCKET, document.document_path, ORGANIZER_BUCKET, key)
            copied.append(key)
    except Exception:
        await storage.delete_objects(ORGANIZER_BUCKET, copied)
        raise

    return copied


async def create_request(
    http_request: Request, token: str, pilot: Pilot, db: AsyncDBSession, redis: AsyncRedisSession, storage: Storage
) -> VerificationRequestRead:
    # Cheapest checks first: the body is not touched until the token and the pending check pass
    pilot_id = pilot.id
    payload = await _load_token(token, pilot_id, redis)
    plan = payload.plan
    await _ensure_no_pending(pilot_id, db)
    _check_content_length(http_request, plan)

    async with http_request.form(max_files=MAX_DOCUMENTS, max_fields=MAX_DOCUMENTS) as form:
        documents = await _read_documents(_match_files(form, plan))

    # Claimed only after the files pass, so a bad file can be replaced without a new preview
    if not await claim_verification_token(redis, payload.jti):
        raise _no_verified_request()

    request = VerificationRequest(
        pilot_id=pilot_id,
        first_name=plan.first_name,
        last_name=plan.last_name,
        phone_number=plan.phone_number,
        pilot_number=plan.pilot_number,
        keep_documents=plan.keep_documents,
    )
    uploaded: list[str] = []

    try:
        db.add(request)
        await db.flush()
        request_id = request.id

        for doc_type, document in documents.items():
            key = verification_key(request_id, doc_type, document.ext)
            await storage.put_object(VERIFICATION_BUCKET, key, document.body, document.content_type)
            uploaded.append(key)

            db.add(VerificationDocument(request_id=request_id, document_path=key, document_type=doc_type))

        await db.commit()
    except Exception as e:
        await db.rollback()
        await storage.delete_objects(VERIFICATION_BUCKET, uploaded)
        await release_verification_token(redis, payload.jti)

        # The partial index catches a concurrent request that passed the check above
        if isinstance(e, IntegrityError):
            raise APIExceptions.conflict("Pilot already has a pending verification request")
        raise

    return VerificationRequestRead.model_validate(await get_request(request_id, db))


async def withdraw_request(request_id: int, pilot: Pilot, db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    request = await Queries.Verification.get_by_id(request_id, db)
    if request is None or request.pilot_id != pilot.id:
        raise APIExceptions.not_found("Verification request not found")

    if request.status != VerificationRequestStatus.PENDING:
        raise APIExceptions.conflict(f"Only a pending request can be withdrawn, this one is {request.status}")

    keys = detach_documents(request)
    request.status = VerificationRequestStatus.WITHDRAWN
    await db.commit()

    await storage.delete_objects(VERIFICATION_BUCKET, keys)

    return VerificationRequestRead.model_validate(await get_request(request_id, db))


async def _held_by_another(holder_id: int, expires_in: int, db: AsyncDBSession):
    holder = await Queries.Moderator.get_by_id(holder_id, db)

    return APIExceptions.conflict({
        "msg": "The request is being reviewed by another moderator",
        "moderator": ReviewHolder.model_validate(holder).model_dump() if holder is not None else None,
        "expires_in": expires_in,
    })


async def open_for_review(
    request_id: int, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession, storage: Storage
) -> VerificationReviewRead:
    request = await get_request(request_id, db)
    result = VerificationReviewRead.model_validate(request)

    # Only a pending request is reviewed, the documents of the others are deleted already
    if request.status == VerificationRequestStatus.PENDING:
        lock = await acquire_review_lock(redis, _REVIEW_LOCK_KIND, request_id, moderator.id, REVIEW_LOCK_TTL_SECONDS)
        if not lock.taken:
            raise await _held_by_another(lock.holder_id, lock.expires_in, db)
        result.review_expires_in = lock.expires_in

    paths = {document.id: document.document_path for document in request.verification_document}
    for document in result.documents:
        document.url = await storage.presigned_get(VERIFICATION_BUCKET, paths[document.id])

    return result


async def release_review(request_id: int, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession) -> dict[str, str]:
    await get_request(request_id, db)

    if not await release_review_lock(redis, _REVIEW_LOCK_KIND, request_id, moderator.id):
        raise APIExceptions.conflict("The request is being reviewed by another moderator")

    return {"message": f"Review of request {request_id} released"}


async def list_requests(
    status: Optional[VerificationRequestStatus], limit: int, offset: int, db: AsyncDBSession, redis: AsyncRedisSession,
) -> list[VerificationQueueItem]:
    requests = await Queries.Verification.get_page(status, limit, offset, db)
    pending = [request.id for request in requests if request.status == VerificationRequestStatus.PENDING]
    holds = await get_review_holds(redis, _REVIEW_LOCK_KIND, pending)
    moderators = {
        moderator.id: moderator
        for moderator in await Queries.Moderator.get_by_ids({hold.holder_id for hold in holds.values()}, db)
    }

    items = []
    for request in requests:
        item = VerificationQueueItem.model_validate(request)
        if (hold := holds.get(request.id)) is not None:
            holder = moderators.get(hold.holder_id)
            item.review = ReviewState(
                moderator=ReviewHolder.model_validate(holder) if holder is not None else None,
                expires_in=hold.expires_in,
            )
        items.append(item)

    return items


async def _decided_by(request_id: int, moderator_id: int, db: AsyncDBSession, redis: AsyncRedisSession) -> VerificationRequest:
    """The pending request locked to the moderator for the decision, as when opening it."""
    request = await get_request(request_id, db)
    if request.status != VerificationRequestStatus.PENDING:
        raise APIExceptions.conflict(f"The request is decided already, it is {request.status}")

    lock = await acquire_review_lock(redis, _REVIEW_LOCK_KIND, request_id, moderator_id, REVIEW_LOCK_TTL_SECONDS)
    if not lock.taken:
        raise await _held_by_another(lock.holder_id, lock.expires_in, db)

    return request


def _check_expiry(privileges: set[FlyingPrivileges], expiry: dict[FlyingPrivileges, date]) -> None:
    today = datetime.now(timezone.utc).date()
    errors: list[EntityError] = []

    for privilege in sorted(privileges - expiry.keys()):
        errors.append(verification_error("privilege_expiry", f"Expiry date of {privilege} is required", "expiry_missing", privilege))
    for privilege in sorted(expiry.keys() - privileges):
        errors.append(verification_error("privilege_expiry", f"Request has no {privilege} certificate", "expiry_unexpected", privilege))
    for privilege, expires_at in expiry.items():
        if expires_at < today:
            errors.append(verification_error("privilege_expiry", f"Certificate {privilege} has already expired", "expiry_in_past", expires_at.isoformat()))

    if errors:
        raise APIExceptions.unprocessable(errors)


async def approve_request(
    request_id: int, expiry: dict[FlyingPrivileges, date], moderator: AfdModerator,
    db: AsyncDBSession, redis: AsyncRedisSession, storage: Storage,
) -> VerificationApprovalResult:
    moderator_id = moderator.id
    request = await _decided_by(request_id, moderator_id, db, redis)

    privileges = {
        FlyingPrivileges(document.document_type.removeprefix(_PRIVILEGE_PREFIX))
        for document in request.verification_document
        if document.document_type.startswith(_PRIVILEGE_PREFIX)
    }
    # a wrong date keeps the lock, the moderator fixes it and approves again
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

    kept = await keep_documents_in_organizer(request, storage) if request.keep_documents else []

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

        keys = detach_documents(request)
        request.status = VerificationRequestStatus.APPROVED
        request.verified_by = moderator_id
        await db.commit()
    except Exception:
        await db.rollback()
        await storage.delete_objects(ORGANIZER_BUCKET, kept)
        raise

    await storage.delete_objects(VERIFICATION_BUCKET, keys)
    await release_review_lock(redis, _REVIEW_LOCK_KIND, request_id, moderator_id)

    return VerificationApprovalResult(
        request=VerificationRequestRead.model_validate(await get_request(request_id, db)),
        granted=granted,
        renewed=renewed,
        privileges=held,
        kept_documents=kept,
    )


async def reject_request(
    request_id: int, reason: str, moderator: AfdModerator, db: AsyncDBSession, redis: AsyncRedisSession, storage: Storage,
) -> VerificationRequestRead:
    moderator_id = moderator.id
    request = await _decided_by(request_id, moderator_id, db, redis)

    keys = detach_documents(request)
    request.status = VerificationRequestStatus.REJECTED
    request.reason = reason
    request.verified_by = moderator_id
    await db.commit()

    await storage.delete_objects(VERIFICATION_BUCKET, keys)
    await release_review_lock(redis, _REVIEW_LOCK_KIND, request_id, moderator_id)

    return VerificationRequestRead.model_validate(await get_request(request_id, db))
