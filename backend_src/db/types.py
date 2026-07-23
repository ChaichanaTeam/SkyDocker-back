from sqlalchemy import Enum as SQLEnum, cast
from sqlalchemy.types import UserDefinedType
from typing import Any


class EnumWithUnknown(SQLEnum):
    def __init__(self, *enums, **kw: dict[str, Any]):
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