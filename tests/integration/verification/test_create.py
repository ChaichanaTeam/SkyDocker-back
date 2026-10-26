import pytest
from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.verification_behaviour import (
    PNG, create_request, pdf, withdraw_request
)


PILOT_NUMBER = {"pilot_number": "POL-RP-TEST0001"}


@pytest.fixture
def pilot(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator) -> UserInfo:
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"
    return new_user


def test_create_fills_contact_from_profile(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    body = r.json()
    assert body["status"] == "pending"
    assert (body["first_name"], body["last_name"]) == (pilot["first_name"], pilot["last_name"])
    assert body["email"] == pilot["email"]
    assert body["phone_number"] == pilot["phone_number"]
    assert body["pilot_number"] == PILOT_NUMBER["pilot_number"]
    assert [d["document_type"] for d in body["documents"]] == ["operator_number"]
    assert all(d["url"] is None for d in body["documents"]), "Pilot must not get download links"


def test_create_overrides_contact(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = {**PILOT_NUMBER, "email": "contact@localhost.me", "phone_number": functional.random_phone()}
    files = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}

    r = create_request(client, pilot, get_endpoint_link, files, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    body = r.json()
    assert (body["email"], body["phone_number"]) == (fields["email"], fields["phone_number"])
    assert sorted(d["document_type"] for d in body["documents"]) == ["operator_number", "privilege_a1"]


def test_operator_number_document_required(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"privilege_a1": pdf()}, PILOT_NUMBER)
    assert r.status_code == 422, f"Request without operator_number must be rejected: {r.text}"


def test_pilot_number_required(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()})
    assert r.status_code == 422, f"New pilot has no number, request must be rejected: {r.text}"


def test_file_type_detected_by_content(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(body=b"<html>not a pdf</html>")}

    r = create_request(client, pilot, get_endpoint_link, files, PILOT_NUMBER)
    assert r.status_code == 422, f"Text renamed to .pdf must be rejected: {r.text}"


def test_file_size_limited(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(body=b"%PDF-" + b"0" * (10 * 1024 * 1024))}

    r = create_request(client, pilot, get_endpoint_link, files, PILOT_NUMBER)
    assert r.status_code == 413, f"File over 10 MB must be rejected: {r.text}"


def test_one_pending_request_until_withdrawn(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER)
    assert r.status_code == 409, f"Second pending request must be rejected: {r.text}"

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 200, f"Withdraw failed: {r.text}"
    assert r.json()["status"] == "withdrawn"
    assert r.json()["documents"] == [], "Withdrawn request must lose its documents"

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 409, f"Withdrawn request cannot be withdrawn again: {r.text}"

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER)
    assert r.status_code == 201, f"New request after withdraw must be accepted: {r.text}"


def test_create_requires_auth(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER, auth=False)
    assert r.status_code == 401, f"Request without token must be rejected: {r.text}"


def test_cannot_withdraw_foreign_request(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, PILOT_NUMBER)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    stranger = functional.create_user()
    assert registration_flow(client, stranger, get_endpoint_link), "Registration failed"

    r = withdraw_request(client, stranger, get_endpoint_link, r.json()["id"])
    assert r.status_code == 404, f"Foreign request must look missing: {r.text}"
