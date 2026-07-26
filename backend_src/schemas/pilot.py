from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional

class PilotLogin(BaseModel):
    email: EmailStr
    password: str


class PilotRegister(BaseModel):
    email: EmailStr
    phone_number: str = Field(min_length=1, max_length=15)

    password: str = Field(min_length=8)
    password_confirm: str

    pilot_number: Optional[str] = None

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Password do not match")
        return self


class PilotVerifyCode(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)