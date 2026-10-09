import pytest
from httpx import Client

from tests.config import Config
from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.login_behaviour import login
from tests.utils.behavioural.registration_behaviour import (
    registration_request_otp, registration_verify_otp, registration_end
)


RATE_LIMIT_MAX_ATTEMPTS = 50


def _obtain_register_token(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> None:
    r = registration_request_otp(client, user, get_endpoint_link)
    assert r.status_code == 200, f"request-otp failed: {r.text}"
    user["tokens"]["verify_token"] = r.json()["token"]

    r = registration_verify_otp(client, user, get_endpoint_link)
    assert r.status_code == 200, f"verify-otp failed: {r.text}"
    user["tokens"]["register_token"] = r.json()["token"]


def test_duplicate_email_cannot_register_twice(
    client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator
):
    # 409 now; 200 with a dead-end token once user enumeration is fixed
    duplicate = functional.create_user(email=registered_user["email"], password="an0th3rp455w0rd")

    r = registration_request_otp(client, duplicate, get_endpoint_link)
    assert r.status_code in (200, 409), f"Unexpected request-otp response: {r.text}"

    if r.status_code == 200:
        duplicate["tokens"]["verify_token"] = r.json().get("token")

        r = registration_verify_otp(client, duplicate, get_endpoint_link)
        if r.status_code == 200:
            duplicate["tokens"]["register_token"] = r.json().get("token")
            r = registration_end(client, duplicate, get_endpoint_link)

        assert r.status_code != 200, f"Duplicate email must not finish registration: {r.text}"

    r = login(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"Original account must stay intact: {r.text}"

    r = login(client, duplicate, get_endpoint_link)
    assert r.status_code == 401, f"Duplicate credentials must not be accepted: {r.text}"


def test_verify_otp_wrong_code(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = registration_request_otp(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"request-otp failed: {r.text}"
    new_user["tokens"]["verify_token"] = r.json()["token"]

    r = registration_verify_otp(client, new_user, get_endpoint_link, code=functional.wrong_otp_code())
    assert r.status_code == 400, f"Wrong code should be rejected: {r.text}"


def test_register_without_token_rejected(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    payload = {
        "phone_number": new_user["phone_number"],
        "password": new_user["password"],
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
    }
    r = client.post(get_endpoint_link("live", "auth/register"), json=payload)
    assert r.status_code in (401, 403), f"Registration without a token should be rejected: {r.text}"


def test_register_with_wrong_token_type(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = registration_request_otp(client, new_user, get_endpoint_link)
    assert r.status_code == 200, f"request-otp failed: {r.text}"
    new_user["tokens"]["register_token"] = r.json()["token"]

    r = registration_end(client, new_user, get_endpoint_link)
    assert r.status_code == 401, f"Verify token must not be accepted as register token: {r.text}"


def test_register_rejects_short_password(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    _obtain_register_token(client, new_user, get_endpoint_link)
    new_user["password"] = "ab"

    r = registration_end(client, new_user, get_endpoint_link)
    assert r.status_code == 422, f"Short password should be rejected: {r.text}"


def test_register_rejects_missing_password(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    _obtain_register_token(client, new_user, get_endpoint_link)
    payload = {
        "phone_number": new_user["phone_number"],
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
    }

    r = registration_end(client, new_user, get_endpoint_link, payload=payload)
    assert r.status_code == 422, f"Missing password should be rejected: {r.text}"


def test_register_rejects_invalid_phone(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    _obtain_register_token(client, new_user, get_endpoint_link)
    new_user["phone_number"] = "12345"

    r = registration_end(client, new_user, get_endpoint_link)
    assert r.status_code == 422, f"Invalid phone number should be rejected: {r.text}"


@pytest.mark.order(-1)
def test_rate_limiting(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    if Config.is_server_in_debug:
        pytest.skip("Rate limits are relaxed in DEBUG mode")

    statuses = []
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS):
        r = registration_request_otp(client, new_user, get_endpoint_link)
        statuses.append(r.status_code)
        if r.status_code == 429:
            break

    assert 429 in statuses, f"Rate limiting should be enforced, got: {statuses}"
