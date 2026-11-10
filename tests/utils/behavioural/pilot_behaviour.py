from typing import Any, Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def _auth(user: UserInfo) -> dict[str, str]:
    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def pilot_get(
    client: Client, user: Optional[UserInfo], get_endpoint_link: EndpointCreator, path: str,
    params: Optional[dict[str, Any]] = None
) -> Response:
    """GET under /pilots, without a user the request goes unauthenticated."""
    return client.get(
        get_endpoint_link("live", f"pilots/{path}"),
        headers=_auth(user) if user is not None else None,
        params=params,
    )


def pilot_update(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, body: dict[str, Any]) -> Response:
    return client.patch(get_endpoint_link("live", "pilots/me"), headers=_auth(user), json=body)
