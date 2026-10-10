from httpx import Response, Client

from tests.utils import functional
from tests.types import UserInfo, EndpointCreator
from .session_behaviour import request_refresh_token


def logout(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/logout"),
        "json": {"refresh_token": user["tokens"]["refresh_token"]}
    }
    r = client.post(**request)

    return r


def logout_flow(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> bool:
    logout(client, user, get_endpoint_link)
    
    r = request_refresh_token(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    user["tokens"] = functional.create_default_tokens()
    return True