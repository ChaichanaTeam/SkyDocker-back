from typing import Annotated, Any, Literal, Optional
from pydantic import BaseModel, SerializeAsAny, model_validator, EmailStr, AfterValidator
from pydantic_extra_types.phone_numbers import PhoneNumber


class E164PhoneNumber(PhoneNumber):
    phone_format = "E164"


_GMAIL = {"gmail.com", "googlemail.com"}
_PLUS_ONLY = {
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "fastmail.com", "proton.me", "protonmail.com",
}


def _strip_tag(name: str) -> str:
    name = name.split('+')[0]
    if len(name) == 0:
        raise ValueError("Name is empty")
    return name


def normalize_email(email: EmailStr) -> EmailStr:
    name, domain = email.lower().split('@')

    if domain in _GMAIL:
        return f"{_strip_tag(name).replace('.', '')}@gmail.com"
    elif domain in _PLUS_ONLY:
        return f"{_strip_tag(name)}@{domain}"

    return f"{name}@{domain}"


NormalizedEmailStr = Annotated[EmailStr, AfterValidator(normalize_email)]


class BoundingBox(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def unpack(self) -> tuple[float, float, float, float]:
        return self.min_lon, self.min_lat, self.max_lon, self.max_lat

    @model_validator(mode="after")
    def validate_box(self):
        result = (
            self.min_lon < self.max_lon and
            self.min_lat < self.max_lat
        )

        if not result:
            raise ValueError("Incorrect order of coordinate values")
        return self


class Coordinate(BaseModel):
    lon: float
    lat: float

    @model_validator(mode="after")
    def validate_position(self):
        x1, y1 = -9.5, 36.0
        x2, y2 = 31.5833, 70.0833

        result = (
            x1 < self.lon < x2 and
            y1 < self.lat < y2
        )

        if not result:
            raise ValueError("Position is not in supported region")
        return self


class FeatureProperties(BaseModel):
    pass


class GeoFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: Optional[SerializeAsAny[FeatureProperties]]


class GeoJson(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoFeature]
    