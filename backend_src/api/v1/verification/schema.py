from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal, Optional

from fastapi import Header
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend_src.api.shared_schemas import E164PhoneNumber
from backend_src.core.security import TokenPayload, TokenType
from backend_src.models import VerificationDocumentType, VerificationRequestStatus
from backend_src.storage import MAX_DOCUMENTS


VerificationToken = Annotated[str, Header(alias="X-Verification-Token", description="Token issued by POST /verification-requests/preview")]


class VerificationPreviewRequest(BaseModel):
    """What the pilot is going to submit. Files follow only after this passes."""

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    phone_number: E164PhoneNumber = Field(description="Pilot's phone, written to the profile on approval")
    pilot_number: Optional[str] = Field(None, min_length=1, max_length=255, description="Number from the operator_number document. Only for a pilot without a number")
    keep_documents: bool = Field(False, description="Keep the documents in the pilot's organizer after approval. When false they are deleted")
    document_types: list[VerificationDocumentType] = Field(min_length=1, max_length=MAX_DOCUMENTS, description="Types of the files that will be uploaded, one file per type")

    @field_validator("document_types")
    @classmethod
    def validate_document_types(cls, document_types: list[VerificationDocumentType]) -> list[VerificationDocumentType]:
        if VerificationDocumentType.UNKNOWN in document_types:
            raise ValueError("Unknown document type")
        if len(set(document_types)) != len(document_types):
            raise ValueError("One file per document type")
        return document_types


class VerificationPlan(BaseModel):
    """Verified request, the only data the token carries and the request is created from."""

    first_name: str
    last_name: str
    phone_number: str
    pilot_number: str
    keep_documents: bool
    document_types: list[VerificationDocumentType]


class VerificationTokenPayload(TokenPayload):
    type: Literal[TokenType.VERIFICATION_REQUEST] = TokenType.VERIFICATION_REQUEST
    plan: VerificationPlan


class VerificationTokenResponse(BaseModel):
    verification_token: str = Field(..., description="Pass this token in X-Verification-Token to POST /verification-requests/")
    expires_in: int = Field(..., description="Seconds the token stays valid")


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
    phone_number: str
    pilot_number: str
    keep_documents: bool

    reason: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime

    documents: list[VerificationDocumentRead] = Field(validation_alias="verification_document")
