from httpx import Client, Response

from tests.types import EndpointCreator


# A border sync downloads the outline from GADM, slower than the default client timeout
SYNC_TIMEOUT_SECONDS = 60


def health(client: Client, get_endpoint_link: EndpointCreator) -> Response:
    r = client.get(get_endpoint_link("live", "health"))

    return r


def border_sync(client: Client, get_endpoint_link: EndpointCreator, admin_key: str, country_tag: str) -> Response:
    request = {
        "url": get_endpoint_link("live", "geo-zone/border/sync"),
        "headers": {"X-Admin-Key": admin_key},
        "params": {"country_tag": country_tag},
        "timeout": SYNC_TIMEOUT_SECONDS,
    }
    r = client.post(**request)

    return r
