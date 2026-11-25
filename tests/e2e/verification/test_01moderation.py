from datetime import date, timedelta

from httpx import Client

from tests.types import EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.pilot_behaviour import pilot_get
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.verification_behaviour import (
    PNG, approve_request, list_requests, pdf, review_request, submit_request,
)


def test_request_from_pilot_to_privilege(client: Client, moderator: str, get_endpoint_link: EndpointCreator):
    pilot = functional.create_user()
    assert registration_flow(client, pilot, get_endpoint_link), "Registration failed"

    # the pilot sends the operator registration and an A1 certificate
    fields = {
        "first_name": "Jan", "last_name": "Kowalski", "phone_number": functional.random_phone(),
        "pilot_number": "POL-RP-TEST0001", "keep_documents": False,
    }
    documents = {"operator_number": pdf(), "privilege_a1": ("a1.png", PNG, "image/png")}
    r = submit_request(client, pilot, get_endpoint_link, documents, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"
    request_id = r.json()["id"]

    # the moderator finds it free in the queue and opens it
    queue = list_requests(client, moderator, get_endpoint_link, status="pending", limit=200).json()
    queued = next(item for item in queue if item["id"] == request_id)
    assert queued["review"] is None, f"A new request must be free to open: {queued}"

    r = review_request(client, moderator, get_endpoint_link, request_id)
    assert r.status_code == 200 and all(document["url"] for document in r.json()["documents"]), \
        f"The moderator must get the documents: {r.text}"

    # and approves it with the last valid day read from the certificate
    expires_at = (date.today() + timedelta(days=5 * 365)).isoformat()
    r = approve_request(client, moderator, get_endpoint_link, request_id, {"a1": expires_at})
    assert r.status_code == 200, f"Request was not approved: {r.text}"
    assert r.json()["granted"] == ["a1"], f"The pilot must get the A1 privilege: {r.text}"

    privileges = pilot_get(client, pilot, get_endpoint_link, "me/privileges").json()
    assert {"flying_privilege": "a1", "expires_at": expires_at} in privileges, f"The privilege must reach the pilot: {privileges}"

    own = pilot_get(client, pilot, get_endpoint_link, "me/verification-requests").json()
    assert own[0]["id"] == request_id and own[0]["status"] == "approved", f"The pilot must see the approval: {own}"
    assert own[0]["verified_at"] is not None, f"The pilot must see when it was approved: {own}"
