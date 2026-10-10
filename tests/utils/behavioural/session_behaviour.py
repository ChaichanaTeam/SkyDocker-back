from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def request_refresh_token(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/refresh"),
        "json": {"refresh_token": user["tokens"]["refresh_token"]}
    }
    r = client.post(**request)

    return r