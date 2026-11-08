from typing import Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def _auth(user: Optional[UserInfo]) -> dict[str, str]:
    if user is None:
        return {}

    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def country_at_point(
    client: Client, user: Optional[UserInfo], get_endpoint_link: EndpointCreator, point: tuple[float, float]
) -> Response:
    lon, lat = point
    request = {
        "url": get_endpoint_link("live", "geo-zone/country"),
        "headers": _auth(user),
        "params": {"lon": lon, "lat": lat}
    }
    r = client.get(**request)

    return r


def supported_countries(client: Client, user: Optional[UserInfo], get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "geo-zone/country/supported"),
        "headers": _auth(user)
    }
    r = client.get(**request)

    return r
