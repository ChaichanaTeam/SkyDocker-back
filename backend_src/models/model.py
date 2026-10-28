from sqlalchemy import (
    FetchedValue, Integer, SMALLINT, INTEGER, BIGINT, VARCHAR, DateTime, func, Boolean, ForeignKey, TEXT, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Raster, RasterElement
from datetime import datetime
from typing import Optional
from uuid import UUID
from shapely.geometry import Point, Polygon

from backend_src.db.base import Base
from backend_src.db.types import EnumWithUnknown, H3Index, GeometryType
from .enum import (
    GeoZoneType, GeoZoneActivityMode, GeoZoneActivitySource,
    UserActivity, FlyingPrivileges,
    VerificationRequestStatus, VerificationDocumentType,
    OperationalCategory, MissionFlightGoal, MissionStatus, DroneCategory
)


class Country(Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(SMALLINT, primary_key=True)

    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    country_tag: Mapped[str] = mapped_column(VARCHAR(2), nullable=False)


class Model(Base):
    __tablename__ = "model"

    id: Mapped[int]                         = mapped_column(Integer, primary_key=True, autoincrement=True)

    manufacturer: Mapped[str]               = mapped_column(VARCHAR(255), nullable=False)
    model_name: Mapped[str]                 = mapped_column(VARCHAR(255), nullable=False)
    category: Mapped[OperationalCategory]   = mapped_column(
        EnumWithUnknown(
            OperationalCategory,
            name="operational_category",
            unknown_value=OperationalCategory.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )

    is_model_verified: Mapped[bool]         = mapped_column(Boolean, server_default="false", nullable=False)
    created_at: Mapped[datetime]            = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    speed: Mapped[int]                      = mapped_column(Integer, nullable=False)
    mtom: Mapped[int]                       = mapped_column(Integer, nullable=False)
    max_height: Mapped[int]                 = mapped_column(Integer, nullable=False)
    max_range: Mapped[int]                  = mapped_column(Integer, nullable=False)


class AfdModerator(Base):
    __tablename__ = "afd_moderator"

    id: Mapped[int]                     = mapped_column(Integer, primary_key=True, autoincrement=True)

    first_name: Mapped[str]             = mapped_column(VARCHAR(255), nullable=False)
    last_name: Mapped[str]              = mapped_column(VARCHAR(255), nullable=False)
    email: Mapped[str]                  = mapped_column(VARCHAR(255), nullable=False)
    password_hash: Mapped[str]          = mapped_column(VARCHAR(255), nullable=False)

    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GeoZone(Base):
    __tablename__ = "geo_zone"

    id: Mapped[int]                                             = mapped_column(BIGINT, primary_key=True)
    country_id: Mapped[int]                                     = mapped_column(SMALLINT, ForeignKey("country.id"), nullable=False)
    parent_id: Mapped[Optional[int]]                            = mapped_column(BIGINT, ForeignKey("geo_zone.id", ondelete="SET NULL"))

    external_id: Mapped[UUID]                                   = mapped_column(Uuid, nullable=False)
    type: Mapped[GeoZoneType]                                   = mapped_column(
            EnumWithUnknown(
                GeoZoneType,
                name="geo_zone_type",
                unknown_value=GeoZoneType.UNKNOWN,
                values_callable=lambda enum_cls: [member.value for member in enum_cls]
            ),
            nullable=False
        )
    source_type: Mapped[str]                                    = mapped_column(VARCHAR(16), nullable=False)
    activity_mode: Mapped[GeoZoneActivityMode]                  = mapped_column(
            EnumWithUnknown(
                GeoZoneActivityMode,
                name="geo_zone_activity_mode",
                unknown_value=GeoZoneActivityMode.UNKNOWN,
                values_callable=lambda enum_cls: [member.value for member in enum_cls]
            ),
            nullable=False
        )
    tag: Mapped[str]                                            = mapped_column(VARCHAR(255), nullable=False)
    zone_polygon: Mapped[Polygon]                               = mapped_column(GeometryType("POLYGON", 4326), nullable=False)

    lower_limit_ft: Mapped[int]                                 = mapped_column(Integer, nullable=False)
    upper_limit_ft: Mapped[int]                                 = mapped_column(Integer, nullable=False)

    valid_from: Mapped[Optional[datetime]]                      = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]]                        = mapped_column(DateTime(timezone=True))

    description_pl: Mapped[Optional[str]]                       = mapped_column(TEXT)
    description_en: Mapped[Optional[str]]                       = mapped_column(TEXT)
    contact: Mapped[Optional[str]]                              = mapped_column(VARCHAR(255))

    source_modified_at: Mapped[datetime]                        = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime]                                = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    country: Mapped["Country"]                                  = relationship()
    activity_time: Mapped[list['ActivityTime']]                 = relationship(passive_deletes=True)


