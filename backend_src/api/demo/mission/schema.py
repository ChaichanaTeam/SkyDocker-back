from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_src.api.shared_schemas import FeatureProperties
from backend_src.models.enum import (
    FlyingPrivileges,
    OperationalCategory,
    MissionFlightGoal,
    MissionStatus,
)
from backend_src.models.model import Mission


class MissionProperties(FeatureProperties):
    id: int
    category: OperationalCategory
    flight_goal: Optional[MissionFlightGoal]
    flying_privilege: FlyingPrivileges
    status: MissionStatus
    height: int
    range: int
    starts_at: datetime
    ends_at: datetime
    time: int
    pilot_id: int
    drone_id: int
    country_id: int

    @classmethod
    def from_mission(cls, mission: Mission) -> MissionProperties:
        return cls(
            id=mission.id,
            category=mission.category,
            flight_goal=mission.flight_goal,
            flying_privilege=mission.flying_privilege,
            status=mission.status,
            height=mission.height,
            range=mission.range,
            starts_at=mission.starts_at,
            ends_at=mission.ends_at,
            time=mission.time,
            pilot_id=mission.pilot_id,
            drone_id=mission.drone_id,
            country_id=mission.country_id,
        )
