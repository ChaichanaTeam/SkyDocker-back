from backend_src.models import VerificationDocumentType
from .schema import VerificationRequestRead, VerificationTokenResponse


ROUTER = {
    "tags": ["verification"],
    "responses": {
        401: { "description": "Missing or invalid access token" },
        429: { "description": "Rate limit exceeded" }
    }
}


UPLOAD_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["document_types", "files"],
                    "properties": {
                        "document_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [doc_type.value for doc_type in VerificationDocumentType if doc_type is not VerificationDocumentType.UNKNOWN],
                            },
                            "description": "Type of every file, in the same order as `files`. The same set as in the preview",
                        },
                        "files": {
                            "type": "array",
                            "items": { "type": "string", "format": "binary" },
                            "description": "PDF, JPEG or PNG up to 10 MB each, one per type",
                        },
                    },
                }
            }
        },
    }
}


PREVIEW_REQUEST = {
    "summary": "Verify a verification request before uploading files",
    "description": "Checks the form and issues a token for POST /verification-requests/. No files are sent at this step.\n\n"
                    "`first_name`, `last_name` and `phone_number` are required.\n\n"
                    "A pilot without a number must pass `pilot_number` and list `operator_number` in `document_types`. "
                    "A pilot who already has a number must pass neither, the number is taken from the profile.\n\n"
                    "With `keep_documents=true` the documents are copied to the pilot's organizer after approval. "
                    "Otherwise they are deleted once the request is approved. "
                    "Rejected and withdrawn requests always lose their documents.\n\n"
                    "Business-rule errors come in the same shape as validation errors: "
                    "`detail[].loc`, `detail[].msg`, `detail[].type` (`verification.*`), `detail[].input`.",
    "response_description": "Verification token",
    "response_model": VerificationTokenResponse,
    "responses": {
        200: { "description": "Form verified, token returned" },
        409: { "description": "Pilot already has a pending request" },
        422: { "description": "Invalid form or it breaks a pilot number rule, see detail" }
    }
}

CREATE_REQUEST = {
    "summary": "Upload documents and create the request",
    "description": "Creates the request verified by POST /verification-requests/preview. "
                    "The token goes in `X-Verification-Token`, is valid for 15 minutes and works once. "
                    "A failed upload does not use it up.\n\n"
                    "Documents are two repeated multipart fields paired by position: `document_types` and `files`.\n\n"
                    "File type is detected by content, not by name.",
    "response_description": "Created request with its documents",
    "response_model": VerificationRequestRead,
    "status_code": 201,
    "openapi_extra": UPLOAD_BODY,
    "responses": {
        201: { "description": "Request created, documents stored" },
        404: { "description": "No verified request: the token is invalid, expired, already used or issued to another pilot" },
        409: { "description": "Pilot already has a pending request" },
        413: { "description": "A file is larger than 10 MB" },
        422: { "description": "Files differ from the preview or have an unsupported type, see detail" }
    }
}

WITHDRAW_REQUEST = {
    "summary": "Withdraw a verification request",
    "description": "Withdraws the pilot's own pending request and deletes its documents. "
                    "A new request can be submitted afterwards",
    "response_description": "Withdrawn request",
    "response_model": VerificationRequestRead,
    "responses": {
        200: { "description": "Request withdrawn, documents deleted" },
        404: { "description": "Request not found or belongs to another pilot" },
        409: { "description": "Request is not pending" }
    }
}
