from typing import Any, Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


PDF = b"%PDF-1.4 test document"
PNG = b"\x89PNG\r\n\x1a\n test image"

DocumentFile = tuple[str, bytes, str]
Documents = dict[str, DocumentFile]


def pdf(name: str = "document.pdf", body: bytes = PDF) -> DocumentFile:
    return name, body, "application/pdf"


def _auth(user: UserInfo) -> dict[str, str]:
    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def preview_request(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator,
    fields: dict[str, Any], document_types: list[str], auth: bool = True,
) -> Response:
    request = {
        "url": get_endpoint_link("live", "verification-requests/preview"),
        "headers": _auth(user) if auth else {},
        "json": {**fields, "document_types": document_types},
    }
    r = client.post(**request)

    return r


def upload_documents(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator,
    token: str, documents: Documents, document_types: Optional[list[str]] = None,
) -> Response:
    request = {
        "url": get_endpoint_link("live", "verification-requests/"),
        "headers": {**_auth(user), "X-Verification-Token": token},
        "data": {"document_types": document_types if document_types is not None else list(documents)},
        "files": [("files", file) for file in documents.values()],
    }
    r = client.post(**request)

    return r


def submit_request(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator,
    documents: Documents, fields: dict[str, Any],
) -> Response:
    r = preview_request(client, user, get_endpoint_link, fields, list(documents))
    assert r.status_code == 200, f"Preview failed: {r.text}"

    return upload_documents(client, user, get_endpoint_link, r.json()["verification_token"], documents)


def withdraw_request(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    request = {
        "url": get_endpoint_link("live", f"verification-requests/{request_id}/withdraw"),
        "headers": _auth(user),
    }
    r = client.post(**request)

    return r


def approve_request(client: Client, get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    r = client.post(get_endpoint_link("demo", f"verification-requests/{request_id}/approve"))

    return r


def reject_request(client: Client, get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    r = client.post(get_endpoint_link("demo", f"verification-requests/{request_id}/reject"), params={"reason": "Unreadable scan"})

    return r


def pilot_profile(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    # The grant endpoint returns the profile contact, there is no live profile endpoint yet
    r = client.post(
        get_endpoint_link("demo", "flying-privilege/grant"),
        params={"email": user["email"], "privileges": ["a1"]},
    )

    return r
