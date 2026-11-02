from httpx import Client

from tests import constants
from tests.types import PilotInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import (
    checkin_preview, checkin_create, checkin_end, checkin_bbox
)


POINT = constants.CHECKIN_CLEAN_POINT


def test_preview(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_preview(client, pilot, get_endpoint_link, functional.checkin_plan(POINT, pilot["drone_id"]))
    assert r.status_code == 200, f"Preview of a free flight failed: {r.text}"

    body = r.json()
    assert body.get("checkin_token"), f"Preview did not return a check-in token: {r.text}"
    assert body.get("expires_in") == 60, f"Check-in token should live a minute: {r.text}"
    pilot["checkin_token"] = body["checkin_token"]


def test_create(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_create(client, pilot, get_endpoint_link)
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    feature = r.json()
    assert feature["type"] == "Feature", f"Check-in should come as a GeoJSON feature: {r.text}"
    assert tuple(feature["geometry"]["coordinates"]) == POINT, f"Check-in is not at the home point: {r.text}"

    properties = feature["properties"]
    assert properties["status"] == "created", f"New check-in should be created: {r.text}"
    assert properties["contact"] == pilot["phone_number"], f"Check-in should show the pilot contact: {r.text}"
    assert properties["time"] == 30 * 60, f"Check-in should last the planned 30 minutes: {r.text}"


def test_create_again_conflicts(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_create(client, pilot, get_endpoint_link)
    assert r.status_code == 409, f"The same token must not start a second check-in: {r.text}"


def test_visible_in_bbox(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_bbox(client, pilot, get_endpoint_link, POINT)
    assert r.status_code == 200, f"Started check-in is not on the map: {r.text}"

    points = [tuple(feature["geometry"]["coordinates"]) for feature in r.json()["features"]]
    assert POINT in points, f"Started check-in is not on the map: {r.text}"


def test_end(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_end(client, pilot, get_endpoint_link)
    assert r.status_code == 200, f"Check-in was not ended: {r.text}"
    assert r.json()["properties"]["status"] == "ended_intime", f"Check-in should end in time: {r.text}"


def test_end_again(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_end(client, pilot, get_endpoint_link)
    assert r.status_code == 404, f"There is no check-in in progress to end: {r.text}"


def test_new_preview_after_end(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_preview(client, pilot, get_endpoint_link, functional.checkin_plan(POINT, pilot["drone_id"]))
    assert r.status_code == 200, f"Ended check-in must not block a new one: {r.text}"
