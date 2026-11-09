import pytest
from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils import functional
from tests.utils.behavioural.pilot_behaviour import pilot_get, pilot_update


def _pilot_id(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> int:
    r = pilot_get(client, user, get_endpoint_link, "me")
    assert r.status_code == 200, f"Profile failed: {r.text}"

    return r.json()["id"]


@pytest.mark.parametrize("path", ["me", "me/privileges", "me/drones", "me/missions", "me/check-ins", "me/check-ins/active", "1"])
def test_requires_token(client: Client, get_endpoint_link: EndpointCreator, path: str):
    r = pilot_get(client, None, get_endpoint_link, path)
    assert r.status_code in (401, 403), f"{path} must need a token: {r.text}"


def test_new_pilot_profile(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = pilot_get(client, fresh_user, get_endpoint_link, "me")
    assert r.status_code == 200, f"A just registered pilot must get a profile: {r.text}"

    body = r.json()
    assert body["email"] == fresh_user["email"]
    assert body["first_name"] is None and body["last_name"] is None
    assert body["phone_number"] is None and body["pilot_number"] is None
    assert body["show_to_public"] is False
    assert "password_hash" not in body


def test_update_changes_passed_fields(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    phone = functional.random_phone()

    r = pilot_update(client, fresh_user, get_endpoint_link, {"phone_number": phone})
    assert r.status_code == 200, f"Update failed: {r.text}"
    assert r.json()["phone_number"] == phone

    r = pilot_update(client, fresh_user, get_endpoint_link, {"show_to_public": True})
    assert r.status_code == 200, f"Update failed: {r.text}"
    assert r.json()["phone_number"] == phone, "A field left out must keep its value"

    body = pilot_get(client, fresh_user, get_endpoint_link, "me").json()
    assert body["phone_number"] == phone and body["show_to_public"] is True, "Update was not saved"


def test_update_empty_body(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    before = pilot_get(client, fresh_user, get_endpoint_link, "me").json()

    r = pilot_update(client, fresh_user, get_endpoint_link, {})
    assert r.status_code == 200, f"An empty update is allowed: {r.text}"
    assert r.json() == before


@pytest.mark.parametrize("body", [
    {"phone_number": None},
    {"show_to_public": None},
    {"phone_number": "not-a-phone"},
    {"phone_number": "+49301234561111111"},
])
def test_update_rejected(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator, body: dict):
    r = pilot_update(client, fresh_user, get_endpoint_link, body)
    assert r.status_code == 422, f"{body} must be rejected: {r.text}"


def test_update_cannot_set_verified_fields(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = pilot_update(client, fresh_user, get_endpoint_link, {"pilot_number": "POL123", "first_name": "Fake", "last_name": "Name"})
    assert r.status_code == 200, f"Unknown fields are ignored: {r.text}"

    body = pilot_get(client, fresh_user, get_endpoint_link, "me").json()
    assert body["pilot_number"] is None, "Pilot number comes only from an approved request"
    assert body["first_name"] is None and body["last_name"] is None, "Name comes only from an approved request"


def test_public_hidden_by_default(client: Client, fresh_user: UserInfo, other_user: UserInfo, get_endpoint_link: EndpointCreator):
    target = _pilot_id(client, other_user, get_endpoint_link)

    r = pilot_get(client, fresh_user, get_endpoint_link, str(target))
    assert r.status_code == 404, f"A hidden profile must look missing: {r.text}"


def test_public_own_is_visible(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    me = _pilot_id(client, fresh_user, get_endpoint_link)

    r = pilot_get(client, fresh_user, get_endpoint_link, str(me))
    assert r.status_code == 200, f"Own profile is always visible: {r.text}"


def test_public_opened(client: Client, fresh_user: UserInfo, other_user: UserInfo, get_endpoint_link: EndpointCreator):
    target = _pilot_id(client, other_user, get_endpoint_link)
    r = pilot_update(client, other_user, get_endpoint_link, {"show_to_public": True, "phone_number": functional.random_phone()})
    assert r.status_code == 200, f"Update failed: {r.text}"

    r = pilot_get(client, fresh_user, get_endpoint_link, str(target))
    assert r.status_code == 200, f"An opened profile must be visible: {r.text}"
    assert not {"email", "phone_number", "pilot_number"} & set(r.json()), f"Contacts must stay private: {r.text}"


@pytest.mark.parametrize("path,status", [("999999999999", 404), (str(2**63), 422), ("0", 422)])
def test_public_ids(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator, path: str, status: int):
    r = pilot_get(client, fresh_user, get_endpoint_link, path)
    assert r.status_code == status, f"Pilot id {path}: {r.text}"
