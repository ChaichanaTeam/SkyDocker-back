from uuid import uuid4


def verification_key(request_id: int, document_type: str, ext: str) -> str:
    return f"requests/{request_id}/{document_type}/{uuid4().hex}.{ext}"


def organizer_prefix(pilot_id: int) -> str:
    # The trailing slash keeps pilot 1 out of the files of pilot 12
    return f"pilots/{pilot_id}/"


def organizer_key(pilot_id: int, document_type: str, ext: str) -> str:
    return f"{organizer_prefix(pilot_id)}{document_type}/{uuid4().hex}.{ext}"
