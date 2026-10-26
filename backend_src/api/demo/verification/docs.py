from backend_src.api.v1.verification.schema import VerificationRequestRead


CREATE_REQUEST = {
    "summary": "Submit a verification request without auth",
    "description": "Same as live `POST /verification-requests/`, but the pilot is taken from `?email=` "
                    "instead of the access token.\n\n"
                    "Without `email` the demo pilot is used (created on first use). "
                    "It has no pilot number, so pass `pilot_number`.",
    "response_model": VerificationRequestRead,
    "status_code": 201,
    "responses": {
        201: { "description": "Request created, documents stored" },
        404: { "description": "Pilot with the given email not found" },
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
                    "and copies `pilot_number` to the pilot.\n\n"
                    "Documents are kept: later the pilot decides whether to move them to the organizer. "
                    "The verification bucket removes them after 30 days anyway",
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
