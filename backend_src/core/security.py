from __future__ import annotations
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Union, TypeVar, Self, overload
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError, field_validator

from .config import Settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"
    REGISTER = "register"
    CHECKIN = "checkin"
    VERIFICATION_REQUEST = "verification_request"


class TokenPayload(BaseModel):
    sub: str
    jti: str
    type:  TokenType
    iat: Union[int, datetime]
    exp: Union[int, datetime]
    gen: int = 0

    @classmethod
    def from_token_string(cls, token: str) -> Self:
        payload_dict = jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])
        return cls(**payload_dict)

    @field_validator("iat", "exp", mode="before")
    def validate_datetime(cls, time) -> int:
        if isinstance(time, datetime):
            return int(time.timestamp())
        return time


T = TypeVar("T", bound=TokenPayload)


class EmailTokenPayload(TokenPayload):
    email: str


class IssuedToken(BaseModel):
    token: str
    jti: str
    expires_at: datetime

    @classmethod
    def from_payload(cls, payload: TokenPayload) -> IssuedToken:
        return cls(
            token=jwt.encode(payload.model_dump(), Settings.SECRET_KEY, algorithm=Settings.ALGORITHM),
            jti=payload.jti,
            expires_at=datetime.fromtimestamp(payload.exp, tz=timezone.utc) # type: ignore
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def dummy_verify_password() -> bool:
    return pwd_context.dummy_verify()


def _create_token(subject: str, expires_delta: timedelta, token_type: TokenType, payload_cls: type[TokenPayload] = TokenPayload, **claims) -> IssuedToken:
    now = datetime.now(timezone.utc)
    jti = uuid4().hex
    exp = now + expires_delta

    payload = payload_cls(
        sub=subject,
        jti=jti,
        type=token_type,
        iat=now,
        exp=exp,
        **claims
    )
    
    return IssuedToken.from_payload(payload)


def create_access_token(subject: str, gen: int) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.ACCESS,
        gen=gen,
    )


def create_refresh_token(subject: str, gen: int) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=Settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TokenType.REFRESH,
        gen=gen,
    )


def create_reset_token(subject: str, gen: int) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.RESET_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.RESET,
        gen=gen,
    )


def create_verify_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.VERIFY,
    )


def create_register_verify_token(normalized: str, original: str) -> IssuedToken:
    return _create_token(
        subject=normalized,
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.VERIFY,
        payload_cls=EmailTokenPayload,
        email=original
    )


def create_register_token(normalized: str, original: str) -> IssuedToken:
    return _create_token(
        subject=normalized,
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.REGISTER,
        payload_cls=EmailTokenPayload,
        email=original
    )


def create_checkin_token(pilot_id: str, payload_cls: type[TokenPayload], **claims) -> IssuedToken:
    return _create_token(
        subject=pilot_id,
        expires_delta=timedelta(seconds=Settings.CHECKIN_TOKEN_EXPIRE_SECONDS),
        token_type=TokenType.CHECKIN,
        payload_cls=payload_cls,
        **claims
    )


def create_verification_token(pilot_id: str, payload_cls: type[TokenPayload], **claims) -> IssuedToken:
    return _create_token(
        subject=pilot_id,
        expires_delta=timedelta(minutes=Settings.VERIFICATION_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.VERIFICATION_REQUEST,
        payload_cls=payload_cls,
        **claims
    )


@overload
def decode_token(token: str) -> Optional[TokenPayload]: ...

@overload
def decode_token(token: str, payload_cls: type[T] = TokenPayload) -> Optional[T]: ...

def decode_token(token: str, payload_cls: type[T] = TokenPayload) -> Optional[TokenPayload]:
    try:
        return payload_cls.from_token_string(token)

    except (jwt.PyJWTError, ValidationError):
        return None
