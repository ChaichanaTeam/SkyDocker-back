from typing import Any, Optional

from fastapi import Request, UploadFile
from sqlalchemy.exc import IntegrityError
from starlette.datastructures import FormData, UploadFile as StarletteUploadFile

from backend_src.api.exceptions import APIExceptions, EntityError
from backend_src.cache import (
    AsyncRedisSession, claim_verification_token, is_verification_token_used, release_verification_token
)
from backend_src.core import security
from backend_src.core.config import Settings
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    Pilot, VerificationDocument, VerificationRequest,
    VerificationDocumentType, VerificationRequestStatus
)
from backend_src.storage import (
    Document, DocumentTooLarge, Storage, UnsupportedDocument,
    MAX_DOCUMENTS, MAX_DOCUMENT_SIZE, MULTIPART_OVERHEAD, ORGANIZER_BUCKET, VERIFICATION_BUCKET,
    check_document_size, detect_document_format, organizer_key, verification_key
)
from .schema import (
    VerificationPlan, VerificationPreviewRequest, VerificationRequestRead,
    VerificationTokenPayload, VerificationTokenResponse
)


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
