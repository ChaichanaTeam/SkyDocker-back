import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils
import httpx

@pytest.fixture(scope="module")
def client():
    session = httpx.Client()
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_user():
    user = {
        "email": utils.random_email(),
        "phone_number": "+48123456789",
        "first_name": "Name",
        "last_name": "Surname",
        "password": "p455w0rd"
    }

    yield user