from typing import Any, Optional
from httpx import Response, Client

from tests import constants
from tests.types import UserInfo, EndpointCreator


def _register_payload(test_user: UserInfo) -> dict[str, str]:
    return {
        "password": test_user["password"]
    }


def registration_request_otp(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/register/request-otp"),
        "json": {"email": user["email"]}
    }
    r = client.post(**request)

    return r


def registration_verify_otp(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, code: Optional[str] = None
) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/register/verify-otp"),
        "headers": {"Authorization": f"{user['tokens']['type']} {user['tokens']['verify_token']}"},
        "json": {"code": code or constants.OTP_CODE}
    }
    r = client.post(**request)

    return r


def registration_end(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, payload: Optional[dict[str, Any]] = None
) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/register"),
        "headers": {"Authorization": f"{user['tokens']['type']} {user['tokens']['register_token']}"},
        "json": payload if payload is not None else _register_payload(user)
    }
    r = client.post(**request)

    return r


def registration_flow(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> bool:
    r = registration_request_otp(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    verify_token = r.json().get("token")
    if verify_token is None:
        return False
    
    user["tokens"]["verify_token"] = verify_token

    r = registration_verify_otp(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    register_token = r.json().get("token")
    if register_token is None:
        return False
    
    user["tokens"]["register_token"] = register_token

    r = registration_end(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    body = r.json()
    if body.get("access_token") is None or body.get("refresh_token") is None:
        return False


    user["tokens"]["access_token"] = body["access_token"]
    user["tokens"]["refresh_token"] = body["refresh_token"]
    user["tokens"]["register_token"] = None
    user["tokens"]["verify_token"] = None
    user["tokens"]["reset_token"] = None

    return True