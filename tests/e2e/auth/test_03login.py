from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils.behavioural.logout_behaviour import logout_flow


def test_login(client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator):
    logout_flow(client, registered_user, get_endpoint_link)

    request = {
        "url": get_endpoint_link("live", "auth/login"),
        "json": {"email": registered_user["email"], "password": registered_user["password"]}
    }
    r = client.post(**request)
    assert r.status_code == 200, f"Login request failed: {r.text}"

    body = r.json()
    assert body.get("access_token") and body.get("refresh_token"), f"Login did not return access: {r.text}"