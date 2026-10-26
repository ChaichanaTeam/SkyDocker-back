from typing import Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


PDF = b"%PDF-1.4 test document"
PNG = b"\x89PNG\r\n\x1a\n test image"

DocumentFiles = dict[str, tuple[str, bytes, str]]


def pdf(name: str = "document.pdf", body: bytes = PDF) -> tuple[str, bytes, str]:
    return name, body, "application/pdf"


def _auth(user: UserInfo) -> dict[str, str]:
    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def create_request(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator,
    files: DocumentFiles, fields: Optional[dict[str, str]] = None, auth: bool = True,
) -> Response:
    request = {
        "url": get_endpoint_link("live", "verification-requests/"),
        "headers": _auth(user) if auth else {},
        "files": files,
        "data": fields or {},
    }
    r = client.post(**request)

    return r


def withdraw_request(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, request_id: int) -> Response:
    request = {
        "url": get_endpoint_link("live", f"verification-requests/{request_id}/withdraw"),
        "headers": _auth(user),
    }
    r = client.post(**request)

    return r
