from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils.behavioural.registration_behaviour import (
    registration_request_otp, registration_verify_otp, registration_end
)
from tests.utils.behavioural.logout_behaviour import logout
from tests.utils.behavioural.session_behaviour import request_refresh_token


def test_request_otp(client: Client, test_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = registration_request_otp(client, test_user, get_endpoint_link)
    assert r.status_code == 200, f"Failed to request OTP: {r.text}"

    verify_token = r.json().get("token")
    assert verify_token, f"request-otp did not return a verify token: {r.text}"
    test_user["tokens"]["verify_token"] = verify_token


def test_verify_otp(client: Client, test_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = registration_verify_otp(client, test_user, get_endpoint_link)
    assert r.status_code == 200, f"Failed to verify OTP: {r.text}"

    register_token = r.json().get("token")
    assert register_token, f"verify-otp did not return a registration token: {r.text}"
    test_user["tokens"]["register_token"] = register_token


def test_register(client: Client, test_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = registration_end(client, test_user, get_endpoint_link)
    assert r.status_code == 200, f"Registration failed: {r.text}"

    body = r.json()
    assert body.get("access_token") and body.get("refresh_token"), f"Registration did not return tokens: {r.text}"
    test_user["tokens"]["access_token"] = body["access_token"]
    test_user["tokens"]["refresh_token"] = body["refresh_token"]


def test_logout(client: Client, test_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = logout(client, test_user, get_endpoint_link)
    assert r.status_code == 200, f"Logout failed: {r.text}"

    r = request_refresh_token(client, test_user, get_endpoint_link)
    assert r.status_code == 401, f"Refresh token should be revoked after logout: {r.text}"