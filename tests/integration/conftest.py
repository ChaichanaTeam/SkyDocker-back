import pytest

from tests.types import UserInfo
from tests.utils import functional


@pytest.fixture(scope="function")
def new_user() -> UserInfo:
    return functional.create_user()
