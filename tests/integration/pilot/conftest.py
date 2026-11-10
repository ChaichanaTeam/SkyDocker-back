import pytest
from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow


def _registered(client: Client, get_endpoint_link: EndpointCreator) -> UserInfo:
    user = functional.create_user()
    assert registration_flow(client, user, get_endpoint_link), "Registration failed"

    return user


@pytest.fixture(scope="function")
def fresh_user(client: Client, get_endpoint_link: EndpointCreator) -> UserInfo:
    return _registered(client, get_endpoint_link)


@pytest.fixture(scope="function")
def other_user(client: Client, get_endpoint_link: EndpointCreator) -> UserInfo:
    return _registered(client, get_endpoint_link)
