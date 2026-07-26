from sqlalchemy import (
    FetchedValue, Integer, SMALLINT, INTEGER, BIGINT, VARCHAR, DateTime, func, Boolean, ForeignKey, TEXT
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from geoalchemy2.types import Geometry
from shapely.geometry import Polygon, Point

from backend_src.db.base import Base
from backend_src.db.types import EnumWithUnknown, H3Index
from .enum import (
    ModelManufacturer,
    GeoZoneType,
    UserActivity, FlyingPrivileges,
    VerificationRequestStatus, VerificationDocumentType,
    MissionCategory, MissionFlightGoal, MissionStatus, AtcDecision
)


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(SMALLINT, primary_key = True)

    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    country_tag: Mapped[str] = mapped_column(VARCHAR(2), nullable=False)


class Model(Base):
    __tablename__ = "model"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True, autoincrement=True)

    manufacturer: Mapped[ModelManufacturer] = mapped_column(
        EnumWithUnknown(
            ModelManufacturer,
            name="model_manufacturer",
            unknown_value=ModelManufacturer.UNKNOWN
        )
    )

    model_name: Mapped[str]     = mapped_column(VARCHAR(255), nullable=False)

    speed: Mapped[int]          = mapped_column(Integer, nullable=False)
    weight: Mapped[int]         = mapped_column(Integer, nullable=False)
    max_height: Mapped[int]     = mapped_column(Integer, nullable=False)
    max_range: Mapped[int]      = mapped_column(Integer, nullable=False)


class VerificationAdmin(Base):
    __tablename__ = "verification_admin"

    id: Mapped[int]                     = mapped_column(primary_key=True)

    first_name: Mapped[str]             = mapped_column(VARCHAR(255), nullable=False)
    last_name: Mapped[str]              = mapped_column(VARCHAR(255), nullable=False)
    email: Mapped[str]                  = mapped_column(VARCHAR(255), nullable=False)
    password_hash: Mapped[str]          = mapped_column(VARCHAR(255), nullable=False)

    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AtcAdmin(Base):
    __tablename__ = "atc_admin"

    id: Mapped[int]                             = mapped_column(primary_key=True)
    country_id: Mapped[int]                     = mapped_column(SMALLINT, ForeignKey("country.id"))

    email: Mapped[str]                          = mapped_column(VARCHAR(255), nullable=False)
    affiliation: Mapped[str]                    = mapped_column(VARCHAR(4), nullable=False)
    api_key: Mapped[str]                        = mapped_column(VARCHAR(255), nullable=False)

    is_revoked: Mapped[bool]                    = mapped_column(Boolean, default=False, nullable=False)
    revoke_reason: Mapped[Optional[str]]        = mapped_column(TEXT)
    expires_at: Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]]      = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime]                = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GeoZone(Base):
    __tablename__ = "geo_zone"

    id: Mapped[int]                                             = mapped_column(BIGINT, primary_key=True)
    country_id: Mapped[int]                                     = mapped_column(SMALLINT, ForeignKey("country.id"), nullable=False)
        
    type: Mapped[GeoZoneType]                                   = mapped_column(
            EnumWithUnknown(
                GeoZoneType,
                name="geo_zone_type",
                unknown_value=GeoZoneType.UNKNOWN
            ),
            nullable=False
        )
    tag: Mapped[str]                                            = mapped_column(VARCHAR(255), nullable=False)
    strength: Mapped[int]                                       = mapped_column(Integer, nullable=False)
    zone_polygon: Mapped[Polygon]                               = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    height_agl: Mapped[Optional[int]]                           = mapped_column(Integer)
    height_amsl: Mapped[Optional[int]]                          = mapped_column(Integer)


class GeoZoneH3(Base):
    __tablename__ = "geo_zone_h3"

    id: Mapped[int]             = mapped_column(BIGINT, primary_key=True)

    geo_zone_id: Mapped[int]    = mapped_column(BIGINT, ForeignKey("geo_zone.id"))
    h3_index: Mapped[str]       = mapped_column(H3Index)


class ActivityTime(Base):
    __tablename__ = "activity_time"

    id: Mapped[int]                 = mapped_column(BIGINT, primary_key=True)
    geo_zone_id: Mapped[int]        = mapped_column(BIGINT, ForeignKey("geo_zone.id"))

    start_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime]       = mapped_column(DateTime(timezone=True))


