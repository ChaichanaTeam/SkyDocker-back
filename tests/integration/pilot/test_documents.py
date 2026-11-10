from typing import Any

from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils import functional
from tests.utils.behavioural.pilot_behaviour import pilot_get
from tests.utils.behavioural.verification_behaviour import PNG, approve_request, pdf, submit_request


def _fields(**overrides: Any) -> dict[str, Any]:
    return {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone_number": functional.random_phone(),
        "pilot_number": "POL-RP-TEST0001",
        **overrides,
    }


def _approved_request(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, documents: dict, keep_documents: bool, expiry=None
) -> int:
    r = submit_request(client, user, get_endpoint_link, documents, _fields(keep_documents=keep_documents))
    assert r.status_code == 201, f"Request was not created: {r.text}"
    pilot_id = r.json()["pilot_id"]

    r = approve_request(client, get_endpoint_link, r.json()["id"], expiry)
    assert r.status_code == 200, f"Approve failed: {r.text}"

    return pilot_id


def _documents(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> list[dict[str, Any]]:
    r = pilot_get(client, user, get_endpoint_link, "me/documents")
    assert r.status_code == 200, f"Documents failed: {r.text}"

    return r.json()


def test_new_pilot_has_no_documents(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    assert _documents(client, fresh_user, get_endpoint_link) == []


def test_kept_documents_are_listed(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    files = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}
    pilot_id = _approved_request(client, fresh_user, get_endpoint_link, files, True, {"a1": "2099-01-01"})

    documents = _documents(client, fresh_user, get_endpoint_link)
    assert {document["document_type"] for document in documents} == set(files)
    assert all(f"pilots/{pilot_id}/" in document["url"] for document in documents), f"Wrong folder: {documents}"
    assert all(document["size"] > 0 and document["uploaded_at"] for document in documents), f"Incomplete: {documents}"


def test_documents_without_consent_are_not_listed(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator):
    _approved_request(client, fresh_user, get_endpoint_link, {"operator_number": pdf()}, False)

    assert _documents(client, fresh_user, get_endpoint_link) == []


def test_documents_are_private(client: Client, fresh_user: UserInfo, other_user: UserInfo, get_endpoint_link: EndpointCreator):
    _approved_request(client, other_user, get_endpoint_link, {"operator_number": pdf()}, True)

    assert _documents(client, fresh_user, get_endpoint_link) == [], "Documents of another pilot leaked"