class GeoZoneH3(Base):
    __tablename__ = "geo_zone_h3"

    id: Mapped[int]             = mapped_column(BIGINT, primary_key=True)

    geo_zone_id: Mapped[int]    = mapped_column(BIGINT, ForeignKey("geo_zone.id", ondelete="CASCADE"), nullable=False)
    h3_index: Mapped[str]       = mapped_column(H3Index, nullable=False)


class ActivityTime(Base):
    __tablename__ = "activity_time"

    id: Mapped[int]                                 = mapped_column(BIGINT, primary_key=True)
    geo_zone_id: Mapped[int]                        = mapped_column(BIGINT, ForeignKey("geo_zone.id", ondelete="CASCADE"), nullable=False)

    source: Mapped[GeoZoneActivitySource]           = mapped_column(
            EnumWithUnknown(
                GeoZoneActivitySource,
                name="geo_zone_activity_source",
                unknown_value=GeoZoneActivitySource.UNKNOWN,
                values_callable=lambda enum_cls: [member.value for member in enum_cls]
            ),
            nullable=False
        )
    source_ref: Mapped[Optional[str]]               = mapped_column(VARCHAR(64))

    start_at: Mapped[datetime]                      = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime]                       = mapped_column(DateTime(timezone=True), nullable=False)

    lower_limit_ft: Mapped[Optional[int]]           = mapped_column(Integer)
    upper_limit_ft: Mapped[Optional[int]]           = mapped_column(Integer)


class Dem(Base):
    __tablename__ = "dem"

    id: Mapped[int]                 = mapped_column(BIGINT, primary_key=True)

    tile: Mapped[str]               = mapped_column(VARCHAR(16), nullable=False)
    rast: Mapped[RasterElement]     = mapped_column(Raster(spatial_index=False), nullable=False)


class Pilot(Base):
    __tablename__ = "pilot"

    id: Mapped[int]                                                     = mapped_column(BIGINT, primary_key=True)

    first_name: Mapped[str]                                             = mapped_column(VARCHAR(255), nullable=False)
    last_name: Mapped[str]                                              = mapped_column(VARCHAR(255), nullable=False)

    email: Mapped[str]                                                  = mapped_column(VARCHAR(255), nullable=False)
    normalized_email: Mapped[str]                                       = mapped_column(VARCHAR(255), nullable=False, unique=True)
    phone_number: Mapped[str]                                           = mapped_column(VARCHAR(15), nullable=False)
    pilot_number: Mapped[Optional[str]]                                 = mapped_column(VARCHAR(255))

    password_hash: Mapped[str]                                          = mapped_column(VARCHAR(255), nullable=False)

    show_to_public: Mapped[bool]                                        = mapped_column(Boolean, server_default="false", nullable=False)
    activity: Mapped[Optional[UserActivity]]                            = mapped_column(
        EnumWithUnknown(
            UserActivity,
            name="user_activity",
            unknown_value=UserActivity.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        )
    )
    flight_time: Mapped[int]                                            = mapped_column(INTEGER, server_default="0", nullable=False)
    dronepark_hash: Mapped[Optional[str]]                               = mapped_column(VARCHAR(255))

    created_at: Mapped[datetime]                                        = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    drone: Mapped[list['Drone']]                                        = relationship('Drone', back_populates='pilot')
    pilot_to_flying_privileges: Mapped[list['PilotToFlyingPrivileges']]   = relationship()
    verification_request: Mapped[list['VerificationRequest']]           = relationship('VerificationRequest', back_populates='pilot')
    mission: Mapped[list['Mission']]                                    = relationship('Mission', back_populates='pilot')
    checkin: Mapped[list['Checkin']]                                    = relationship('Checkin', back_populates='pilot')


class Drone(Base):
    __tablename__ = "drone"

    id: Mapped[int]                         = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                   = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)

    is_drone_modified: Mapped[bool]         = mapped_column(Boolean, server_default="false", nullable=False)
    category: Mapped[DroneCategory]         = mapped_column(
        EnumWithUnknown(
            DroneCategory,
            name="drone_category",
            unknown_value=DroneCategory.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )

    model_id: Mapped[int]                   = mapped_column(INTEGER, ForeignKey("model.id"), nullable=False)
    serial_number: Mapped[str]              = mapped_column(VARCHAR(255), nullable=False)

    flight_time: Mapped[int]                = mapped_column(INTEGER, server_default="0", nullable=False)
    mtom_override: Mapped[Optional[int]]    = mapped_column(Integer)

    model: Mapped['Model']                  = relationship()
    pilot: Mapped['Pilot']                  = relationship('Pilot', back_populates='drone')
    mission: Mapped[list['Mission']]        = relationship('Mission', back_populates='drone')
    checkin: Mapped[list['Checkin']]        = relationship()


class PilotToFlyingPrivileges(Base):
    __tablename__ = "pilot_to_flying_privileges"

    id: Mapped[int]                                 = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    pilot_id: Mapped[int]                           = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)
    flying_privilege: Mapped[FlyingPrivileges]      = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )


