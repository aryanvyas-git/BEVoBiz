from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


class SignupRequest(BaseModel):
    business_name: str = Field(max_length=200)
    email: EmailStr
    password: str = Field(max_length=128)

    @field_validator("business_name")
    @classmethod
    def business_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("business_name must not be blank")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BusinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    business_id: int
    created_at: datetime


class MeResponse(BaseModel):
    user: UserResponse
    business: BusinessResponse
