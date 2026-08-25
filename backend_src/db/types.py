from geoalchemy2 import Geometry, WKBElement
from shapely import wkb
from sqlalchemy import Enum as SQLEnum, cast
from sqlalchemy.types import UserDefinedType, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect
from typing import Any, Optional
from shapely.geometry import Polygon as ShapelyPolygon


class EnumWithUnknown(SQLEnum):
    def __init__(self, *enums, **kw):
        super().__init__(*enums, **kw)
        # SQLAlchemy sets the _adapted_from keyword argument sometimes, which contains a reference to the original type - but won't include
        # original keyword arguments, so we need to handle that here.
        self._unknown_value = kw["_adapted_from"]._unknown_value if "_adapted_from" in kw else kw.get("unknown_value",None)
        if self._unknown_value is None:
            raise ValueError("unknown_value should be a member of the enum")
    
    # This is the function which resolves the object for the DB value
    def _object_value_for_elem(self, elem: str):
        try:
            return self._object_lookup[elem]
        except LookupError:
            return self._unknown_value


class H3Index(UserDefinedType):
    def get_col_spec(self, **kw: dict[str, Any]):
        return "h3index"

    def bind_expression(self, bindvalue):
        return cast(bindvalue, self)


class GeometryType(TypeDecorator):
    def __init__(self, geometry_type: str, srid: int):
        self.impl = Geometry(geometry_type=geometry_type, srid=srid)
        self.srid = srid

    cache_ok = True

    def process_bind_param(self, value: Optional[ShapelyPolygon], dialect: Dialect) -> Optional[WKBElement]:
        if value is not None:
            return WKBElement(value.wkb, self.srid)
        return value

    def process_result_value(self, value: Optional[WKBElement], dialect: Dialect) -> Optional[Any]:
        if value is not None:
            data = value.data if isinstance(value, WKBElement) else value
            return wkb.loads(data)
        return value