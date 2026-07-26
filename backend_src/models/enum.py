from enum import Enum, StrEnum


class GeoZoneType(StrEnum):
    UNKNOWN = "unknown"


class UserActivity(StrEnum):
    UNKNOWN = "unknown"


class FlyingPrivileges(StrEnum):
    UNKNOWN = "unknown"


class VerificationRequestStatus(StrEnum):
    UNKNOWN = "unknown"
    pending = "pending"


class VerificationDocumentType(StrEnum):
    UNKNOWN = "unknown"


# class MissionOperationType(StrEnum):
#    UNKNOWN = "unknown"   


class MissionCategory(StrEnum):
    UNKNOWN = "unknown"
    open    = "open"
    specific = "specific"
    certified = "certified"


class MissionFlightGoal(StrEnum):
    UNKNOWN = "unknown"


class MissionStatus(StrEnum):
    UNKNOWN = "unknown"
    created = 'created'
    pending = 'pending'
    accepted = 'accepted'
    active = 'active'
    late = 'late'
    loss_of_control = 'loss_of_control'
    ended_intime = 'ended_intime'
    late_end = 'late_end'