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


def approve_request(
    client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, request_id: int,
    privilege_expiry: Optional[dict[str, str]] = None,
) -> Response:
    r = client.post(
        get_endpoint_link("live", f"verification-requests/{request_id}/approve"),
        headers=_moderator_auth(token),
        json={"privilege_expiry": privilege_expiry or {}},
    )

    return r


def reject_request(
    client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, request_id: int, reason: Optional[str] = "Unreadable scan",
) -> Response:
    body = {"reason": reason} if reason is not None else {}
    r = client.post(
        get_endpoint_link("live", f"verification-requests/{request_id}/reject"), headers=_moderator_auth(token), json=body,
    )

    return r


def _moderator_auth(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token is not None else {}


def list_requests(client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, **params) -> Response:
    return client.get(get_endpoint_link("live", "verification-requests/"), headers=_moderator_auth(token), params=params)


def find_in_queue(
    client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, request_id: int, status: str,
) -> Optional[dict[str, Any]]:
    """The request in the moderator queue, paged through: earlier test runs leave many older requests before it."""
    offset = 0
    while items := list_requests(client, token, get_endpoint_link, status=status, limit=200, offset=offset).json():
        for item in items:
            if item["id"] == request_id:
                return item
        offset += len(items)

    return None


def review_request(client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    return client.get(get_endpoint_link("live", f"verification-requests/{request_id}"), headers=_moderator_auth(token))


def release_review(client: Client, token: Optional[str], get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    return client.delete(get_endpoint_link("live", f"verification-requests/{request_id}/review"), headers=_moderator_auth(token))


def pilot_profile(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    # The grant endpoint returns the profile contact, there is no live profile endpoint yet
    r = client.post(
        get_endpoint_link("demo", "flying-privilege/grant"),
        params={"email": user["email"], "privileges": ["a1"]},
    )

    return r
