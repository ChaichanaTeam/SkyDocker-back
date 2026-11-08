from .schema import VerificationRequestRead


ROUTER = {
    "tags": ["verification"],
    "responses": {
        401: { "description": "Missing or invalid access token" },
        429: { "description": "Rate limit exceeded" }
    }
}


CREATE_REQUEST = {
    "summary": "Submit a verification request",
    "description": "Submits the pilot's documents for moderator review.\n\n"
                    "`operator_number` (document issuing the pilot number) is required, "
                    "training certificates `privilege_*` are optional. One file per type.\n\n"
                    "`first_name`, `last_name`, `phone_number` and `pilot_number` are required. "
                    "`email` defaults to the pilot's email.\n\n"
                    "With `keep_documents=true` the documents are copied to the pilot's organizer after approval. "
                    "Otherwise they are deleted once the request is approved. "
                    "Rejected and withdrawn requests always lose their documents.\n\n"
                    "File type is detected by content, not by name.",
    "response_description": "Created request with its documents",
    "response_model": VerificationRequestRead,
    "status_code": 201,
    "responses": {
        201: { "description": "Request created, documents stored" },
        409: { "description": "Pilot already has a pending request" },
        413: { "description": "A file is larger than 10 MB" },
        422: { "description": "Missing required field or operator_number document, or unsupported file type" }
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
