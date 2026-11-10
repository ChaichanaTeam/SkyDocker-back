from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend_src.api.v1.pilot.schema import DroneModelRead
from backend_src.models import Drone, DroneCategory


class ModelDroneRead(BaseModel):
    """Drone of a pilot that uses the model."""

    id: int
    serial_number: str
    category: DroneCategory
    is_drone_modified: bool
    mtom_override: Optional[int]
    pilot_id: int
    pilot_email: str

    @classmethod
    def from_drone(cls, drone: Drone) -> ModelDroneRead:
        return cls(
            id=drone.id,
            serial_number=drone.serial_number,
            category=drone.category,
            is_drone_modified=drone.is_drone_modified,
            mtom_override=drone.mtom_override,
            pilot_id=drone.pilot_id,
            pilot_email=drone.pilot.email,
        )


class UnverifiedModelRead(DroneModelRead):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    drones: list[ModelDroneRead] = Field(description="Drones in drone parks that use the model")
