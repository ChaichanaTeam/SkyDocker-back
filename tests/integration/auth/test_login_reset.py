from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.login_behaviour import login
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.reset_behaviour import (
    forgot_password, password_verify_otp, reset_password, reset_password_flow
)
from tests.utils.behavioural.session_behaviour import request_refresh_token


def test_login_wrong_password_and_unknown_email_indistinguishable(
    client: Client, registered_user: UserInfo, new_user: UserInfo, get_endpoint_link: EndpointCreator
):
    wrong_password = functional.create_user(email=registered_user["email"], password="wr0ngp455w0rd")

    r_wrong = login(client, wrong_password, get_endpoint_link)
    r_unknown = login(client, new_user, get_endpoint_link)

    assert r_wrong.status_code == 401, f"Wrong password should be rejected: {r_wrong.text}"
    assert r_unknown.status_code == 401, f"Unknown email should be rejected: {r_unknown.text}"
    assert r_wrong.json() == r_unknown.json(), "Login errors must not reveal whether the email exists"


def test_forgot_password_unknown_email_does_not_leak_reset(
    client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator
):
    # 404 now; 200 with a dead-end token once user enumeration is fixed
    r = forgot_password(client, new_user, get_endpoint_link)
    assert r.status_code in (200, 404), f"Unexpected forgot-password response: {r.text}"

    token = r.json().get("token") if r.status_code == 200 else None
    if token:
        new_user["tokens"]["verify_token"] = token

        r = password_verify_otp(client, new_user, get_endpoint_link)
        assert r.status_code != 200, f"Unknown email must not get a reset token: {r.text}"


def test_verify_reset_wrong_code(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = forgot_password(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"forgot-password failed: {r.text}"
    registered_user["tokens"]["verify_token"] = r.json()["token"]

    r = password_verify_otp(client, registered_user, get_endpoint_link, code=functional.wrong_otp_code())
    assert r.status_code == 400, f"Wrong code should be rejected: {r.text}"


def test_refresh_reuse_rejected(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"
    old_refresh = new_user["tokens"]["refresh_token"]

    r = request_refresh_token(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"Refresh failed: {r.text}"
    new_user["tokens"]["refresh_token"] = r.json()["refresh_token"]

    stale = functional.create_user(tokens={**new_user["tokens"], "refresh_token": old_refresh})
    r = request_refresh_token(client, stale, get_endpoint_link)
    assert r.status_code == 401, f"Used refresh token must be rejected: {r.text}"


def test_reset_revokes_refresh_sessions(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"
    old_refresh = new_user["tokens"]["refresh_token"]

    assert reset_password_flow(client, new_user, get_endpoint_link), "Password reset failed"

    stale = functional.create_user(tokens={**new_user["tokens"], "refresh_token": old_refresh})
    r = request_refresh_token(client, stale, get_endpoint_link)
    assert r.status_code == 401, f"Refresh token issued before reset must be revoked: {r.text}"

    r = request_refresh_token(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"Refresh token issued by reset must work: {r.text}"


def test_reset_token_single_use(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"

    r = forgot_password(client, new_user, get_endpoint_link)
    new_user["tokens"]["verify_token"] = r.json()["token"]
    r = password_verify_otp(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"verify-reset-token failed: {r.text}"
    new_user["tokens"]["reset_token"] = r.json()["token"]

    new_user["password"] += "2"
    r = reset_password(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"First reset failed: {r.text}"

    new_user["password"] += "3"
    r = reset_password(client, new_user, get_endpoint_link)
    assert r.status_code == 401, f"Reset token must not be reusable: {r.text}"


def test_reset_keeps_other_users_sessions(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    other = functional.create_user()
    assert registration_flow(client, other, get_endpoint_link), "Registration of the other pilot failed"
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"

    assert reset_password_flow(client, new_user, get_endpoint_link), "Password reset failed"

    r = request_refresh_token(client, other, get_endpoint_link)
    assert r.status_code == 200, f"Other pilot's session must stay intact: {r.text}"
