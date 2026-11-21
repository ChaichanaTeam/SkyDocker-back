from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend_src.api.v1.pilot.schema import DroneModelRead
from backend_src.dronepark import MAX_TAKE_OFF_MASS_G
from backend_src.models import Drone, DroneCategory, OperationalCategory


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


class ModelCorrection(BaseModel):
    """Values the moderator fixes before the model goes into the catalog, the rest is kept."""

    model_config = ConfigDict(str_strip_whitespace=True)

    manufacturer: Optional[str] = Field(None, min_length=1, max_length=255)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[OperationalCategory] = None
    speed: Optional[int] = Field(None, gt=0, description="Metres per second")
    mtom: Optional[int] = Field(None, ge=1, le=MAX_TAKE_OFF_MASS_G, description="Maximum take-off mass in grams")
    max_height: Optional[int] = Field(None, gt=0, description="Metres")
    max_range: Optional[int] = Field(None, gt=0, description="Metres")

    @field_validator("category")
    @classmethod
    def validate_category(cls, category: Optional[OperationalCategory]) -> Optional[OperationalCategory]:
        if category is OperationalCategory.UNKNOWN:
            raise ValueError("Unknown operational category")
        return category


class ModelReplacement(BaseModel):
    model_id: int = Field(ge=1, description="Catalog model that takes the place of the typed-in one")


class ClassConflict(BaseModel):
    """Drone whose class mark no longer fits its take-off mass after the model changed."""

    drone_id: int
    pilot_email: str
    category: DroneCategory
    mass_g: int
    msg: str


class ModelReview(BaseModel):
    model: DroneModelRead = Field(description="The catalog model the drones use now")
    class_conflicts: list[ClassConflict] = Field(description="Drones to fix by hand, empty when every class still fits")
