from backend_src.models import VerificationDocumentType
from backend_src.api.v1.moderator.docs import MODERATOR_AUTH, MODERATOR_401
from .schema import VerificationQueueItem, VerificationRequestRead, VerificationReviewRead, VerificationTokenResponse


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

LIST_REQUESTS = {
    "summary": "List verification requests",
    "description": "The moderator queue, the oldest request first, paginated with `limit` and `offset`. "
                    "Filter by `?status=`, e.g. pending; without it every status is listed.\n\n"
                    "`review` of a pending request tells which moderator reviews it now and for how long, "
                    "null means it is free to open. Document links come only with GET /verification-requests/{request_id}.\n\n"
                    + MODERATOR_AUTH,
    "response_description": "Verification requests",
    "response_model": list[VerificationQueueItem],
    "responses": {
        200: { "description": "Requests listed" },
        401: MODERATOR_401,
    }
}


GET_REQUEST = {
    "summary": "Open a request for review",
    "description": "The request with presigned download links to its documents, the links expire in 5 minutes.\n\n"
                    "Opening a pending request locks it to the moderator for the same 5 minutes, so another moderator "
                    "cannot open it meanwhile. Opening it again extends the lock and gives fresh links. "
                    "`review_expires_in` tells how long the lock lasts. "
                    "DELETE /verification-requests/{request_id}/review releases it earlier.\n\n" + MODERATOR_AUTH,
    "response_description": "Request with document links",
    "response_model": VerificationReviewRead,
    "responses": {
        200: { "description": "Request opened, pending request locked to the moderator" },
        401: MODERATOR_401,
        404: { "description": "Request not found" },
        409: { "description": "Another moderator reviews the request: `detail.moderator` is who, "
                              "`detail.expires_in` is seconds until the lock runs out" }
    }
}

RELEASE_REVIEW = {
    "summary": "Release a request",
    "description": "Releases the moderator's lock on the request before it runs out, so another moderator can open it. "
                    "Releasing a request that is not locked succeeds.\n\n" + MODERATOR_AUTH,
    "response_description": "Release confirmation message",
    "responses": {
        200: { "description": "Lock released" },
        401: MODERATOR_401,
        404: { "description": "Request not found" },
        409: { "description": "Another moderator reviews the request" }
    }
}
