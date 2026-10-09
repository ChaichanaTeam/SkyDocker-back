from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils.behavioural.reset_behaviour import (
    forgot_password,
    password_verify_otp,
    reset_password
)

def test_forgot_password(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = forgot_password(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"Reset request failed: {r.text}"

    verify_token = r.json().get("token")
    assert verify_token, f"Request did not return a reset token: {r.text}"
    registered_user["tokens"]["verify_token"] = verify_token


def test_verify_otp(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = password_verify_otp(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"Code is invalid: {r.text}"

    reset_token = r.json().get("token")
    assert reset_token, f"Request did not return a reset token: {r.text}"
    registered_user["tokens"]["reset_token"] = reset_token


def test_reset_password(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    new_password = registered_user["password"] + "2"
    registered_user["password"] = new_password

    r = reset_password(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"Reset confirm failed: {r.text}"

    body = r.json()
    assert body.get("access_token") and body.get("refresh_token"), f"Request did not return access: {r.text}"
    registered_user["tokens"]["access_token"] = body["access_token"]
    registered_user["tokens"]["refresh_token"] = body["refresh_token"]