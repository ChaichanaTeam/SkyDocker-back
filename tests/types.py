from typing import Callable, Literal, Optional, TypedDict
from httpx import URL


EndpointCreator = Callable[[Literal["live"] | Literal["demo"], str], URL]


class UserInfo(TypedDict):
    email: str
    phone_number: str
    first_name: str
    last_name: str
    password: str

    tokens: "TokenContainer"


class PilotInfo(UserInfo):
    drone_id: Optional[int]
    checkin_token: Optional[str]
    checkin_id: Optional[int]


class TokenContainer(TypedDict):
    type: Literal["Bearer"]
    verify_token: Optional[str]
    register_token: Optional[str]
    reset_token: Optional[str]
    
    access_token: Optional[str]
    refresh_token: Optional[str]