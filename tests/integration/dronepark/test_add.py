import pytest
from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils import functional
from tests.utils.behavioural.dronepark_behaviour import (
    add_drone, custom_model, delete_drone, drone_body, own_drones, random_serial, remove_custom_drone,
)
from tests.utils.behavioural.registration_behaviour import registration_flow


def test_add_catalog_drone(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    air = drone_catalog["DJI Air 3"]
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(air["id"]))
    assert r.status_code == 201, f"Drone of the catalog was not added: {r.text}"

    drone = r.json()
    assert drone["model"]["id"] == air["id"], f"Drone must get the chosen model: {r.text}"
    assert drone["model"]["is_model_verified"], f"A catalog model is checked: {r.text}"

    listed = [d["id"] for d in own_drones(client, drone_owner, get_endpoint_link).json()]
    assert drone["id"] in listed, "The added drone must be in the drone park"
    delete_drone(client, drone_owner, get_endpoint_link, drone["id"])


def test_add_custom_drone(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    model = custom_model(mtom=480)
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=model))
    assert r.status_code == 201, f"Drone with its own model was not added: {r.text}"

    drone = r.json()
    remove_custom_drone(client, drone_owner, get_endpoint_link, drone)
    assert not drone["model"]["is_model_verified"], f"A typed-in model waits for a moderator: {r.text}"
    assert drone["model"]["category"] == "open", f"A typed-in model is in the open category: {r.text}"
    assert drone["model"]["mtom"] == 480, f"The typed-in values must be kept: {r.text}"


def test_custom_model_in_catalog(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    mini = drone_catalog["DJI Mini 4 Pro"]
    model = custom_model(manufacturer="dji", model_name=" mini-4 pro ", mtom=249)
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=model, category="c0"))
    assert r.status_code == 409, f"A catalog model typed in again must be refused: {r.text}"
    assert r.json()["detail"]["model_id"] == mini["id"], f"The catalog model to choose must be returned: {r.text}"


def test_serial_number_is_unique(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    air = drone_catalog["DJI Air 3"]
    serial = random_serial()
    first = add_drone(client, drone_owner, get_endpoint_link, drone_body(air["id"], serial_number=serial))
    assert first.status_code == 201, f"Drone was not added: {first.text}"

    # another pilot, other case and spaces around
    other = functional.create_user()
    assert registration_flow(client, other, get_endpoint_link), "Registration failed"
    r = add_drone(client, other, get_endpoint_link, drone_body(air["id"], serial_number=f"  {serial.lower()} "))
    assert r.status_code == 409, f"A serial number can be registered once in the whole system: {r.text}"

    delete_drone(client, drone_owner, get_endpoint_link, first.json()["id"])
    r = add_drone(client, other, get_endpoint_link, drone_body(air["id"], serial_number=serial))
    assert r.status_code == 201, f"The serial number of a deleted drone can be registered again: {r.text}"
    delete_drone(client, other, get_endpoint_link, r.json()["id"])


@pytest.mark.parametrize("overrides, mass", [
    pytest.param({"category": "c0"}, 720, id="c0-catalog-mass"),
    pytest.param({"category": "c1", "is_drone_modified": True, "mtom_override": 900}, 900, id="c1-modified-mass"),
])
def test_class_must_fit_mass(
    client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator, overrides: dict, mass: int
):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(drone_catalog["DJI Air 3"]["id"], **overrides))
    assert r.status_code == 422, f"A class that does not fit {mass} g must be refused: {r.text}"
    assert functional.error_types(r) == {"drone.class_mass_mismatch"}, f"Wrong error for the class: {r.text}"


@pytest.mark.parametrize("overrides", [
    pytest.param({"is_drone_modified": True}, id="modified-without-mass"),
    pytest.param({"mtom_override": 700}, id="mass-without-modified"),
    pytest.param({"custom_model": custom_model()}, id="model-id-and-custom-model"),
    pytest.param({"category": "unknown"}, id="unknown-class"),
    pytest.param({"serial_number": "   "}, id="blank-serial-number"),
    pytest.param({"is_drone_modified": True, "mtom_override": 30_000, "category": "pb"}, id="mass-over-25-kg"),
])
def test_invalid_request(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator, overrides: dict):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(drone_catalog["DJI Air 3"]["id"], **overrides))
    assert r.status_code == 422, f"Invalid drone must be refused: {r.text}"
    assert not any(t.startswith("drone.") for t in functional.error_types(r)), f"Validation must fail first: {r.text}"


def test_custom_model_needs_every_value(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    model = custom_model()
    del model["max_range"]
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(custom_model=model))
    assert r.status_code == 422, f"A typed-in model needs every value of its specification: {r.text}"


def test_unknown_catalog_model(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body(2**31 - 1))
    assert r.status_code == 404, f"A model outside the catalog cannot be chosen: {r.text}"


def test_without_token(client: Client, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = client.post(get_endpoint_link("live", "pilots/me/drones"), json=drone_body(drone_catalog["DJI Air 3"]["id"]))
    assert r.status_code == 401, f"Adding a drone needs an access token: {r.text}"
