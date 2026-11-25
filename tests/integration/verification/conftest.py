import pytest
from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.utils.behavioural.verification_behaviour import pdf, submit_request, withdraw_request


@pytest.fixture
def pending_request(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    """A pending request of a fresh pilot, withdrawn afterwards so its documents are deleted."""
    assert registration_flow(client, new_user, get_endpoint_link), "Registration failed"

    fields = {"first_name": "Jan", "last_name": "Kowalski", "phone_number": functional.random_phone(), "pilot_number": "POL-RP-TEST0001"}
    r = submit_request(client, new_user, get_endpoint_link, {"operator_number": pdf()}, fields)
    assert r.status_code == 201, f"Request was not created: {r.text}"

    yield r.json()
    withdraw_request(client, new_user, get_endpoint_link, r.json()["id"])
