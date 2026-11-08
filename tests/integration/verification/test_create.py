import pytest
from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.verification_behaviour import (
    PNG, approve_request, create_request, pdf, pilot_profile, reject_request, withdraw_request
)


REQUIRED_FIELDS = ("first_name", "last_name", "phone_number", "pilot_number")


def request_fields(**overrides: str) -> dict[str, str]:
    return {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone_number": functional.random_phone(),
        "pilot_number": "POL-RP-TEST0001",
        **overrides,
    }


@pytest.fixture
def pilot(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator) -> UserInfo:
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"
    return new_user


def test_create_stores_fields(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = request_fields()

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    body = r.json()
    assert body["status"] == "pending"
    assert (body["first_name"], body["last_name"]) == (fields["first_name"], fields["last_name"])
    assert body["email"] == pilot["email"], "Email must default to the profile"
    assert body["phone_number"] == fields["phone_number"]
    assert body["pilot_number"] == fields["pilot_number"]
    assert body["keep_documents"] is False, "Documents must not be kept without consent"
    assert [d["document_type"] for d in body["documents"]] == ["operator_number"]
    assert all(d["url"] is None for d in body["documents"]), "Pilot must not get download links"


def test_create_overrides_email(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = request_fields(email="contact@localhost.me")
    files = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}

    r = create_request(client, pilot, get_endpoint_link, files, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    body = r.json()
    assert body["email"] == fields["email"]
    assert sorted(d["document_type"] for d in body["documents"]) == ["operator_number", "privilege_a1"]


@pytest.mark.parametrize("missing", REQUIRED_FIELDS)
def test_required_field_missing(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator, missing: str):
    fields = request_fields()
    del fields[missing]

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, fields)
    assert r.status_code == 422, f"Request without {missing} must be rejected: {r.text}"


def test_operator_number_document_required(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"privilege_a1": pdf()}, request_fields())
    assert r.status_code == 422, f"Request without operator_number must be rejected: {r.text}"


def test_file_type_detected_by_content(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(body=b"<html>not a pdf</html>")}

    r = create_request(client, pilot, get_endpoint_link, files, request_fields())
    assert r.status_code == 422, f"Text renamed to .pdf must be rejected: {r.text}"


def test_file_size_limited(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(body=b"%PDF-" + b"0" * (10 * 1024 * 1024))}

    r = create_request(client, pilot, get_endpoint_link, files, request_fields())
    assert r.status_code == 413, f"File over 10 MB must be rejected: {r.text}"


def test_one_pending_request_until_withdrawn(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 409, f"Second pending request must be rejected: {r.text}"

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 200, f"Withdraw failed: {r.text}"
    assert r.json()["status"] == "withdrawn"
    assert r.json()["documents"] == [], "Withdrawn request must lose its documents"

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 409, f"Withdrawn request cannot be withdrawn again: {r.text}"

    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"New request after withdraw must be accepted: {r.text}"


def test_create_requires_auth(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields(), auth=False)
    assert r.status_code == 401, f"Request without token must be rejected: {r.text}"


def test_cannot_withdraw_foreign_request(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"

    stranger = functional.create_user()
    assert registration_flow(client, stranger, get_endpoint_link), "Registration failed"

    r = withdraw_request(client, stranger, get_endpoint_link, r.json()["id"])
    assert r.status_code == 404, f"Foreign request must look missing: {r.text}"


def test_approve_keeps_documents_when_asked(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}

    r = create_request(client, pilot, get_endpoint_link, files, request_fields(keep_documents="true"))
    assert r.status_code == 201, f"Request was not created: {r.text}"
    assert r.json()["keep_documents"] is True
    pilot_id = r.json()["pilot_id"]

    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"

    body = r.json()
    assert body["request"]["status"] == "approved"
    assert body["request"]["documents"] == [], "Originals must leave the verification bucket"
    kept = body["kept_documents"]
    assert len(kept) == 2, f"Both documents must be kept: {kept}"
    assert all(key.startswith(f"pilots/{pilot_id}/") for key in kept), f"Wrong folder: {kept}"
    assert any(key.endswith(".png") for key in kept), f"Extension must survive the copy: {kept}"


def test_approve_deletes_documents_without_consent(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields(keep_documents="false"))
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"
    assert r.json()["kept_documents"] == [], "Pilot did not agree to keep documents"
    assert r.json()["request"]["documents"] == []


def test_reject_never_keeps_documents(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields(keep_documents="true"))
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = reject_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Reject failed: {r.text}"
    assert r.json()["status"] == "rejected"
    assert r.json()["documents"] == []


def test_approve_fills_profile_and_replaces_phone(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    first = request_fields()
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, first)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"

    profile = pilot_profile(client, pilot, get_endpoint_link).json()
    assert (profile["first_name"], profile["last_name"]) == (first["first_name"], first["last_name"])
    assert profile["phone_number"] == first["phone_number"]

    second = request_fields(first_name="Other", last_name="Person")
    r = create_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, second)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"

    profile = pilot_profile(client, pilot, get_endpoint_link).json()
    assert (profile["first_name"], profile["last_name"]) == (first["first_name"], first["last_name"]), "Names must not be overwritten"
    assert profile["phone_number"] == second["phone_number"], "Phone must follow the approved request"
