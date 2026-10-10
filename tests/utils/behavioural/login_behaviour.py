from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def login(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/login"),
        "json": {"email": user["email"], "password": user["password"]}
    }
    r = client.post(**request)

    return r
