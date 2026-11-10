from typing import Optional

from backend_src.models import Drone, DroneCategory


# Heaviest drone of the open and specific categories, a certified drone is out of scope
MAX_TAKE_OFF_MASS_G = 25_000

# EU class marks and the take-off mass each allows, the drone must weigh less;
# a privately built drone (pb) and the remaining classes are not limited by mass
CLASS_MASS_LIMITS_G: dict[DroneCategory, int] = {
    DroneCategory.C0: 250,
    DroneCategory.C1: 900,
    DroneCategory.C2: 4_000,
    DroneCategory.C3: 25_000,
    DroneCategory.C4: 25_000,
}


def take_off_mass(drone: Drone) -> int:
    """Mass the rules see: the modified drone's own one, otherwise its model's."""
    return drone.mtom_override if drone.mtom_override is not None else drone.model.mtom


def class_mass_conflict(category: DroneCategory, mass_g: int) -> Optional[str]:
    """Why the class mark does not fit the take-off mass, None when it does."""
    limit = CLASS_MASS_LIMITS_G.get(category)
    if limit is None or mass_g < limit:
        return None

    return f"Class {category.value} needs a take-off mass below {limit} g, the drone has {mass_g} g"
