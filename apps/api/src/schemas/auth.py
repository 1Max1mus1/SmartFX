from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    plan: str = Field(default="free", pattern="^(free|pro)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserPayload(BaseModel):
    id: str
    email: EmailStr
    plan: str
    created_at: datetime


class AuthPayload(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPayload
