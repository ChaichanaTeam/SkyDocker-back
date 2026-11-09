import pytest

from backend_src.worker import config
from backend_src.worker.scheduler import cron, every


def test_unset_cron_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SYNC_TEST_CRON", raising=False)
    assert config._cron("SYNC_TEST_CRON", "0 3 * * *") == "0 3 * * *", "An unset cron must use the default schedule"


def test_empty_cron_disables_job(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SYNC_TEST_CRON", "")
    assert config._cron("SYNC_TEST_CRON", "0 3 * * *") is None, "An empty cron must disable the job"
    assert cron(None) is None, "A disabled cron job must get no trigger"


@pytest.mark.parametrize("value, minutes", [("", 0), ("0", 0), ("15", 15)])
def test_interval_minutes(monkeypatch: pytest.MonkeyPatch, value: str, minutes: int):
    monkeypatch.setenv("SYNC_TEST_MINUTES", value)
    assert config._minutes("SYNC_TEST_MINUTES", 360) == minutes, f"{value!r} must give {minutes} minutes"


def test_zero_interval_disables_job():
    assert every(0) is None, "A job every 0 minutes must be disabled"
    assert every(360) is not None, "A job with an interval must get a trigger"


def test_unset_interval_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SYNC_TEST_MINUTES", raising=False)
    assert config._minutes("SYNC_TEST_MINUTES", 360) == 360, "An unset interval must use the default"


@pytest.mark.parametrize("value, delays", [("5,15,45", [5, 15, 45]), (" 15 ", [15]), ("", [])])
def test_retry_delays(monkeypatch: pytest.MonkeyPatch, value: str, delays: list[int]):
    monkeypatch.setenv("SYNC_TEST_DELAYS", value)
    assert config._delays("SYNC_TEST_DELAYS", "5,15,45") == delays, f"{value!r} must give the delays {delays}"
