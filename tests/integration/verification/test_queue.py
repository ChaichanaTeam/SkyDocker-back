from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.verification_behaviour import find_in_queue, list_requests, release_review, review_request


def _queued(client: Client, moderator: str, get_endpoint_link: EndpointCreator, request_id: int) -> dict:
    item = find_in_queue(client, moderator, get_endpoint_link, request_id, "pending")
    assert item is not None, f"Pending request {request_id} must be in the queue"
    return item


def test_queue_without_token(client: Client, get_endpoint_link: EndpointCreator):
    r = list_requests(client, None, get_endpoint_link)
    assert r.status_code in (401, 403), f"The queue must require a token: {r.text}"


def test_queue_with_pilot_token(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = list_requests(client, registered_user["tokens"]["access_token"], get_endpoint_link)
    assert r.status_code == 401, f"A pilot must not see the moderator queue: {r.text}"


def test_queue_shows_review(client: Client, moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator):
    request_id = pending_request["id"]
    item = _queued(client, moderator, get_endpoint_link, request_id)
    assert item["review"] is None, f"An unopened request must be free: {item}"
    assert all(document["url"] is None for document in item["documents"]), f"The queue must not give document links: {item}"

    review_request(client, moderator, get_endpoint_link, request_id)
    try:
        review = _queued(client, moderator, get_endpoint_link, request_id)["review"]
        assert review is not None and review["moderator"]["id"], f"An opened request must show its reviewer: {review}"
        assert review["expires_in"] > 0, f"The time left of the review must be shown: {review}"
    finally:
        release_review(client, moderator, get_endpoint_link, request_id)

    assert _queued(client, moderator, get_endpoint_link, request_id)["review"] is None, "A released request must be free again"


def test_queue_order_and_filter(client: Client, moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator):
    r = list_requests(client, moderator, get_endpoint_link, status="pending", limit=200)
    assert r.status_code == 200, f"The queue was not listed: {r.text}"

    items = r.json()
    assert all(item["status"] == "pending" for item in items), "The filter must keep only pending requests"
    created = [item["created_at"] for item in items]
    assert created == sorted(created), "The oldest request must come first"

    r = list_requests(client, moderator, get_endpoint_link, limit=1)
    assert len(r.json()) == 1, f"limit must cut the page: {r.text}"
    r = list_requests(client, moderator, get_endpoint_link, limit=201)
    assert r.status_code == 422, f"A page is at most 200 requests: {r.text}"


def test_demo_list_is_gone(client: Client, get_endpoint_link: EndpointCreator):
    r = client.get(get_endpoint_link("demo", "verification-requests/"))
    assert r.status_code == 405, f"The queue lives in v1 only now: {r.text}"