class VerificationRequest(Base):
    __tablename__ = "verification_request"

    id: Mapped[int]                                                             = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                                                       = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)

    status: Mapped[VerificationRequestStatus]                                   = mapped_column(
        EnumWithUnknown(
            VerificationRequestStatus,
            name="verification_request_status",
            unknown_value=VerificationRequestStatus.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        server_default="pending",
        nullable=False
    )
    reason: Mapped[Optional[str]]                                                = mapped_column(TEXT)
    verified_by: Mapped[Optional[int]]                                           = mapped_column(INTEGER, ForeignKey("afd_moderator.id"))
    verified_at: Mapped[Optional[datetime]]                                      = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime]                                                 = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pilot: Mapped['Pilot']                                                       = relationship('Pilot', back_populates='verification_request')
    afd_moderator: Mapped[Optional['AfdModerator']]                              = relationship()
    verification_document: Mapped[list['VerificationDocument']]                  = relationship()


class VerificationDocument(Base):
    __tablename__ = "verification_document"

    id: Mapped[int]                                                         = mapped_column(BIGINT, primary_key=True)
    request_id: Mapped[int]                                                 = mapped_column(BIGINT, ForeignKey("verification_request.id"), nullable=False)

    document_path: Mapped[str]                                              = mapped_column(VARCHAR(255), nullable=False)
    document_type: Mapped[VerificationDocumentType]                         = mapped_column(
        EnumWithUnknown(
            VerificationDocumentType,
            name="verification_document_type",
            unknown_value=VerificationDocumentType.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )

    created_at: Mapped[datetime]                                            = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Mission(Base):
    __tablename__ = "mission"

    id: Mapped[int]                                         = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                                   = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)
        
    drone_id: Mapped[int]                                   = mapped_column(BIGINT, ForeignKey("drone.id"), nullable=False)
    category: Mapped[OperationalCategory]                   = mapped_column(
        EnumWithUnknown(
            OperationalCategory,
            name="mission_category",
            unknown_value=OperationalCategory.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )
    flight_goal: Mapped[Optional[MissionFlightGoal]]        = mapped_column(
        EnumWithUnknown(
            MissionFlightGoal,
            name="mission_flight_goal",
            unknown_value=MissionFlightGoal.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        )
    )
    description: Mapped[Optional[str]]                      = mapped_column(TEXT)
    flying_privilege: Mapped[FlyingPrivileges]              = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )

    h3_index: Mapped[str]                                   = mapped_column(H3Index, server_default=FetchedValue(), nullable=False)
    country_id: Mapped[int]                                 = mapped_column(SMALLINT, ForeignKey("country.id"), nullable=False)
    home_point: Mapped[Point]                               = mapped_column(GeometryType(geometry_type="POINT", srid=4326), nullable=False)
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
            unknown_value=MissionStatus.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        server_default="created",
        nullable=False
    )

    created_at: Mapped[datetime]                            = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    country: Mapped['Country']                              = relationship()
    drone: Mapped['Drone']                                  = relationship('Drone', back_populates='mission')
    pilot: Mapped['Pilot']                                  = relationship('Pilot', back_populates='mission')


class Checkin(Base):
    __tablename__ = "checkin"

    id: Mapped[int]                             = mapped_column(BIGINT, primary_key=True)
    pilot_id: Mapped[int]                       = mapped_column(BIGINT, ForeignKey("pilot.id"), nullable=False)
    mission_id: Mapped[Optional[int]]           = mapped_column(BIGINT, ForeignKey("mission.id"))
    drone_id: Mapped[int]                       = mapped_column(BIGINT, ForeignKey("drone.id"), nullable=False)

    flying_privilege: Mapped[FlyingPrivileges] = mapped_column(
        EnumWithUnknown(
            FlyingPrivileges,
            name="flying_privileges",
            unknown_value=FlyingPrivileges.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )
    flight_goal: Mapped[Optional[MissionFlightGoal]] = mapped_column(
        EnumWithUnknown(
            MissionFlightGoal,
            name="mission_flight_goal",
            unknown_value=MissionFlightGoal.UNKNOWN,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        )
    )
    description: Mapped[Optional[str]]          = mapped_column(TEXT)

    home_point: Mapped[Point]                   = mapped_column(GeometryType(geometry_type="POINT", srid=4326), nullable=False)
    h3_index: Mapped[str]                       = mapped_column(H3Index, server_default=FetchedValue(), nullable=False)
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
           unknown_value=MissionStatus.UNKNOWN,
           values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        server_default="created",
        nullable=False
    )

    created_at: Mapped[datetime]                = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    country: Mapped['Country']                  = relationship()
    drone: Mapped['Drone']                      = relationship('Drone', back_populates='checkin')
    mission: Mapped[Optional['Mission']]        = relationship()
    pilot: Mapped['Pilot']                      = relationship('Pilot', back_populates='checkin')
    