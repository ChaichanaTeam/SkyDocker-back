from typing import Callable

import pytest
from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.login_behaviour import login
from tests.utils.behavioural.registration_behaviour import (
    registration_flow, registration_request_otp, registration_verify_otp, registration_end
)


def _dotted(local: str) -> str:
    return f"{local[:4]}.{local[4:]}"


def _register(client: Client, email: str, get_endpoint_link: EndpointCreator) -> UserInfo:
    user = functional.create_user(email=email)
    assert registration_flow(client, user, get_endpoint_link), f"Registration of {email} failed"

    return user


def _assert_cannot_register(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> None:
    # 409 now; 200 with a dead-end token once user enumeration is fixed
    r = registration_request_otp(client, user, get_endpoint_link)
    assert r.status_code in (200, 409), f"Unexpected request-otp response: {r.text}"

    if r.status_code == 200:
        user["tokens"]["verify_token"] = r.json().get("token")

        r = registration_verify_otp(client, user, get_endpoint_link)
        if r.status_code == 200:
            user["tokens"]["register_token"] = r.json().get("token")
            r = registration_end(client, user, get_endpoint_link)

        assert r.status_code != 200, f"Alias {user['email']} must not finish registration: {r.text}"


@pytest.mark.parametrize("alias", [
    lambda local: f"{_dotted(local)}@gmail.com",
    lambda local: f"{local}+tag@gmail.com",
    lambda local: f"{local.upper()}@Gmail.com",
    lambda local: f"{local}@googlemail.com",
], ids=["dots", "plus-tag", "case", "googlemail"])
def test_gmail_alias_cannot_register(
    client: Client, get_endpoint_link: EndpointCreator, alias: Callable[[str], str]
):
    local = functional.random_local()
    original = _register(client, f"{local}@gmail.com", get_endpoint_link)

    duplicate = functional.create_user(email=alias(local), password="an0th3rp455w0rd")
    _assert_cannot_register(client, duplicate, get_endpoint_link)

    r = login(client, original, get_endpoint_link)
    assert r.status_code == 200, f"Original account must stay intact: {r.text}"


def test_login_with_gmail_alias(client: Client, get_endpoint_link: EndpointCreator):
    local = functional.random_local()
    original = _register(client, f"{_dotted(local)}+x@gmail.com", get_endpoint_link)

    r = login(client, original, get_endpoint_link)
    assert r.status_code == 200, f"Login with the registered address failed: {r.text}"

    alias = functional.create_user(email=f"{local}@gmail.com", password=original["password"])
    r = login(client, alias, get_endpoint_link)
    assert r.status_code == 200, f"Login with a Gmail alias should succeed: {r.text}"


def test_plus_only_domain_strips_tag(client: Client, get_endpoint_link: EndpointCreator):
    local = _dotted(functional.random_local())
    _register(client, f"{local}@outlook.com", get_endpoint_link)

    duplicate = functional.create_user(email=f"{local}+tag@outlook.com")
    _assert_cannot_register(client, duplicate, get_endpoint_link)


def test_plus_only_domain_keeps_dots(client: Client, get_endpoint_link: EndpointCreator):
    # Outlook treats dots as significant: these are two different mailboxes
    local = functional.random_local()
    _register(client, f"{_dotted(local)}@outlook.com", get_endpoint_link)
    _register(client, f"{local}@outlook.com", get_endpoint_link)


def test_unknown_domain_keeps_tag_and_dots(client: Client, get_endpoint_link: EndpointCreator):
    local = functional.random_local()
    _register(client, f"{_dotted(local)}+tag@wp.pl", get_endpoint_link)
    _register(client, f"{_dotted(local)}@wp.pl", get_endpoint_link)
    _register(client, f"{local}@wp.pl", get_endpoint_link)


def test_tag_only_local_part_rejected(client: Client, get_endpoint_link: EndpointCreator):
    user = functional.create_user(email="+tag@gmail.com")

    r = registration_request_otp(client, user, get_endpoint_link)
    assert r.status_code == 422, f"Address with an empty name should be rejected: {r.text}"
