import asyncio
from types import SimpleNamespace

import pytest
from fakeredis import FakeAsyncRedis
from fastapi import HTTPException

from backend_src.api.v1.dronemodel import service
from backend_src.api.v1.dronemodel.schema import ModelCorrection, ModelReplacement
from backend_src.cache import acquire_review_lock


@pytest.fixture
def no_moderator(monkeypatch: pytest.MonkeyPatch) -> None:
    async def missing(moderator_id, db):
        return None

    monkeypatch.setattr(service.Queries.Moderator, "get_by_id", missing)


@pytest.mark.parametrize("decide", [
    lambda redis: service.approve(7, ModelCorrection(), SimpleNamespace(id=1), None, redis),
    lambda redis: service.replace(7, ModelReplacement(model_id=3), SimpleNamespace(id=1), None, redis),
], ids=["approve", "replace"])
def test_model_decided_by_another(no_moderator: None, decide):
    async def scenario():
        redis = FakeAsyncRedis()
        await acquire_review_lock(redis, "drone_model", 7, 2, 60)
        with pytest.raises(HTTPException) as refused:
            await decide(redis)
        return refused.value

    refused = asyncio.run(scenario())
    assert refused.status_code == 409, "A model another moderator decides on must be refused"
    assert refused.detail["expires_in"] > 0, "The refusal must tell how long the other decision holds the model"


def test_lock_is_released_after_a_failed_decision(monkeypatch: pytest.MonkeyPatch):
    async def missing_model(model_id, db):
        return None

    monkeypatch.setattr(service.Queries.Model, "get_by_id", missing_model)

    async def scenario():
        redis = FakeAsyncRedis()
        with pytest.raises(HTTPException):
            await service.approve(7, ModelCorrection(), SimpleNamespace(id=1), None, redis)
        return await acquire_review_lock(redis, "drone_model", 7, 2, 60)

    assert asyncio.run(scenario()).taken, "A decision that failed must not keep the model from other moderators"
