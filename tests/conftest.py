from typing import Literal
import pytest
from httpx import Client, RequestError, get, ConnectError

from tests.types import UserInfo, EndpointCreator
from tests import constants
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.config import Config


@pytest.fixture(scope="session")
def client():
    session = Client()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_user():
    yield functional.create_user()


@pytest.fixture(scope="session")
def get_endpoint_link():
    def _get_endpoint_link(version: Literal["live"] | Literal["demo"], path: str):
        if version == "live":
            return constants.LIVE_API_LINK.join(path)
        elif version == "demo":
            return constants.DEMO_API_LINK.join(path)

    return _get_endpoint_link


@pytest.fixture(scope="module")
def registered_user(client: Client, test_user: UserInfo, get_endpoint_link: EndpointCreator) -> UserInfo:
    assert registration_flow(client, test_user, get_endpoint_link), "Registration failed"

    return test_user


def check_backend() -> None:
    try:
        r = get(constants.LIVE_API_LINK.join("health"))
        Config.is_server_ready = (r.status_code == 200)

        r = get(constants.DEMO_API_LINK)
        Config.is_server_in_debug = (r.status_code == 200)
    except (RequestError, ConnectError):
        return


def pytest_sessionstart(session):
    check_backend()

    if not Config.is_server_ready:
        pytest.exit("Server is down or in critical condition", 1)