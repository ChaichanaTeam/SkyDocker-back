from datetime import date, timedelta

from httpx import Client

from tests.types import EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.verification_behaviour import (
    approve_request, list_requests, release_review, review_request,
)


A1_EXPIRY = {"a1": (date.today() + timedelta(days=365)).isoformat()}


def _queued(client: Client, moderator: str, get_endpoint_link: EndpointCreator, request_id: int, status: str) -> dict:
    items = list_requests(client, moderator, get_endpoint_link, status=status, limit=200).json()
    return next(item for item in items if item["id"] == request_id)


def test_approve_without_opening(client: Client, moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator):
    request_id = pending_request["id"]
    r = approve_request(client, moderator, get_endpoint_link, request_id)
    assert r.status_code == 200, f"The decision must take the review lock itself: {r.text}"
    assert r.json()["request"]["status"] == "approved", f"The request was not approved: {r.text}"

    item = _queued(client, moderator, get_endpoint_link, request_id, "approved")
    assert item["verified_by"] is not None, f"The moderator who approved must be stored: {item}"
    assert item["verified_at"] is not None, f"The time of the decision must be stored: {item}"


def test_approve_twice(client: Client, moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator):
    assert approve_request(client, moderator, get_endpoint_link, pending_request["id"]).status_code == 200
    r = approve_request(client, moderator, get_endpoint_link, pending_request["id"])
    assert r.status_code == 409, f"A decided request must not be decided again: {r.text}"


def test_approve_request_of_another_reviewer(
    client: Client, moderator: str, other_moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator,
):
    request_id = pending_request["id"]
    assert review_request(client, other_moderator, get_endpoint_link, request_id).status_code == 200, "Request was not opened"

    try:
        r = approve_request(client, moderator, get_endpoint_link, request_id)
        assert r.status_code == 409, f"A request another moderator reviews must not be approved: {r.text}"
        assert r.json()["detail"]["moderator"] is not None, f"The reviewer must be named: {r.text}"
    finally:
        release_review(client, other_moderator, get_endpoint_link, request_id)

    r = approve_request(client, moderator, get_endpoint_link, request_id)
    assert r.status_code == 200, f"A released request must be free to approve: {r.text}"


def test_wrong_expiry_keeps_lock(
    client: Client, moderator: str, other_moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator,
):
    request_id = pending_request["id"]
    r = approve_request(client, moderator, get_endpoint_link, request_id, A1_EXPIRY)
    assert r.status_code == 422, f"The request has no a1 certificate: {r.text}"
    assert functional.error_types(r) == {"verification.expiry_unexpected"}, f"Wrong error: {r.text}"

    r = review_request(client, other_moderator, get_endpoint_link, request_id)
    assert r.status_code == 409, f"After a wrong date the request must stay with its moderator: {r.text}"

    r = approve_request(client, moderator, get_endpoint_link, request_id)
    assert r.status_code == 200, f"The moderator must approve it after fixing the date: {r.text}"


def test_approve_with_pilot_token(client: Client, pending_request: dict, registered_user: dict, get_endpoint_link: EndpointCreator):
    r = approve_request(client, registered_user["tokens"]["access_token"], get_endpoint_link, pending_request["id"])
    assert r.status_code == 401, f"A pilot must not approve requests: {r.text}"


def test_demo_approve_is_gone(client: Client, get_endpoint_link: EndpointCreator):
    r = client.post(get_endpoint_link("demo", "verification-requests/1/approve"), json={"privilege_expiry": {}})
    assert r.status_code in (404, 405), f"Requests are approved only by moderators now: {r.text}"
