import pytest

from backend_src.dronepark import class_mass_conflict, model_key
from backend_src.models import DroneCategory


@pytest.mark.parametrize("category, mass_g, fits", [
    (DroneCategory.C0, 249, True),
    (DroneCategory.C0, 250, False),
    (DroneCategory.C1, 899, True),
    (DroneCategory.C1, 900, False),
    (DroneCategory.C2, 3_999, True),
    (DroneCategory.C2, 4_000, False),
    (DroneCategory.C3, 24_999, True),
    (DroneCategory.C4, 25_000, False),
    (DroneCategory.PB, 25_000, True),
    (DroneCategory.C5, 25_000, True),
])
def test_class_mass_limits(category: DroneCategory, mass_g: int, fits: bool):
    conflict = class_mass_conflict(category, mass_g)
    assert (conflict is None) == fits, f"{category.value} at {mass_g} g: {conflict}"


@pytest.mark.parametrize("typed", [("dji", "mini-4 pro"), ("DJI", "Mini 4 Pro"), (" D J I ", "mini_4_pro")])
def test_model_names_match_loosely(typed: tuple[str, str]):
    assert model_key(*typed) == model_key("DJI", "Mini 4 Pro"), f"{typed} must match DJI Mini 4 Pro"


def test_different_models_do_not_match():
    assert model_key("DJl", "Air 3") != model_key("DJI", "Air 3"), "A misspelled manufacturer is another model"
    assert model_key("DJI", "Mini 4") != model_key("DJI", "Mini 4 Pro"), "Another model of the manufacturer must not match"
