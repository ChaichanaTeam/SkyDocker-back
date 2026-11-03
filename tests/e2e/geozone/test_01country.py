from httpx import Client

from tests import constants
from tests.types import PilotInfo, UserInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import checkin_preview
from tests.utils.behavioural.geozone_behaviour import country_at_point, supported_countries


# The frontend path to a check-in: supported countries, the country at the home point, then the preview
POINT = constants.CHECKIN_CLEAN_POINT

_state: dict[str, object] = {}


def test_supported_countries(client: Client, borders_env: UserInfo, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = supported_countries(client, pilot, get_endpoint_link)
    assert r.status_code == 200, f"Supported countries were not listed: {r.text}"
    _state["supported"] = r.json()["countries"]


def test_country_at_home_point(client: Client, borders_env: UserInfo, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = country_at_point(client, pilot, get_endpoint_link, POINT)
    assert r.status_code == 200, f"Country at the home point was not resolved: {r.text}"

    tag = r.json()["country_tag"]
    assert tag in _state["supported"], f"Home point country {tag} is not supported: {r.text}"  # type: ignore
    _state["country_tag"] = tag


def test_preview_with_resolved_country(client: Client, borders_env: UserInfo, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(POINT, pilot["drone_id"], country_tag=_state["country_tag"])

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 200, f"Preview with the resolved country failed: {r.text}"