class Pilot(Base):
    __tablename__ = "pilot"

    id: Mapped[int]                                             = mapped_column(BIGINT, primary_key=True)

    first_name: Mapped[str]                                     = mapped_column(VARCHAR(255))
    last_name: Mapped[str]                                      = mapped_column(VARCHAR(255))

    email: Mapped[str]                                          = mapped_column(VARCHAR(255))
    phone_number: Mapped[str]                                   = mapped_column(VARCHAR(15))
    pilot_number: Mapped[Optional[str]]                         = mapped_column(VARCHAR(255))

    password_hash: Mapped[str]                                  = mapped_column(VARCHAR(255))
    verification_code_hash: Mapped[Optional[str]]               = mapped_column(VARCHAR(255))
    verification_code_created_at: Mapped[Optional[datetime]]    = mapped_column(DateTime(timezone=True))

    country_id: Mapped[int]                                     = mapped_column(SMALLINT, ForeignKey("country.id"))
    show_to_public: Mapped[bool]                                = mapped_column(Boolean, server_default="false")
    activity: Mapped[Optional[UserActivity]]                    = mapped_column(
        EnumWithUnknown(
            UserActivity,
            name="user_activity",
            unknown_value=UserActivity.UNKNOWN
        )
    )
    flight_time: Mapped[int]                                    = mapped_column(INTEGER, server_default=FetchedValue())
    dronepark_hash: Mapped[Optional[str]]                       = mapped_column(VARCHAR(255))

    verified: Mapped[bool]                                      = mapped_column(Boolean, server_default="false")

    created_at: Mapped[datetime]                                = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Drone(Base):
    __tablename__ = "drone"

    id: Mapped[int]             = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]       = mapped_column(BIGINT, ForeignKey("pilot.id"))

    model_id: Mapped[int]       = mapped_column(INTEGER, ForeignKey("model.id"))
    serial_number: Mapped[str]  = mapped_column(VARCHAR(255))


class GeoZoneToAtc(Base):
    __tablename__ = "geo_zone_to_atc"

    id: Mapped[int]                 = mapped_column(BIGINT, primary_key=True)

    geo_zone_id: Mapped[int]        = mapped_column(BIGINT, ForeignKey("geo_zone.id"))
    atc_admin_id: Mapped[int]       = mapped_column(INTEGER, ForeignKey("atc_admin.id"))


class UserToFlyingPrivileges(Base):
    __tablename__ = "user_to_flying_privileges"

    id: Mapped[int]                                 = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    pilot_id: Mapped[int]                           = mapped_column(BIGINT, ForeignKey("pilot.id"))
    flying_privilege: Mapped[FlyingPrivileges]      = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN
        )
    )


class VerificationRequest(Base):
    __tablename__ = "verification_request"

    id: Mapped[int]                                                             = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                                                       = mapped_column(BIGINT, ForeignKey("pilot.id"))

    status: Mapped[VerificationRequestStatus]                                   = mapped_column(
        EnumWithUnknown(
            VerificationRequestStatus,
            name="verification_request_status",
            unknown_value=VerificationRequestStatus.UNKNOWN
        ),
        server_default="pending"
    )
    reason: Mapped[Optional[str]]                                                = mapped_column(TEXT)
    verified_by: Mapped[Optional[int]]                                           = mapped_column(INTEGER, ForeignKey("verification_admin.id)"))
    verified_at: Mapped[Optional[datetime]]                                      = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime]                                                 = mapped_column(DateTime(timezone=True))


class VerificationDocument(Base):
    __tablename__ = "verification_document"

    id: Mapped[int]                                                         = mapped_column(BIGINT, primary_key=True)
    requset_id: Mapped[int]                                                 = mapped_column(BIGINT, ForeignKey("verification_request.id"))

    document_path: Mapped[str]                                              = mapped_column(VARCHAR(255))
    document_type: Mapped[VerificationDocumentType]                         = mapped_column(
        EnumWithUnknown(
            VerificationDocumentType,
            name="verification_document_type",
            unknown_value=VerificationDocumentType.UNKNOWN
        )
    )

    created_at: Mapped[datetime]                                            = mapped_column(DateTime(timezone=True))


