from datetime import date, timedelta
from typing import Any

import pytest
from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.verification_behaviour import (
    PNG, approve_request, pdf, pilot_profile, preview_request, reject_request,
    submit_request, upload_documents, withdraw_request
)


REQUIRED_FIELDS = ("first_name", "last_name", "phone_number")
OPERATOR_ONLY = ["operator_number"]
A1_EXPIRY = {"a1": (date.today() + timedelta(days=365)).isoformat()}


def request_fields(**overrides: Any) -> dict[str, Any]:
    return {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone_number": functional.random_phone(),
        "pilot_number": "POL-RP-TEST0001",
        **overrides,
    }


def error_types(body: dict[str, Any]) -> set[str]:
    return {error["type"] for error in body["detail"]}


@pytest.fixture
def pilot(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator) -> UserInfo:
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"
    return new_user


@pytest.fixture
def numbered_pilot(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator) -> UserInfo:
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"
    return pilot


def test_create_stores_fields(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = request_fields()
    documents = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}

    r = submit_request(client, pilot, get_endpoint_link, documents, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    body = r.json()
    assert body["status"] == "pending"
    assert (body["first_name"], body["last_name"]) == (fields["first_name"], fields["last_name"])
    assert body["phone_number"] == fields["phone_number"]
    assert body["pilot_number"] == fields["pilot_number"]
    assert body["keep_documents"] is False, "Documents must not be kept without consent"
    assert "email" not in body
    assert sorted(d["document_type"] for d in body["documents"]) == ["operator_number", "privilege_a1"]
    assert all(d["url"] is None for d in body["documents"]), "Pilot must not get download links"


@pytest.mark.parametrize("missing", REQUIRED_FIELDS)
def test_preview_required_field_missing(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator, missing: str):
    fields = request_fields()
    del fields[missing]

    r = preview_request(client, pilot, get_endpoint_link, fields, OPERATOR_ONLY)
    assert r.status_code == 422, f"Preview without {missing} must be rejected: {r.text}"


@pytest.mark.parametrize("types", [[], ["privilege_a1", "privilege_a1"], ["unknown"]])
def test_preview_invalid_document_types(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator, types: list[str]):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), types)
    assert r.status_code == 422, f"Document types {types} must be rejected: {r.text}"


