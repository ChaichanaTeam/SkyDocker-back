from uuid import uuid4


def verification_key(request_id: int, document_type: str, ext: str) -> str:
    return f"requests/{request_id}/{document_type}/{uuid4().hex}.{ext}"


def organizer_key(pilot_id: int, document_type: str, ext: str) -> str:
    return f"pilots/{pilot_id}/{document_type}/{uuid4().hex}.{ext}"
