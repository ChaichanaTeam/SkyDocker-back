import pytest
from httpx import Client

from tests import constants
from tests.types import PilotInfo, EndpointCreator
from tests.utils import functional
from tests.utils.behavioural.checkin_behaviour import checkin_preview


CLEAN = constants.CHECKIN_CLEAN_POINT


def _only_error(r) -> dict:
    errors = r.json()["detail"]
    assert len(errors) == 1, f"Expected exactly one error: {r.text}"

    return errors[0]


def test_home_point_outside_country_airspace(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(constants.CHECKIN_OUTSIDE_POINT, pilot["drone_id"])

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 404, f"A flight outside the country airspace cannot be verified: {r.text}"


def test_unsupported_country(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(CLEAN, pilot["drone_id"], country_tag="DE")

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 404, f"A country without a zone catalog cannot be verified: {r.text}"


def test_zone_needs_consent(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(constants.CHECKIN_CONSENT_POINT, pilot["drone_id"])

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"A flight into a consent zone must be rejected: {r.text}"
    assert functional.error_types(r) == {"checkin.zone_needs_consent"}, f"Wrong reason: {r.text}"
    assert all(error["loc"] == ["body", "height"] for error in r.json()["detail"]), f"Should point to height: {r.text}"


def test_no_privilege(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(CLEAN, pilot["drone_id"], category="a2")

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"A category without the privilege must be rejected: {r.text}"

    error = _only_error(r)
    assert error["type"] == "checkin.no_privilege", f"Wrong reason: {r.text}"
    assert error["loc"] == ["body", "category"], f"Should point to category: {r.text}"


def test_foreign_drone(
    client: Client, pilot: PilotInfo, other_pilot: PilotInfo, get_endpoint_link: EndpointCreator
):
    plan = functional.checkin_plan(CLEAN, other_pilot["drone_id"])

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"A drone of another pilot must be rejected: {r.text}"

    error = _only_error(r)
    assert error["type"] == "checkin.drone_not_found", f"Wrong reason: {r.text}"
    assert error["loc"] == ["body", "drone_id"], f"Should point to drone_id: {r.text}"


def test_missing_mission(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(
        CLEAN, pilot["drone_id"], mission_id=2**62, category=None, height=None, range=None, duration=None
    )

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"A mission the pilot does not have must be rejected: {r.text}"

    error = _only_error(r)
    assert error["type"] == "checkin.mission_not_found", f"Wrong reason: {r.text}"
    assert error["loc"] == ["body", "mission_id"], f"Should point to mission_id: {r.text}"


def test_errors_are_collected(
    client: Client, pilot: PilotInfo, other_pilot: PilotInfo, get_endpoint_link: EndpointCreator
):
    plan = functional.checkin_plan(CLEAN, other_pilot["drone_id"], category="a2")

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"Broken rules must be rejected: {r.text}"
    assert functional.error_types(r) == {"checkin.drone_not_found", "checkin.no_privilege"}, \
        f"All broken rules should come in one response: {r.text}"


@pytest.mark.parametrize("overrides", [
    pytest.param({"mission_id": 1}, id="mission-with-properties"),
    pytest.param({"category": None, "height": None, "range": None, "duration": None}, id="no-mission-no-properties"),
    pytest.param({"height": None}, id="incomplete-properties"),
    pytest.param({"category": "sts01"}, id="sts-without-mission"),
    pytest.param({"height": 200}, id="height-out-of-range"),
    pytest.param({"country_tag": "XX"}, id="unknown-country-code"),
])
def test_invalid_request(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator, overrides: dict):
    plan = functional.checkin_plan(CLEAN, pilot["drone_id"], **overrides)

    r = checkin_preview(client, pilot, get_endpoint_link, plan)
    assert r.status_code == 422, f"Invalid request must be rejected: {r.text}"
    assert not any(t.startswith("checkin.") for t in functional.error_types(r)), \
        f"Request validation should fail before the business rules: {r.text}"


def test_preview_without_token_rejected(client: Client, pilot: PilotInfo, get_endpoint_link: EndpointCreator):
    plan = functional.checkin_plan(CLEAN, pilot["drone_id"])

    r = client.post(get_endpoint_link("live", "check-in/preview"), json=plan)
    assert r.status_code in (401, 403), f"Preview without a token should be rejected: {r.text}"