def test_preview_collects_pilot_number_errors(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = request_fields()
    del fields["pilot_number"]

    r = preview_request(client, pilot, get_endpoint_link, fields, ["privilege_a1"])
    assert r.status_code == 422, f"Pilot without a number must pass it: {r.text}"
    assert error_types(r.json()) == {"verification.pilot_number_required", "verification.operator_number_required"}


def test_preview_conflicts_with_pending(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    assert r.status_code == 409, f"Preview must see the pending request: {r.text}"


def test_pilot_with_number_sends_only_certificates(client: Client, numbered_pilot: UserInfo, get_endpoint_link: EndpointCreator):
    fields = request_fields()
    number = fields.pop("pilot_number")

    r = submit_request(client, numbered_pilot, get_endpoint_link, {"privilege_a2": pdf()}, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    assert r.json()["pilot_number"] == number, "Number must come from the profile"


def test_pilot_with_number_cannot_resend_it(client: Client, numbered_pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, numbered_pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    assert r.status_code == 422, f"Pilot already has a number: {r.text}"
    assert error_types(r.json()) == {"verification.pilot_number_already_set", "verification.operator_number_already_set"}


def test_upload_rejects_invalid_token(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = upload_documents(client, pilot, get_endpoint_link, "not-a-token", {"operator_number": pdf()})
    assert r.status_code == 404, f"Invalid token must be rejected: {r.text}"


def test_upload_rejects_foreign_token(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    assert r.status_code == 200, f"Preview failed: {r.text}"

    stranger = functional.create_user()
    assert registration_flow(client, stranger, get_endpoint_link), "Registration failed"

    r = upload_documents(client, stranger, get_endpoint_link, r.json()["verification_token"], {"operator_number": pdf()})
    assert r.status_code == 404, f"Foreign token must be rejected: {r.text}"


def test_upload_must_match_preview(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    assert r.status_code == 200, f"Preview failed: {r.text}"
    token = r.json()["verification_token"]

    r = upload_documents(client, pilot, get_endpoint_link, token, {"privilege_a1": pdf()})
    assert r.status_code == 422, f"Types differ from the preview: {r.text}"
    assert error_types(r.json()) == {"verification.document_types_mismatch"}

    r = upload_documents(client, pilot, get_endpoint_link, token, {"operator_number": pdf(), "privilege_a1": pdf()}, OPERATOR_ONLY)
    assert r.status_code == 422, f"More files than types: {r.text}"
    assert error_types(r.json()) == {"verification.files_mismatch"}


def test_upload_is_single_use_while_pending(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    token = r.json()["verification_token"]

    r = upload_documents(client, pilot, get_endpoint_link, token, {"operator_number": pdf()})
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = upload_documents(client, pilot, get_endpoint_link, token, {"operator_number": pdf()})
    assert r.status_code == 409, f"Second upload must be rejected: {r.text}"


def test_file_type_detected_by_content(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(body=b"<html>not a pdf</html>"), "privilege_a1": pdf(body=b"also not a pdf")}

    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields())
    assert r.status_code == 422, f"Text renamed to .pdf must be rejected: {r.text}"
    assert len(r.json()["detail"]) == 2, f"All bad files must be reported: {r.text}"


def test_file_size_limited(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(body=b"%PDF-" + b"0" * (10 * 1024 * 1024))}

    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields())
    assert r.status_code == 413, f"File over 10 MB must be rejected: {r.text}"


def test_upload_larger_than_declared(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY)
    token = r.json()["verification_token"]

    r = upload_documents(client, pilot, get_endpoint_link, token, {"operator_number": pdf(body=b"%PDF-" + b"0" * (12 * 1024 * 1024))})
    assert r.status_code == 413, f"Body over the declared limit must be rejected: {r.text}"


def test_one_pending_request_until_withdrawn(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 200, f"Withdraw failed: {r.text}"
    assert r.json()["status"] == "withdrawn"
    assert r.json()["documents"] == [], "Withdrawn request must lose its documents"

    r = withdraw_request(client, pilot, get_endpoint_link, request_id)
    assert r.status_code == 409, f"Withdrawn request cannot be withdrawn again: {r.text}"

    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"New request after withdraw must be accepted: {r.text}"


def test_preview_requires_auth(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = preview_request(client, pilot, get_endpoint_link, request_fields(), OPERATOR_ONLY, auth=False)
    assert r.status_code == 401, f"Preview without token must be rejected: {r.text}"


def test_cannot_withdraw_foreign_request(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"

    stranger = functional.create_user()
    assert registration_flow(client, stranger, get_endpoint_link), "Registration failed"

    r = withdraw_request(client, stranger, get_endpoint_link, r.json()["id"])
    assert r.status_code == 404, f"Foreign request must look missing: {r.text}"


def test_approve_keeps_documents_when_asked(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}

    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields(keep_documents=True))
    assert r.status_code == 201, f"Request was not created: {r.text}"
    assert r.json()["keep_documents"] is True
    pilot_id = r.json()["pilot_id"]

    r = approve_request(client, get_endpoint_link, r.json()["id"], A1_EXPIRY)
    assert r.status_code == 200, f"Approve failed: {r.text}"

    body = r.json()
    assert body["request"]["status"] == "approved"
    assert body["request"]["documents"] == [], "Originals must leave the verification bucket"
    kept = body["kept_documents"]
    assert len(kept) == 2, f"Both documents must be kept: {kept}"
    assert all(key.startswith(f"pilots/{pilot_id}/") for key in kept), f"Wrong folder: {kept}"
    assert any(key.endswith(".png") for key in kept), f"Extension must survive the copy: {kept}"


def test_approve_deletes_documents_without_consent(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields(keep_documents=False))
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"
    assert r.json()["kept_documents"] == [], "Pilot did not agree to keep documents"
    assert r.json()["request"]["documents"] == []


def test_reject_never_keeps_documents(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, request_fields(keep_documents=True))
    assert r.status_code == 201, f"Request was not created: {r.text}"

    r = reject_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Reject failed: {r.text}"
    assert r.json()["status"] == "rejected"
    assert r.json()["documents"] == []


def test_approve_fills_profile_and_replaces_phone(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    first = request_fields()
    r = submit_request(client, pilot, get_endpoint_link, {"operator_number": pdf()}, first)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"])
    assert r.status_code == 200, f"Approve failed: {r.text}"

    profile = pilot_profile(client, pilot, get_endpoint_link).json()
    assert (profile["first_name"], profile["last_name"]) == (first["first_name"], first["last_name"])
    assert profile["phone_number"] == first["phone_number"]

    second = request_fields(first_name="Other", last_name="Person")
    del second["pilot_number"]
    r = submit_request(client, pilot, get_endpoint_link, {"privilege_a1": pdf()}, second)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"], A1_EXPIRY)
    assert r.status_code == 200, f"Approve failed: {r.text}"

    profile = pilot_profile(client, pilot, get_endpoint_link).json()
    assert (profile["first_name"], profile["last_name"]) == (first["first_name"], first["last_name"]), "Names must not be overwritten"
    assert profile["phone_number"] == second["phone_number"], "Phone must follow the approved request"


def test_approve_requires_expiry_of_every_privilege(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(), "privilege_a1": pdf()}
    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    r = approve_request(client, get_endpoint_link, request_id)
    assert r.status_code == 422, f"Privilege without a date must be rejected: {r.text}"
    assert error_types(r.json()) == {"verification.expiry_missing"}

    r = approve_request(client, get_endpoint_link, request_id, A1_EXPIRY)
    assert r.status_code == 200, f"Request must stay pending after a failed approve: {r.text}"
    assert r.json()["granted"] == ["a1"]


def test_approve_rejects_wrong_expiry(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(), "privilege_a1": pdf()}
    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    r = approve_request(client, get_endpoint_link, request_id, {**A1_EXPIRY, "a2": A1_EXPIRY["a1"]})
    assert r.status_code == 422, f"Date for a missing certificate must be rejected: {r.text}"
    assert error_types(r.json()) == {"verification.expiry_unexpected"}

    yesterday = (date.today() - timedelta(days=2)).isoformat()
    r = approve_request(client, get_endpoint_link, request_id, {"a1": yesterday})
    assert r.status_code == 422, f"Expired certificate must be rejected: {r.text}"
    assert error_types(r.json()) == {"verification.expiry_in_past"}


def test_approve_renews_existing_privilege(client: Client, pilot: UserInfo, get_endpoint_link: EndpointCreator):
    documents = {"operator_number": pdf(), "privilege_a1": pdf()}
    r = submit_request(client, pilot, get_endpoint_link, documents, request_fields())
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"], A1_EXPIRY)
    assert (r.json()["granted"], r.json()["renewed"]) == (["a1"], [])

    fields = request_fields()
    del fields["pilot_number"]
    r = submit_request(client, pilot, get_endpoint_link, {"privilege_a1": pdf()}, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    r = approve_request(client, get_endpoint_link, r.json()["id"], A1_EXPIRY)
    assert r.status_code == 200, f"Approve failed: {r.text}"
    assert (r.json()["granted"], r.json()["renewed"], r.json()["privileges"]) == ([], ["a1"], ["a1"])
