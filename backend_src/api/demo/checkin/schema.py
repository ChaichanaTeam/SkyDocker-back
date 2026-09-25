from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from backend_src.models import FlyingPrivileges

class CheckinInput(BaseModel):
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)

    flying_privilege: FlyingPrivileges = FlyingPrivileges.A1
    description: Optional[str] = None

    height: int = Field(gt=0, description="meters")
    range: int = Field(gt=0, description="meters")
    time: int = Field(ge=0, description="seconds, added to pilot.flight_time by a trigger")

    starts_at: Optional[datetime] = Field(default=None, description="defaults to now")
    ends_at: Optional[datetime] = Field(default=None, description="defaults to starts_at + 1h")

    @model_validator(mode="after")
    def _check_window(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self