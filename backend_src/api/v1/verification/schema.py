from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend_src.api.shared_schemas import E164PhoneNumber
from backend_src.models import VerificationDocumentType, VerificationRequestStatus


@dataclass
class VerificationForm:
    first_name: str
    last_name: str
    email: Optional[str]
    phone_number: str
    pilot_number: str
    keep_documents: bool
    documents: dict[VerificationDocumentType, UploadFile]


def _document(description: str):
    return File(None, description=f"{description}. PDF, JPEG or PNG up to 10 MB")


async def verification_form(
    operator_number: UploadFile = File(description="Document issuing the pilot number. PDF, JPEG or PNG up to 10 MB"),
    privilege_a1: Optional[UploadFile] = _document("A1 training certificate"),
    privilege_a2: Optional[UploadFile] = _document("A2 training certificate"),
    privilege_a3: Optional[UploadFile] = _document("A3 training certificate"),
    privilege_sts01: Optional[UploadFile] = _document("STS-01 training certificate"),
    privilege_sts02: Optional[UploadFile] = _document("STS-02 training certificate"),
    first_name: str = Form(min_length=1, max_length=255),
    last_name: str = Form(min_length=1, max_length=255),
    phone_number: E164PhoneNumber = Form(description="Pilot's phone, written to the profile on approval"),
    pilot_number: str = Form(min_length=1, max_length=255, description="Number from the operator_number document"),
    email: Optional[EmailStr] = Form(None, description="Contact email for this request. Defaults to the pilot's email"),
    keep_documents: bool = Form(False, description="Keep the documents in the pilot's organizer after approval. When false they are deleted"),
) -> VerificationForm:
    uploads = {
        VerificationDocumentType.OPERATOR_NUMBER: operator_number,
        VerificationDocumentType.PRIVILEGE_A1: privilege_a1,
        VerificationDocumentType.PRIVILEGE_A2: privilege_a2,
        VerificationDocumentType.PRIVILEGE_A3: privilege_a3,
        VerificationDocumentType.PRIVILEGE_STS01: privilege_sts01,
        VerificationDocumentType.PRIVILEGE_STS02: privilege_sts02,
    }

    return VerificationForm(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        pilot_number=pilot_number,
        keep_documents=keep_documents,
        documents={doc_type: upload for doc_type, upload in uploads.items() if upload is not None},
    )


class VerificationDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: VerificationDocumentType
    url: Optional[str] = Field(None, description="Presigned download link, given only to the reviewer")


class VerificationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pilot_id: int
    status: VerificationRequestStatus

    first_name: str
    last_name: str
    email: str
    phone_number: str
    pilot_number: str
    keep_documents: bool

    reason: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime

    documents: list[VerificationDocumentRead] = Field(validation_alias="verification_document")
