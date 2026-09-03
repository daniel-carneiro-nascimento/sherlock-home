from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    detail: str


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100,
    )
    password: str = Field(
        min_length=1,
        max_length=1024,
    )


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=1024,
    )
    new_password: str = Field(
        min_length=12,
        max_length=1024,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    username: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    user: UserResponse
    expires_at: datetime
