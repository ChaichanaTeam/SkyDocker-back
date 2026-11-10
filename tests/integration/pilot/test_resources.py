import pytest
from httpx import Client

from tests import constants
from tests.types import EndpointCreator, PilotInfo, UserInfo
from tests.utils.behavioural.checkin_behaviour import checkin_end, checkin_flow
from tests.utils.behavioural.pilot_behaviour import pilot_get


CLEAN = constants.CHECKIN_CLEAN_POINT


def test_privileges(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = pilot_get(client, new_pilot, get_endpoint_link, "me/privileges")
    assert r.status_code == 200, f"Privileges failed: {r.text}"
    assert r.json() == [{"flying_privilege": "a1", "expires_at": None}]


def test_drones(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = pilot_get(client, new_pilot, get_endpoint_link, "me/drones")
    assert r.status_code == 200, f"Drones failed: {r.text}"

    drones = r.json()
    assert [drone["id"] for drone in drones] == [new_pilot["drone_id"]]
    assert {"manufacturer", "model_name", "mtom"} <= set(drones[0]["model"])


def test_drone_by_id(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = pilot_get(client, new_pilot, get_endpoint_link, f"me/drones/{new_pilot['drone_id']}")
    assert r.status_code == 200, f"Drone failed: {r.text}"
    assert r.json()["id"] == new_pilot["drone_id"]


def test_drone_of_another_pilot(client: Client, new_pilot: PilotInfo, other_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = pilot_get(client, new_pilot, get_endpoint_link, f"me/drones/{other_pilot['drone_id']}")
    assert r.status_code == 404, f"A drone of another pilot must look missing: {r.text}"

    r = pilot_get(client, new_pilot, get_endpoint_link, "me/drones")
    assert other_pilot["drone_id"] not in [drone["id"] for drone in r.json()]


@pytest.mark.parametrize("path,empty", [
    ("me/privileges", []),
    ("me/drones", []),
    ("me/missions", {"type": "FeatureCollection", "features": []}),
    ("me/check-ins", {"type": "FeatureCollection", "features": []}),
])
def test_empty_lists(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator, path: str, empty):
    r = pilot_get(client, fresh_user, get_endpoint_link, path)
    assert r.status_code == 200, f"An empty list is not an error: {r.text}"
    assert r.json() == empty


@pytest.mark.parametrize("path", ["me/drones/999999999999", "me/missions/999999999999", "me/check-ins/active"])
def test_missing(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator, path: str):
    r = pilot_get(client, fresh_user, get_endpoint_link, path)
    assert r.status_code == 404, f"{path} must not be found: {r.text}"


@pytest.mark.parametrize("path", ["me/missions", "me/check-ins"])
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 2**63}])
def test_page_bounds(client: Client, fresh_user: UserInfo, get_endpoint_link: EndpointCreator, path: str, params: dict):
    r = pilot_get(client, fresh_user, get_endpoint_link, path, params)
    assert r.status_code == 422, f"{params} must be rejected: {r.text}"


def test_checkin_active_and_history(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_flow(client, new_pilot, get_endpoint_link, CLEAN)
    assert r.status_code == 201, f"Check-in was not started: {r.text}"
    checkin_id = r.json()["properties"]["id"]

    r = pilot_get(client, new_pilot, get_endpoint_link, "me/check-ins/active")
    assert r.status_code == 200, f"Active check-in failed: {r.text}"
    assert r.json()["properties"]["id"] == checkin_id
    assert r.json()["properties"]["drone_id"] == new_pilot["drone_id"]
    assert r.json()["properties"]["country_tag"] == "PL"
    assert r.json()["geometry"]["coordinates"] == list(CLEAN)

    r = checkin_end(client, new_pilot, get_endpoint_link)
    assert r.status_code == 200, f"Check-in was not ended: {r.text}"

    r = pilot_get(client, new_pilot, get_endpoint_link, "me/check-ins/active")
    assert r.status_code == 404, f"An ended check-in is not active: {r.text}"

    r = pilot_get(client, new_pilot, get_endpoint_link, "me/check-ins")
    assert r.status_code == 200, f"History failed: {r.text}"
    features = r.json()["features"]
    assert [feature["properties"]["id"] for feature in features] == [checkin_id]
    assert features[0]["properties"]["status"] == "ended_intime"


def test_history_is_private(client: Client, new_pilot: PilotInfo, other_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_flow(client, new_pilot, get_endpoint_link, CLEAN)
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    r = pilot_get(client, other_pilot, get_endpoint_link, "me/check-ins")
    assert r.status_code == 200 and r.json()["features"] == [], f"History of another pilot leaked: {r.text}"

    r = pilot_get(client, other_pilot, get_endpoint_link, "me/check-ins/active")
    assert r.status_code == 404, f"Check-in of another pilot leaked: {r.text}"
