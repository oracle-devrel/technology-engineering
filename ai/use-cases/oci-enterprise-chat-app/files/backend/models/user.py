"""Pydantic models for user authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model."""

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username for login")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_admin: bool = Field(default=False, description="Whether user can administer identity settings")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation timestamp"
    )

    class Config:
        """Pydantic model configuration."""
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserInDB(User):
    """User model with hashed password for database storage."""

    hashed_password: str = Field(..., description="Hashed password")


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response with session token."""

    token: str = Field(..., description="Session token")
    user: User = Field(..., description="User information")
    message: str = Field(default="Login successful")


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile fields."""

    full_name: Optional[str] = Field(default=None, description="Updated full name")
    email: Optional[str] = Field(default=None, description="Updated email address")


class PasswordChangeRequest(BaseModel):
    """Request to change user password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")


class SessionData(BaseModel):
    """Session data stored on server."""

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Session creation timestamp"
    )
    expires_at: Optional[datetime] = Field(default=None, description="Session expiration")
