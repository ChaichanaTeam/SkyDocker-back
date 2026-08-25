from __future__ import annotations
from datetime import datetime

from backend_src.models import MissionStatus
from backend_src.models.model import Checkin
from backend_src.api.shared_schemas import FeatureProperties, E164PhoneNumber


class CheckinProperties(FeatureProperties):
    country_id: int
    country: str
    status: MissionStatus
    contact: E164PhoneNumber
    range: int
    height: int
    start_at: datetime
    time: int


    @classmethod
    def from_checkin(cls, checkin: Checkin) -> CheckinProperties:
        return cls(
            country_id=checkin.country.id,
            country=checkin.country.name,
            status=checkin.status,
            contact=checkin.pilot.phone_number, # type: ignore
            range=checkin.range,
            height=checkin.height,
            start_at=checkin.starts_at,
            time=checkin.time,
        )