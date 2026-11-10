from httpx import Client

from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.dronepark_behaviour import add_drone, drone_body, drone_models, remove_custom_drone


def test_catalog_is_sorted(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = drone_models(client, drone_owner, get_endpoint_link)
    assert r.status_code == 200, f"Catalog was not listed: {r.text}"

    models = r.json()
    assert all(model["is_model_verified"] for model in models), f"Catalog must hold only checked models: {r.text}"
    order = [(model["manufacturer"], model["model_name"]) for model in models]
    assert order == sorted(order), f"Catalog must be sorted by manufacturer and model: {order}"


def test_typed_in_model_is_not_listed(client: Client, drone_owner: UserInfo, drone_catalog: dict, get_endpoint_link: EndpointCreator):
    r = add_drone(client, drone_owner, get_endpoint_link, drone_body())
    assert r.status_code == 201, f"Drone with its own model was not added: {r.text}"
    drone = r.json()

    try:
        listed = {model["id"] for model in drone_models(client, drone_owner, get_endpoint_link).json()}
        assert drone["model"]["id"] not in listed, "A model a pilot typed in must not be in the catalog before a moderator checks it"
    finally:
        remove_custom_drone(client, drone_owner, get_endpoint_link, drone)


def test_without_token(client: Client, get_endpoint_link: EndpointCreator):
    r = drone_models(client, None, get_endpoint_link)
    assert r.status_code == 401, f"Catalog needs an access token: {r.text}"
