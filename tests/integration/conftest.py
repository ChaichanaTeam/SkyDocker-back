from typing import Iterator
import pytest
from httpx import Client

from tests.types import EndpointCreator, PilotInfo, UserInfo
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import pilot_lifetime


@pytest.fixture(scope="function")
def new_user() -> UserInfo:
    return functional.create_user()


@pytest.fixture(scope="function")
def new_pilot(client: Client, get_endpoint_link: EndpointCreator, checkin_env: None) -> Iterator[PilotInfo]:
    yield from pilot_lifetime(client, get_endpoint_link)


@pytest.fixture(scope="function")
def other_pilot(client: Client, get_endpoint_link: EndpointCreator, checkin_env: None) -> Iterator[PilotInfo]:
    yield from pilot_lifetime(client, get_endpoint_link)
