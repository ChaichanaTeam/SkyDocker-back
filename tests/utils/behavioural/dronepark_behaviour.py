import uuid
from typing import Any, Optional
from httpx import Response, Client

from tests.types import UserInfo, EndpointCreator


def _auth(user: Optional[UserInfo]) -> dict[str, str]:
    if user is None:
        return {}

    return {"Authorization": f"{user['tokens']['type']} {user['tokens']['access_token']}"}


def random_serial() -> str:
    return f"TEST-{uuid.uuid4().hex[:12].upper()}"


def custom_model(**overrides) -> dict[str, Any]:
    """A model that is surely not in the catalog, values as from a specification sheet."""
    model: dict[str, Any] = {
        "manufacturer": "Test Aero",
        "model_name": f"Probe {uuid.uuid4().hex[:8]}",
        "speed": 12,
        "mtom": 600,
        "max_height": 500,
        "max_range": 2000,
    }
    model.update(overrides)

    return model


def drone_body(model_id: Optional[int] = None, **overrides) -> dict[str, Any]:
    """Body of an unmodified c1 drone; without model_id the drone gets a custom model."""
    body: dict[str, Any] = {"serial_number": random_serial(), "category": "c1"}
    if model_id is not None:
        body["model_id"] = model_id
    else:
        body["custom_model"] = custom_model()
    body.update(overrides)

    return body


def drone_models(client: Client, user: Optional[UserInfo], get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("live", "drone-models/"), headers=_auth(user))


def own_drones(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("live", "pilots/me/drones"), headers=_auth(user))


def own_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int) -> Response:
    return client.get(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user))


def add_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, body: dict[str, Any]) -> Response:
    return client.post(get_endpoint_link("live", "pilots/me/drones"), headers=_auth(user), json=body)


def update_drone(
    client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int, body: dict[str, Any]
) -> Response:
    return client.patch(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user), json=body)


def delete_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone_id: int) -> Response:
    return client.delete(get_endpoint_link("live", f"pilots/me/drones/{drone_id}"), headers=_auth(user))


def seed_models(client: Client, get_endpoint_link: EndpointCreator) -> Response:
    return client.post(get_endpoint_link("demo", "drone-park/models/seed"))


def unverified_models(client: Client, get_endpoint_link: EndpointCreator) -> Response:
    return client.get(get_endpoint_link("demo", "drone-models/unverified"))


def approve_model(
    client: Client, get_endpoint_link: EndpointCreator, model_id: int, correction: dict[str, Any]
) -> Response:
    return client.post(get_endpoint_link("demo", f"drone-models/{model_id}/approve"), json=correction)


def replace_model(client: Client, get_endpoint_link: EndpointCreator, model_id: int, by_model_id: int) -> Response:
    return client.post(get_endpoint_link("demo", f"drone-models/{model_id}/replace"), json={"model_id": by_model_id})


def delete_model(client: Client, get_endpoint_link: EndpointCreator, model_id: int) -> Response:
    return client.delete(get_endpoint_link("demo", f"drone-models/{model_id}"))


def remove_custom_drone(client: Client, user: UserInfo, get_endpoint_link: EndpointCreator, drone: dict[str, Any]) -> None:
    """Cleanup: deletes the drone and its typed-in model, so test models do not pile up."""
    delete_drone(client, user, get_endpoint_link, drone["id"])
    delete_model(client, get_endpoint_link, drone["model"]["id"])
