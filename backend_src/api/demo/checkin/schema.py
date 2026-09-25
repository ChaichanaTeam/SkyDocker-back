from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend_src.models import FlyingPrivileges


class CheckinInput(BaseModel):
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)

    flying_privilege: FlyingPrivileges = FlyingPrivileges.A1
    description: Optional[str] = None

    height: int = Field(gt=0, description="meters")
    range: int = Field(gt=0, description="meters")
    time: int = Field(gt=0, description="seconds, declared flight duration - ends_at is starts_at + time")

    starts_at: Optional[datetime] = Field(default=None, description="defaults to now")