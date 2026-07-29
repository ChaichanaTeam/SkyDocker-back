import os

class Settings:
    DATABASE_URL                = os.getenv("DATABASE_URL")
    SECRET_KEY                  = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")