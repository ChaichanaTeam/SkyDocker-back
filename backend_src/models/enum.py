from enum import Enum, StrEnum


class GeoZoneType(StrEnum):
    UNKNOWN = "unknown"
    gzt1 = "gzt1"
    gzt2 = "gzt2"
    gzt3 = "gzt3"
    restricted = "restricted"
    prohibited = "prohibited"
    danger = "danger"
    warning = "warning"
    req_authorisation = "req_authorisation"


class UserActivity(StrEnum):
    UNKNOWN = "unknown"


class FlyingPrivileges(StrEnum):
    UNKNOWN = "unknown"
    a1 = 'a1'
    a2 = 'a2'
    a3 = 'a3'
    sts01 = 'sts01'
    sts02 = 'sts02'


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
    recreational = 'recreational'
    photography = 'photography'
    inspection = 'inspection'
    commercial = 'commercial'
    survey = 'survey'


class MissionStatus(StrEnum):
    UNKNOWN = "unknown"
    created = "created"
    cancelled = "cancelled"
    pending = "pending"
    accepted = "accepted"
    active = "active"
    late = "late"
    loss_of_control = "loss_of_control"
    ended_intime = "ended_intime"
    late_end = "late_end"

class AtcDecision(StrEnum):
    UNKNOWN = "unknown"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"