import pytest
from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.verification_behaviour import release_review, review_request


MISSING_REQUEST_ID = 2_000_000_000


@pytest.mark.parametrize("call", [review_request, release_review], ids=["open", "release"])
def test_review_without_token(client: Client, get_endpoint_link: EndpointCreator, call):
    r = call(client, None, get_endpoint_link, MISSING_REQUEST_ID)
    assert r.status_code in (401, 403), f"Reviewing a request must require a token: {r.text}"


@pytest.mark.parametrize("call", [review_request, release_review], ids=["open", "release"])
def test_review_with_pilot_token(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator, call):
    r = call(client, registered_user["tokens"]["access_token"], get_endpoint_link, MISSING_REQUEST_ID)
    assert r.status_code == 401, f"Pilot access token must not pass the moderator dependency: {r.text}"


def test_open_request_for_review(client: Client, moderator: str, pending_request: dict, get_endpoint_link: EndpointCreator):
    request_id = pending_request["id"]

    try:
        r = review_request(client, moderator, get_endpoint_link, request_id)
        assert r.status_code == 200, f"Request was not opened: {r.text}"
        review = r.json()
        assert review["id"] == request_id and review["status"] == "pending", f"The request itself must be returned: {r.text}"
        assert review["pilot_number"] == pending_request["pilot_number"], f"The request fields must be returned: {r.text}"
        assert review["documents"] and all(document["url"] for document in review["documents"]), \
            f"Every document must come with a download link: {r.text}"
        assert review["review_expires_in"] > 0, f"A pending request must be locked to the moderator: {r.text}"

        r = review_request(client, moderator, get_endpoint_link, request_id)
        assert r.status_code == 200, f"The moderator who holds the lock must open the request again: {r.text}"
    finally:
        r = release_review(client, moderator, get_endpoint_link, request_id)
        assert r.status_code == 200, f"The lock was not released: {r.text}"

    r = release_review(client, moderator, get_endpoint_link, request_id)
    assert r.status_code == 200, f"Releasing a free request must succeed: {r.text}"


def test_review_missing_request(client: Client, moderator: str, get_endpoint_link: EndpointCreator):
    assert review_request(client, moderator, get_endpoint_link, MISSING_REQUEST_ID).status_code == 404
    assert release_review(client, moderator, get_endpoint_link, MISSING_REQUEST_ID).status_code == 404
