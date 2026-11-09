from concurrent.futures import ThreadPoolExecutor

import pytest
from httpx import Client

from tests import constants
from tests.types import EndpointCreator, UserInfo
from tests.utils.behavioural.worker_behaviour import border_sync, health


def test_concurrent_syncs_do_not_overlap(get_endpoint_link: EndpointCreator, borders_env: UserInfo):
    if not constants.ADMIN_API_KEY:
        pytest.skip("Sync lock tests need ADMIN_API_KEY")

    def sync_border(_: int) -> int:
        # a client per thread, the requests must really run at the same time
        with Client() as client:
            return border_sync(client, get_endpoint_link, constants.ADMIN_API_KEY, "PL").status_code # type: ignore[arg-type]

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(sync_border, range(2)))

    assert codes == [200, 409], f"One border sync must run and the other must not start while it runs: {codes}"

    with Client() as client:
        run = health(client, get_endpoint_link).json()["syncs"].get("border:PL")
    assert run is not None and run["status"] == "ok", f"The finished admin run must be the last one: {run}"
    assert run["trigger"] == "admin", f"The run was started by the admin endpoint: {run}"
