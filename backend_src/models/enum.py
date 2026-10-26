from enum import StrEnum


class GeoZoneType(StrEnum):
    UNKNOWN = "unknown"
    DRA_P = 'dra_p'
    DRA_RH = 'dra_rh'
    DRA_RM = 'dra_rm'
    DRA_RL = 'dra_rl'
    DRA_T = 'dra_t'
    DRA_U = 'dra_u'
    DRA_I = 'dra_i'


class UserActivity(StrEnum):
    UNKNOWN = "unknown"
    UA1 = 'ua1'
    UA2 = 'ua2'
    UA3 = 'ua3'


class DroneCategory(StrEnum):
    UNKNOWN = "unknown"
    PB = 'pb'
    C0 = 'c0'
    C1 = 'c1'
    C2 = 'c2'
    C3 = 'c3'
    C4 = 'c4'
    C5 = 'c5'
    C6 = 'c6'


class FlyingPrivileges(StrEnum):
    UNKNOWN = "unknown"
    A1 = 'a1'
    A2 = 'a2'
    A3 = 'a3'
    STS01 = 'sts01'
    STS02 = 'sts02'


class VerificationDocumentType(StrEnum):
    UNKNOWN = "unknown"
    PRIVILEGE_A1 = 'privilege_a1'
    PRIVILEGE_A2 = 'privilege_a2'
    PRIVILEGE_A3 = 'privilege_a3'
    PRIVILEGE_STS01 = 'privilege_sts01'
    PRIVILEGE_STS02 = 'privilege_sts02'
    OPERATOR_NUMBER = 'operator_number'


class VerificationRequestStatus(StrEnum):
    UNKNOWN = "unknown"
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'


class OperationalCategory(StrEnum):
    UNKNOWN = "unknown"
    OPEN = 'open'
    SPECIFIC = 'specific'
    CERTIFIED = 'certified'


class MissionFlightGoal(StrEnum):
    UNKNOWN = "unknown"
    RECREATIONAL = 'recreational'
    PHOTOGRAPHY = 'photography'
    INSPECTION = 'inspection'
    COMMERCIAL = 'commercial'
    SURVEY = 'survey'
    COMMON = 'common'


class MissionStatus(StrEnum):
    UNKNOWN = "unknown"
    CREATED = 'created'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    ACTIVE = 'active'
    LATE = 'late'
    LOSS_OF_CONTROL = 'loss_of_control'
    ENDED_INTIME = 'ended_intime'
    LATE_END = 'late_end'