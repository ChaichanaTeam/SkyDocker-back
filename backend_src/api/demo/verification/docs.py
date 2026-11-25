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
