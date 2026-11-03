import re
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        missing = []

        if len(value) < 8:
            missing.append("at least 8 characters")

        if not re.search(r"[A-Z]", value):
            missing.append("an uppercase letter")

        if not re.search(r"[a-z]", value):
            missing.append("a lowercase letter")

        if not re.search(r"[0-9]", value):
            missing.append("a number")

        if not re.search(r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]", value):
            missing.append("a special character")

        if missing:
            raise ValueError(
                "Password must contain " + ", ".join(missing) + "."
            )

        return value


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class AuthSessionResponse(BaseModel):
    user: UserResponse
    expires_at: int #expiration istant expressed in seconds