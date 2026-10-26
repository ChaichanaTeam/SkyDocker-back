from sqlalchemy.exc import IntegrityError

from backend_src.api.exceptions import APIExceptions
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import (
    Pilot, VerificationDocument, VerificationRequest,
    VerificationDocumentType, VerificationRequestStatus
)
from backend_src.storage import (
    Document, DocumentTooLarge, Storage, UnsupportedDocument,
    VERIFICATION_BUCKET, read_document, verification_key
)
from .schema import VerificationForm, VerificationRequestRead


async def _read_documents(form: VerificationForm) -> dict[VerificationDocumentType, Document]:
    documents = {}

    for doc_type, upload in form.documents.items():
        try:
            documents[doc_type] = await read_document(upload)
        except DocumentTooLarge as e:
            raise APIExceptions.content_too_large(f"{doc_type}: {e}")
        except UnsupportedDocument as e:
            raise APIExceptions.unprocessable(f"{doc_type}: {e}")

    return documents


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


async def create_request(form: VerificationForm, pilot: Pilot, db: AsyncDBSession, storage: Storage) -> VerificationRequestRead:
    pilot_number = form.pilot_number or pilot.pilot_number
    if pilot_number is None:
        raise APIExceptions.unprocessable("pilot_number is required: the pilot has no number yet")

    if await Queries.Verification.get_pending_by_pilot(pilot.id, db) is not None:
        raise APIExceptions.conflict("Pilot already has a pending verification request")

    documents = await _read_documents(form)

    request = VerificationRequest(
        pilot_id=pilot.id,
        first_name=form.first_name or pilot.first_name,
        last_name=form.last_name or pilot.last_name,
        email=form.email or pilot.email,
        phone_number=form.phone_number or pilot.phone_number,
        pilot_number=pilot_number,
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
