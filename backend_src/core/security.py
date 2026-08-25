from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Union
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator

from .config import Settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"
    REGISTER = "register"


class TokenPayload(BaseModel):
    sub: str
    jti: str
    type:  TokenType
    iat: Union[int, datetime]
    exp: Union[int, datetime]

    @classmethod
    def from_token_string(cls, token: str) -> TokenPayload:
        payload_dict = jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])
        return cls(**payload_dict)

    @field_validator("iat", "exp", mode="before")
    def validate_datetime(cls, time) -> int:
        if isinstance(time, datetime):
            return int(time.timestamp())
        return time


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


def _create_token(subject: str, expires_delta: timedelta, token_type: TokenType) -> IssuedToken:
    now = datetime.now(timezone.utc)
    jti = uuid4().hex
    exp = now + expires_delta

    payload = TokenPayload(
        sub=subject,
        jti=jti,
        type=token_type,
        iat=now,
        exp=exp,
    )
    
    return IssuedToken.from_payload(payload)


def create_access_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.ACCESS,
    )


def create_refresh_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=Settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TokenType.REFRESH,
    )


def create_reset_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.RESET_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.RESET,
    )


def create_verify_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.VERIFY,
    )


def create_register_token(subject: str) -> IssuedToken:
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.REGISTER,
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        return TokenPayload.from_token_string(token)

    except jwt.PyJWTError:
        return None
