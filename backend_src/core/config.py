from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


_DEBUG = os.getenv("DEBUG", "").strip().lower() in ("1", "true", "yes")


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw is None:
        return ["http://localhost:3000"] if _DEBUG else []

    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    # Browsers refuse a wildcard origin on credentialed requests (refresh cookie)
    if "*" in origins:
        raise ValueError("CORS_ORIGINS must list explicit origins, '*' is not allowed")

    return origins


def _cookie_samesite() -> str:
    value = os.getenv("MODERATOR_COOKIE_SAMESITE", "strict").strip().lower()
    if value not in ("strict", "lax", "none"):
        raise ValueError("MODERATOR_COOKIE_SAMESITE must be one of: strict, lax, none")

    return value

@dataclass(frozen=True)
class Settings:
    DEBUG                           = _DEBUG

    DATABASE_URL                    = os.getenv("DATABASE_URL")
    REDIS_URL                       = os.getenv("REDIS_URL")

    SECRET_KEY                      = os.getenv("SECRET_KEY")
    ALGORITHM                       = os.getenv("ALGORITHM", "")
    OTP_CODE                        = os.getenv("OTP_CODE")

    ACCESS_TOKEN_EXPIRE_MINUTES     = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0"))
    REFRESH_TOKEN_EXPIRE_DAYS       = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "0"))
    RESET_TOKEN_EXPIRE_MINUTES      = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "60"))
    VERIFY_TOKEN_EXPIRE_MINUTES     = int(os.getenv("VERIFY_TOKEN_EXPIRE_MINUTES", "60"))
    CHECKIN_TOKEN_EXPIRE_SECONDS    = int(os.getenv("CHECKIN_TOKEN_EXPIRE_SECONDS", "60"))
    VERIFICATION_TOKEN_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_MINUTES", "15"))

    ADMIN_API_KEY                   = os.getenv("ADMIN_API_KEY")

    MODERATOR_ACCESS_TOKEN_EXPIRE_MINUTES     = int(os.getenv("MODERATOR_ACCESS_TOKEN_EXPIRE_MINUTES", "10"))
    MODERATOR_REFRESH_TOKEN_EXPIRE_MINUTES    = int(os.getenv("MODERATOR_REFRESH_TOKEN_EXPIRE_MINUTES", "30"))
    MODERATOR_COOKIE_SAMESITE                 = _cookie_samesite()
    MODERATOR_COOKIE_SECURE                   = not _DEBUG

    PANSA_API_URL                  = os.getenv("PANSA_API_URL") or "https://api.dronemap.pansa.pl"
    PANSA_API_KEY                   = os.getenv("PANSA_API_KEY")
    PANSA_USER_AGENT                = os.getenv("PANSA_USER_AGENT") or "SkyDocker (university thesis project)"

    STORAGE_URL                     = os.getenv("STORAGE_URL")
    STORAGE_PUBLIC_URL              = os.getenv("STORAGE_PUBLIC_URL")
    STORAGE_APP_KEY                 = os.getenv("STORAGE_APP_KEY")
    STORAGE_APP_SECRET              = os.getenv("STORAGE_APP_SECRET")

    CORS_ORIGINS                    = _cors_origins()
