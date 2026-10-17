from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    DEBUG                           = os.getenv("DEBUG", "").strip().lower() in ("1", "true", "yes")

    DATABASE_URL                    = os.getenv("DATABASE_URL")
    REDIS_URL                       = os.getenv("REDIS_URL")

    SECRET_KEY                      = os.getenv("SECRET_KEY")
    ALGORITHM                       = os.getenv("ALGORITHM", "")
    OTP_CODE                        = os.getenv("OTP_CODE")

    ACCESS_TOKEN_EXPIRE_MINUTES     = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0"))
    REFRESH_TOKEN_EXPIRE_DAYS       = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "0"))
    RESET_TOKEN_EXPIRE_MINUTES      = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "60"))
    VERIFY_TOKEN_EXPIRE_MINUTES     = int(os.getenv("VERIFY_TOKEN_EXPIRE_MINUTES", "60"))

    ORIGINS                         = ["http://localhost:3000"]
