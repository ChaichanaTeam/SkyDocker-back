from backend_src.api.v1.verification.docs import UPLOAD_BODY
from backend_src.api.v1.verification.schema import VerificationRequestRead, VerificationTokenResponse


PREVIEW_REQUEST = {
    "summary": "Verify a request form without auth",
    "description": "Same as live `POST /verification-requests/preview`, but the pilot is taken from `?email=` "
                    "instead of the access token.\n\n"
                    "Without `email` the demo pilot is used (created on first use).",
    "response_model": VerificationTokenResponse,
    "responses": {
        200: { "description": "Form verified, token returned" },
        404: { "description": "Pilot with the given email not found" },
        409: { "description": "Pilot already has a pending request" },
        422: { "description": "Invalid form or it breaks a pilot number rule" }
    }
}

CREATE_REQUEST = {
    "summary": "Upload documents without auth",
    "description": "Same as live `POST /verification-requests/`, pass the same `?email=` as in the preview.",
    "response_model": VerificationRequestRead,
    "status_code": 201,
    "openapi_extra": UPLOAD_BODY,
    "responses": {
        201: { "description": "Request created, documents stored" },
        404: { "description": "Pilot not found, or the token is invalid, expired or issued to another pilot" },
        409: { "description": "Pilot already has a pending request" }
    }
}

LIST_REQUESTS = {
    "summary": "List verification requests",
    "description": "All requests, newest first. Filter by `?status=`. Document links are not included, open a request by id",
    "response_model": list[VerificationRequestRead],
}

GET_REQUEST = {
    "summary": "Open a request as a moderator",
    "description": "Request with presigned download links to its documents. Links expire in 5 minutes",
    "response_model": VerificationRequestRead,
    "responses": {
        404: { "description": "Request not found" }
    }
}

APPROVE_REQUEST = {
    "summary": "Approve a request",
    "description": "Moderator simulation. Grants the privileges of the submitted `privilege_*` certificates "
                    "and writes `pilot_number` and `phone_number` to the pilot, names only if the profile has none.\n\n"
                    "With `keep_documents` the documents are copied to the organizer, `kept_documents` lists their keys. "
                    "The originals are deleted either way",
    "responses": {
        404: { "description": "Request not found" },
        409: { "description": "Request is not pending" }
    }
}

REJECT_REQUEST = {
    "summary": "Reject a request",
    "description": "Moderator simulation. Stores the reason and deletes the documents",
    "response_model": VerificationRequestRead,
    "responses": {
        404: { "description": "Request not found" },
        409: { "description": "Request is not pending" }
    }
}

DELETE_REQUEST = {
    "summary": "Delete a request",
    "description": "Deletes the request in any status together with its files in storage",
    "responses": {
        404: { "description": "Request not found" }
    }
}

DELETE_ALL_REQUESTS = {
    "summary": "Delete all requests",
    "description": "Resets the demo: deletes every request together with its files in storage",
}
