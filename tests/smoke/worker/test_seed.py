import asyncio
import json
from pathlib import Path

import pytest

from backend_src.seed import SeedError, load_moderators
from backend_src.worker import seed
from backend_src.worker.constants import EXIT_FAILED


SECRET = "s3cret-pa55word"


def _profile(**overrides) -> dict:
    return {"email": "moderator@example.com", "first_name": "Jan", "last_name": "Kowalski", "password": SECRET} | overrides


def _write(tmp_path: Path, moderators: list[dict]) -> Path:
    path = tmp_path / "moderators.json"
    path.write_text(json.dumps({"moderators": moderators}), encoding="utf-8")
    return path


def test_valid_file_loads(tmp_path: Path):
    profiles = load_moderators(_write(tmp_path, [_profile(), _profile(email="other@example.com")]))

    assert [profile.email for profile in profiles] == ["moderator@example.com", "other@example.com"]


def test_example_file_is_valid():
    profiles = load_moderators(Path("data/seed/moderators.example.json"))
    assert profiles, "The committed example must stay a valid seed file"


def test_missing_file_rejected(tmp_path: Path):
    with pytest.raises(SeedError, match="not found"):
        load_moderators(tmp_path / "missing.json")


def test_broken_json_rejected(tmp_path: Path):
    path = tmp_path / "moderators.json"
    path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(SeedError, match="not valid JSON"):
        load_moderators(path)


@pytest.mark.parametrize("profile", [
    _profile(password="short"),
    _profile(email="not-an-email"),
    _profile(first_name=""),
])
def test_invalid_profile_rejected_without_leaking_password(tmp_path: Path, profile: dict):
    with pytest.raises(SeedError) as error:
        load_moderators(_write(tmp_path, [profile]))

    assert profile["password"] not in str(error.value), "Seed errors must not print passwords"


def test_duplicate_email_ignoring_case_rejected(tmp_path: Path):
    path = _write(tmp_path, [_profile(), _profile(email="Moderator@Example.com")])

    with pytest.raises(SeedError, match="duplicate email"):
        load_moderators(path)


def test_run_seed_with_missing_file_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(seed, "setup_logging", lambda log_file: None)

    assert asyncio.run(seed.run_seed("moderators", str(tmp_path / "missing.json"))) == EXIT_FAILED
