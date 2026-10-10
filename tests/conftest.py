import os
from pathlib import Path
from typing import Literal, Optional
import pytest
from httpx import Client, RequestError, get, ConnectError

from tests.types import UserInfo, EndpointCreator
from tests import constants
from tests.utils import functional
from tests.utils.behavioural.registration_behaviour import registration_flow
from tests.config import Config


TESTS_ROOT = Path(__file__).parent
SUITES = ("smoke", "e2e", "integration")


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


def _suite_of(item: pytest.Item) -> str:
    return item.path.relative_to(TESTS_ROOT).parts[0]


def _module_of(item: pytest.Item) -> Optional[str]:
    # tests/<suite>/<module>/test_*.py
    parts = item.path.relative_to(TESTS_ROOT).parts

    return parts[1] if len(parts) > 2 else None


def _module_option(config: pytest.Config, name: str, env: str) -> set[str]:
    values = config.getoption(name) or [os.getenv(env, "")]

    return {module.strip() for value in values for module in value.split(",") if module.strip()}


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--suite",
        choices=SUITES,
        default=os.getenv("TEST_SUITE", "smoke"),
        help="Test suite to run after smoke tests (env: TEST_SUITE, default: smoke)",
    )
    parser.addoption(
        "--module",
        action="append",
        help="Run only these modules, comma separated, repeatable (env: TEST_MODULES)",
    )
    parser.addoption(
        "--exclude-module",
        action="append",
        help="Skip these modules, comma separated, repeatable (env: TEST_EXCLUDE_MODULES)",
    )


def pytest_sessionstart(session: pytest.Session):
    # Smoke tests don't talk to the server
    if session.config.getoption("suite") == "smoke":
        return

    check_backend()

    if not Config.is_server_ready:
        pytest.exit("Server is down or in critical condition", 1)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    allowed = {"smoke", config.getoption("suite")}
    included = _module_option(config, "module", "TEST_MODULES")
    excluded = _module_option(config, "exclude_module", "TEST_EXCLUDE_MODULES")

    known = {module for item in items if (module := _module_of(item))}
    unknown = (included | excluded) - known
    if unknown:
        raise pytest.UsageError(
            f"Unknown test modules: {', '.join(sorted(unknown))}. Known: {', '.join(sorted(known))}"
        )

    def is_selected(item: pytest.Item) -> bool:
        suite = _suite_of(item)
        if suite == "smoke":
            return True
        if suite not in allowed:
            return False

        module = _module_of(item)
        if included and module not in included:
            return False

        return module not in excluded

    selected = [item for item in items if is_selected(item)]
    deselected = [item for item in items if not is_selected(item)]

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    report = yield

    if report.failed and _suite_of(item) == "smoke":
        item.session.shouldstop = "Smoke test failed, remaining suites are skipped"

    return report