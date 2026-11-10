import os
from importlib.util import find_spec
import pytest
from httpx import Client

from tests.types import UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.login_behaviour import login
from tests.utils.behavioural.pilot_behaviour import pilot_get
from tests.utils.behavioural.moderator_behaviour import (
    REFRESH_COOKIE_NAME, moderator_login, moderator_refresh, moderator_logout, moderator_me
)


# The tokens are signed with the server key, so forging needs the same .env and the backend sources
can_forge = pytest.mark.skipif(
    find_spec("backend_src") is None or not os.getenv("SECRET_KEY"),
    reason="Forging tokens needs backend_src and the server SECRET_KEY",
)


def test_login_unknown_moderator_rejected(client: Client, new_user: UserInfo, get_endpoint_link: EndpointCreator):
    r = moderator_login(client, new_user["email"], new_user["password"], get_endpoint_link)

    assert r.status_code == 401, f"Unknown moderator should be rejected: {r.text}"
    assert REFRESH_COOKIE_NAME not in r.headers.get("set-cookie", ""), "Failed login must not set a refresh cookie"


def test_pilot_credentials_do_not_log_in_moderator(
    client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator
):
    r = moderator_login(client, registered_user["email"], registered_user["password"], get_endpoint_link)
    assert r.status_code == 401, f"Pilot account must not log in as moderator: {r.text}"


def test_refresh_without_cookie_rejected(client: Client, get_endpoint_link: EndpointCreator):
    r = moderator_refresh(client, get_endpoint_link)
    assert r.status_code == 401, f"Refresh without cookie should be rejected: {r.text}"


def test_refresh_with_garbage_cookie_rejected_and_cleared(client: Client, get_endpoint_link: EndpointCreator):
    r = moderator_refresh(client, get_endpoint_link, cookie="not-a-token")

    assert r.status_code == 401, f"Garbage refresh cookie should be rejected: {r.text}"
    set_cookie = r.headers.get("set-cookie", "")
    assert REFRESH_COOKIE_NAME in set_cookie and "Max-Age=0" in set_cookie, "Rejected refresh must clear the cookie"


def test_refresh_with_pilot_refresh_token_rejected(
    client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator
):
    r = login(client, registered_user, get_endpoint_link)
    assert r.status_code == 200, f"Pilot login failed: {r.text}"

    r = moderator_refresh(client, get_endpoint_link, cookie=r.json()["refresh_token"])
    assert r.status_code == 401, f"Pilot refresh token must not refresh a moderator session: {r.text}"


def test_logout_without_cookie_succeeds(client: Client, get_endpoint_link: EndpointCreator):
    r = moderator_logout(client, get_endpoint_link)
    assert r.status_code == 200, f"Logout should always succeed: {r.text}"


def test_me_without_token_rejected(client: Client, get_endpoint_link: EndpointCreator):
    r = moderator_me(client, get_endpoint_link)
    assert r.status_code in (401, 403), f"Moderator endpoint must require a token: {r.text}"


def test_me_with_pilot_access_token_rejected(
    client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator
):
    r = moderator_me(client, get_endpoint_link, registered_user["tokens"]["access_token"])
    assert r.status_code == 401, f"Pilot access token must not pass the moderator dependency: {r.text}"


@can_forge
def test_moderator_access_token_rejected_by_pilot_endpoint(
    client: Client, registered_user: UserInfo, get_endpoint_link: EndpointCreator
):
    from backend_src.core.security import create_moderator_access_token

    r = pilot_get(client, registered_user, get_endpoint_link, "me")
    assert r.status_code == 200, f"Pilot profile failed: {r.text}"

    # Same subject id as the pilot, only the token type differs
    forged = create_moderator_access_token(str(r.json()["id"]), 0).token
    impostor = functional.create_user()
    impostor["tokens"]["type"] = "Bearer"
    impostor["tokens"]["access_token"] = forged

    r = pilot_get(client, impostor, get_endpoint_link, "me")
    assert r.status_code == 401, f"Moderator access token must not pass the pilot dependency: {r.text}"


def test_cors_preflight_allows_dashboard_origin(client: Client, get_endpoint_link: EndpointCreator):
    origin = (os.getenv("CORS_ORIGINS") or "http://localhost:3000").split(",")[0].strip()
    r = client.options(
        get_endpoint_link("live", "moderator/auth/refresh"),
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )

    assert r.status_code == 200, f"Preflight from the dashboard origin failed: {r.text}"
    assert r.headers.get("access-control-allow-origin") == origin
    assert r.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_rejects_unknown_origin(client: Client, get_endpoint_link: EndpointCreator):
    r = client.options(
        get_endpoint_link("live", "moderator/auth/refresh"),
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert "access-control-allow-origin" not in r.headers, "Unknown origin must not be allowed"
