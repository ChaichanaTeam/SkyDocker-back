from typing import Optional
from httpx import Response, Client

from tests.types import EndpointCreator


REFRESH_COOKIE_NAME = "moderator_refresh"


def moderator_login(client: Client, email: str, password: str, get_endpoint_link: EndpointCreator) -> Response:
    return client.post(
        get_endpoint_link("live", "moderator/auth/login"),
        json={"email": email, "password": password},
    )


def moderator_refresh(client: Client, get_endpoint_link: EndpointCreator, cookie: Optional[str] = None) -> Response:
    headers = {"Cookie": f"{REFRESH_COOKIE_NAME}={cookie}"} if cookie is not None else None
    return client.post(get_endpoint_link("live", "moderator/auth/refresh"), headers=headers)


def moderator_logout(client: Client, get_endpoint_link: EndpointCreator, cookie: Optional[str] = None) -> Response:
    headers = {"Cookie": f"{REFRESH_COOKIE_NAME}={cookie}"} if cookie is not None else None
    return client.post(get_endpoint_link("live", "moderator/auth/logout"), headers=headers)


def moderator_me(client: Client, get_endpoint_link: EndpointCreator, access_token: Optional[str] = None) -> Response:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token is not None else None
    return client.get(get_endpoint_link("live", "moderator/me"), headers=headers)
