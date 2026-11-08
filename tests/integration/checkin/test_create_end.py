from httpx import Client

from tests import constants
from tests.types import PilotInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import (
    checkin_preview, checkin_create, checkin_end, checkin_flow
)


CLEAN = constants.CHECKIN_CLEAN_POINT


def test_create_with_garbage_token(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_create(client, new_pilot, get_endpoint_link, token="not-a-token")
    assert r.status_code == 404, f"A garbage token is not a verified check-in: {r.text}"


def test_create_with_access_token(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_create(client, new_pilot, get_endpoint_link, token=new_pilot["tokens"]["access_token"])
    assert r.status_code == 404, f"An access token must not pass as a check-in token: {r.text}"


def test_create_with_token_of_another_pilot(
    client: Client, new_pilot: PilotInfo, other_pilot: PilotInfo, get_endpoint_link: EndpointCreator
):
    r = checkin_preview(client, other_pilot, get_endpoint_link, functional.checkin_plan(CLEAN, other_pilot["drone_id"]))
    assert r.status_code == 200, f"Preview failed: {r.text}"
    foreign_token = r.json()["checkin_token"]

    r = checkin_create(client, new_pilot, get_endpoint_link, token=foreign_token)
    assert r.status_code == 404, f"A token of another pilot must not start a check-in: {r.text}"

    r = checkin_end(client, new_pilot, get_endpoint_link)
    assert r.status_code == 404, f"Rejected token must not leave a check-in behind: {r.text}"


def test_preview_while_active(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_flow(client, new_pilot, get_endpoint_link, CLEAN)
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    r = checkin_preview(client, new_pilot, get_endpoint_link, functional.checkin_plan(CLEAN, new_pilot["drone_id"]))
    assert r.status_code == 409, f"A pilot must not plan a second check-in while one is active: {r.text}"


def test_second_token_while_active(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(CLEAN, new_pilot["drone_id"])
    tokens = []
    for _ in range(2):
        r = checkin_preview(client, new_pilot, get_endpoint_link, plan)
        assert r.status_code == 200, f"Preview failed: {r.text}"
        tokens.append(r.json()["checkin_token"])

    r = checkin_create(client, new_pilot, get_endpoint_link, token=tokens[0])
    assert r.status_code == 201, f"Check-in was not started: {r.text}"

    r = checkin_create(client, new_pilot, get_endpoint_link, token=tokens[1])
    assert r.status_code == 409, f"A second verified token must not start a parallel check-in: {r.text}"


def test_end_without_active(client: Client, new_pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    r = checkin_end(client, new_pilot, get_endpoint_link)
    assert r.status_code == 404, f"There is no check-in in progress to end: {r.text}"


def test_create_and_end_without_token_rejected(client: Client, get_endpoint_link: EndpointCreator):
    r = client.post(get_endpoint_link("live", "check-in/"), json={"checkin_token": "any"})
    assert r.status_code in (401, 403), f"Create without a token should be rejected: {r.text}"

    r = client.post(get_endpoint_link("live", "check-in/end"))
    assert r.status_code in (401, 403), f"End without a token should be rejected: {r.text}"


def test_bbox_without_token_rejected(client: Client, get_endpoint_link: EndpointCreator):
    lon, lat = CLEAN
    params = {"min_lon": lon - 0.01, "min_lat": lat - 0.01, "max_lon": lon + 0.01, "max_lat": lat + 0.01}

    r = client.get(get_endpoint_link("live", "check-in/"), params=params)
    assert r.status_code in (401, 403), f"Check-ins on the map are only for pilots: {r.text}"
