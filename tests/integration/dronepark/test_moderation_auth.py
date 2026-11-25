from typing import Callable, Optional

import pytest
from httpx import Client, Response

from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.dronepark_behaviour import approve_model, delete_model, replace_model, unverified_models


# The model ids do not matter, the token is checked before the model is looked up
MODERATION_CALLS: dict[str, Callable[[Client, Optional[str], EndpointCreator], Response]] = {
    "unverified": lambda client, token, link: unverified_models(client, token, link),
    "approve": lambda client, token, link: approve_model(client, token, link, 1, {}),
    "replace": lambda client, token, link: replace_model(client, token, link, 1, 1),
    "delete": lambda client, token, link: delete_model(client, token, link, 1),
}


@pytest.mark.parametrize("call", MODERATION_CALLS.values(), ids=MODERATION_CALLS.keys())
def test_moderation_without_token(client: Client, get_endpoint_link: EndpointCreator, call):
    r = call(client, None, get_endpoint_link)
    assert r.status_code in (401, 403), f"Drone model moderation must require a token: {r.text}"


@pytest.mark.parametrize("call", MODERATION_CALLS.values(), ids=MODERATION_CALLS.keys())
def test_moderation_with_pilot_token(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator, call):
    r = call(client, registered_user["tokens"]["access_token"], get_endpoint_link)
    assert r.status_code == 401, f"Pilot access token must not pass the moderator dependency: {r.text}"
