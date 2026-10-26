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
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    pilot_number: Optional[str]
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
    first_name: Optional[str] = Form(None, min_length=1, max_length=255, description="Defaults to the pilot's first name"),
    last_name: Optional[str] = Form(None, min_length=1, max_length=255, description="Defaults to the pilot's last name"),
    email: Optional[EmailStr] = Form(None, description="Contact email for this request. Defaults to the pilot's email"),
    phone_number: Optional[E164PhoneNumber] = Form(None, description="Contact phone for this request. Defaults to the pilot's phone"),
    pilot_number: Optional[str] = Form(None, min_length=1, max_length=255, description="Number from the operator_number document. Defaults to the pilot's number"),
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
    phone_number: Optional[str]
    pilot_number: str

    reason: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime

    documents: list[VerificationDocumentRead] = Field(validation_alias="verification_document")
