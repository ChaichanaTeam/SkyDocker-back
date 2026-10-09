from typing import Optional
from httpx import Client, Response

from tests import constants
from tests.types import UserInfo, EndpointCreator


def forgot_password(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/forgot-password"),
        "json": {"email": user["email"]}
    }
    r = client.post(**request)

    return r


def password_verify_otp(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, code: Optional[str] = None
) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/verify-reset-token"),
        "headers": {"Authorization": f"{user['tokens']['type']} {user['tokens']['verify_token']}"},
        "json": {"code": code or constants.OTP_CODE}
    }
    r = client.post(**request)

    return r


def reset_password(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    request = {
        "url": get_endpoint_link("live", "auth/reset-password"),
        "headers": {"Authorization": f"{user['tokens']['type']} {user['tokens']['reset_token']}"},
        "json": {"new_password": user["password"]}
    }
    r = client.patch(**request)

    return r


def reset_password_flow(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> bool:
    r = forgot_password(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    verify_token = r.json().get("token")
    if verify_token is None:
        return False
    user["tokens"]["verify_token"] = verify_token

    r = password_verify_otp(client, user, get_endpoint_link)
    if r.status_code != 200:
        return False

    reset_token = r.json().get("token")
    if reset_token is None:
        return False
    
    user["tokens"]["reset_token"] = reset_token

    new_password = user["password"] + "2"
    user["password"] = new_password

    r = reset_password(client, user, get_endpoint_link)
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