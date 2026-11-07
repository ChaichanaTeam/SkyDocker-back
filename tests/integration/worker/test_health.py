from httpx import Client

from tests.types import EndpointCreator
from tests.utils.behavioural.worker_behaviour import health


RUN_STATUSES = {"running", "ok", "skipped", "retrying", "failed"}
TRIGGERS = {"schedule", "retry", "startup", "admin", "cli"}


def test_health_shows_worker(client: Client, get_endpoint_link: EndpointCreator):
    r = health(client, get_endpoint_link)
    assert r.status_code == 200, f"The server must be healthy: {r.text}"

    body = r.json()
    assert body.get("worker") in ("up", "down"), f"Health must tell whether the sync worker runs: {r.text}"
    assert isinstance(body.get("syncs"), dict), f"Health must list the last sync runs: {r.text}"


def test_sync_runs_are_public_safe(client: Client, get_endpoint_link: EndpointCreator):
    r = health(client, get_endpoint_link)

    for job, run in r.json()["syncs"].items():
        assert run["status"] in RUN_STATUSES, f"Unknown status of the {job} sync: {run}"
        assert run["trigger"] in TRIGGERS, f"Unknown trigger of the {job} sync: {run}"
        assert "started_at" in run, f"The {job} run must have its start time: {run}"
        assert "summary" not in run, f"Error details of the {job} sync must stay in the logs: {run}"