class Mission(Base):
    __tablename__ = "mission"

    id: Mapped[int]                                         = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                                   = mapped_column(BIGINT, ForeignKey("pilot.id"))
        
    drone_id: Mapped[int]                                   = mapped_column(BIGINT, ForeignKey("drone.id"))
    category: Mapped[MissionCategory] = mapped_column(
        EnumWithUnknown(
                MissionCategory,
                unknown_value=MissionCategory.UNKNOWN
        ),
        nullable=False
    )
    flight_goal: Mapped[Optional[MissionFlightGoal]]        = mapped_column(
        EnumWithUnknown(
            MissionFlightGoal,
            name="mission_fligh_goal",
            unknown_value=MissionFlightGoal.UNKNOWN
        )
    )
    description: Mapped[Optional[str]]                      = mapped_column(TEXT)
    flying_privilege: Mapped[FlyingPrivileges]              = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN
        )
    )

    h3_index: Mapped[str]                                   = mapped_column(H3Index, nullable=False)
    country_id: Mapped[int]                                 = mapped_column(SMALLINT, ForeignKey("country.id"), nullable=False)
    home_point: Mapped[Point]                               = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    height: Mapped[int]                                     = mapped_column(INTEGER, nullable=False)
    range: Mapped[int]                                      = mapped_column(INTEGER, nullable=False)
    starts_at: Mapped[datetime]                             = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime]                               = mapped_column(DateTime(timezone=True), nullable=False)
    time: Mapped[int]                                       = mapped_column(INTEGER, nullable=False)

    spotter_first_name: Mapped[Optional[str]]               = mapped_column(VARCHAR(255))   
    spotter_last_name: Mapped[Optional[str]]                = mapped_column(VARCHAR(255))   
    spotter_phone: Mapped[Optional[str]]                    = mapped_column(VARCHAR(15))

    status: Mapped[MissionStatus]                           = mapped_column(
        EnumWithUnknown(
            MissionStatus,
            name="mission_status",
            unknown_value=MissionStatus.UNKNOWN
        ),
        server_default=FetchedValue()
    )

    created_at: Mapped[datetime]                            = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Checkin(Base):
    __tablename__ = "checkin"

    id: Mapped[int]                             = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                       = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)
    mission_id: Mapped[Optional[int]]           = mapped_column(BIGINT, ForeignKey("mission.id"))

    flying_privilege: Mapped[FlyingPrivileges] = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN
        ),
        nullable=False
    )
    flight_goal: Mapped[Optional[MissionFlightGoal]] = mapped_column(
        EnumWithUnknown(
            MissionFlightGoal,
            name="mission_flight_goal",
            unknown_value=MissionFlightGoal.UNKNOWN
        )
    )
    description: Mapped[Optional[str]]          = mapped_column(TEXT)

    home_point: Mapped[Point]                   = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    h3_index: Mapped[str]                       = mapped_column(H3Index, nullable=False)
    country_id: Mapped[int]                     = mapped_column(SMALLINT, ForeignKey("country.id"), nullable=False)
    height: Mapped[int]                         = mapped_column(INTEGER, nullable=False)
    range: Mapped[int]                          = mapped_column(INTEGER, nullable=False)
    starts_at: Mapped[datetime]                 = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime]                   = mapped_column(DateTime(timezone=True), nullable=False)
    time: Mapped[int]                           = mapped_column(INTEGER, nullable=False)

    status: Mapped[MissionStatus]               = mapped_column(
        EnumWithUnknown(
           MissionStatus,
           name="mission_status",
           unknown_value=MissionStatus.UNKNOWN
        ),
        server_default=FetchedValue()
    )

    created_at: Mapped[datetime]                = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MissionAtcApproval(Base):
    __tablename__ = "mission_atc_approval"

    id: Mapped[int]                             = mapped_column(BIGINT, primary_key=True)
    
    mission_id: Mapped[int]                     = mapped_column(BIGINT, ForeignKey("mission.id"), nullable=False)
    atc_admin_id: Mapped[int]                   = mapped_column(INTEGER, ForeignKey("atc_admin.id"), nullable=False)

    status: Mapped[AtcDecision]               = mapped_column(
        EnumWithUnknown(
           AtcDecision,
           name="atc_decision",
           unknown_value=AtcDecision.UNKNOWN
        ),
        server_default="pending"
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())