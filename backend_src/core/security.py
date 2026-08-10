from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4
import jwt
from passlib.context import CryptContext

from .config import Settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"


@dataclass(frozen=True)
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _create_token(subject: str, expires_delta: timedelta, token_type: TokenType) -> IssuedToken:
    now = datetime.now(timezone.utc)
    jti = uuid4().hex
    exp = now + expires_delta

    payload = {
        "sub": subject,
        "jti": jti,
        "type": token_type.value,
        "iat": now,
        "exp": exp,
    }
    
    token = jwt.encode(payload, Settings.SECRET_KEY, algorithm=Settings.ALGORITHM)
    return IssuedToken(token=token, jti=jti, expires_at=exp)


def create_access_token(pilot_id: int) -> IssuedToken:
    return _create_token(
        subject=str(pilot_id),
        expires_delta=timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.ACCESS,
    )


def create_refresh_token(pilot_id: int) -> IssuedToken:
    return _create_token(
        subject=str(pilot_id),
        expires_delta=timedelta(days=Settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=TokenType.REFRESH,
    )


def create_reset_token(pilot_id: int) -> IssuedToken:
    return _create_token(
        subject=str(pilot_id),
        expires_delta=timedelta(minutes=Settings.RESET_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.RESET,
    )


def create_verify_token(pilot_id: int) -> IssuedToken:
    return _create_token(
        subject=str(pilot_id),
        expires_delta=timedelta(minutes=Settings.VERIFY_TOKEN_EXPIRE_MINUTES),
        token_type=TokenType.VERIFY,
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
