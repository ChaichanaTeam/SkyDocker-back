import json
from datetime import date, datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from pydantic import AliasPath, BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints, field_validator


def _blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _int_or_none(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


Name = Annotated[str, StringConstraints(strip_whitespace=True)]
Text = Annotated[Optional[str], BeforeValidator(_blank_to_none)]
Feet = Annotated[Optional[int], BeforeValidator(_int_or_none)]


class PansaModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class LocalizedText(PansaModel):
    pl: Text = None
    en: Text = None


class Zone(PansaModel):
    uid: UUID
    name: Name
    type: str
    min_ft: int = Field(validation_alias="min")
    max_ft: int = Field(validation_alias="max")
    modified: datetime
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    h24: bool = Field(False, validation_alias="acts")
    source: Text = None
    contact: Text = None
    description: Optional[LocalizedText] = None
    # parent zone, e.g. ATZ EPKP for ATZEPKP1KM
    master: Text = Field(None, validation_alias=AliasPath("etc", "master"))
    geometry: dict[str, Any] = Field(validation_alias="geojson")

    @field_validator("h24", mode="before")
    @classmethod
    def _h24(cls, acts: Any) -> bool:
        return bool(acts and acts.get("H24"))


class ZoneType(PansaModel):
    uid: UUID
    name: Name
    description: Optional[LocalizedText] = None

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, value: Any) -> Any:
        # this endpoint returns the {"pl": ..., "en": ...} object as a JSON string
        return json.loads(value) if isinstance(value, str) else value


class Activation(PansaModel):
    """Airspace reservation from the AUP/UUP."""

    id: int = Field(validation_alias="webcatid")
    designator: Name
    type: str
    min_ft: int = Field(validation_alias="min")
    max_ft: int = Field(validation_alias="max")
    start: datetime
    stop: datetime
    plan: Text = Field(None, validation_alias=AliasPath("etc", "upType"))
    plan_date: Optional[date] = Field(None, validation_alias=AliasPath("etc", "reservation", "aupDate"))
    geometry: Optional[dict[str, Any]] = Field(None, validation_alias=AliasPath("etc", "geometry"))

    @field_validator("geometry", mode="before")
    @classmethod
    def _geometry(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {"type": value.get("type"), "coordinates": value.get("coordinates")}
        return value


class TimeWindow(PansaModel):
    start: datetime
    stop: datetime


class HourSlot(PansaModel):
    # only the time of day is meaningful, the date part is arbitrary
    begin: datetime
    end: datetime


class NotamSchedule(PansaModel):
    """One rule of a NOTAM activity schedule (``etc.actDef``)."""

    period_mode: str = Field(validation_alias="periodMode")
    repeat_mode: Text = Field(None, validation_alias="repeatMode")
    slot_mode: Text = Field(None, validation_alias="slotMode")
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    # months and weekdays are numbered like JavaScript Date: January = 0, Sunday = 0
    months: list[int] = []
    days: list[int] = []
    weekdays: list[int] = []
    hour_slots: list[HourSlot] = Field([], validation_alias="hourSlots")


class Notam(PansaModel):
    uid: UUID
    series: str
    type: str
    zone_name: Optional[Name] = Field(None, validation_alias="zonename")
    starts_at: datetime = Field(validation_alias="b")
    ends_at: datetime = Field(validation_alias="c")
    schedule_text: Text = Field(None, validation_alias="d")
    text: Text = Field(None, validation_alias="e")
    lower_ft: Feet = Field(None, validation_alias="f")
    upper_ft: Feet = Field(None, validation_alias="g")
    active: bool
    modified: datetime
    # windows already expanded by PANSA, only for the next day or two
    activations: list[TimeWindow] = Field([], validation_alias="notamActivations")
    schedule: list[NotamSchedule] = Field([], validation_alias=AliasPath("etc", "actDef"))
