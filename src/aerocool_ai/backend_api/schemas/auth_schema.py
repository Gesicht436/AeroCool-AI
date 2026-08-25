"""Pydantic v2 Schemas for User Authentication and Account Profiles."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserLoginRequest(BaseModel):
    """Payload for credentials authentication."""

    model_config = ConfigDict(extra="ignore")

    email: str = Field(..., description="User account email address", examples=["admin@aerocool.ai"])
    password: str = Field(..., description="Plain-text password", examples=["Admin@123"])


class UserRegisterRequest(BaseModel):
    """Payload for user self-registration."""

    model_config = ConfigDict(extra="ignore")

    email: str = Field(..., description="Valid email address", examples=["planner.mumbai@gov.in"])
    password: str = Field(..., min_length=6, description="Account password (min 6 chars)")
    full_name: str = Field(..., min_length=2, description="User full name", examples=["Dr. Priya Sharma"])
    role: Optional[str] = Field(
        default="customer",
        description="Role designation ('customer' or 'admin')",
        examples=["customer"],
    )
    organization: Optional[str] = Field(
        default=None,
        description="Municipal corporation or university affiliation",
        examples=["Brihanmumbai Municipal Corporation"],
    )


class UserProfileResponse(BaseModel):
    """Public user profile attributes."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    organization: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class TokenResponse(BaseModel):
    """Signed JWT token and user profile payload."""

    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class UserListResponse(BaseModel):
    """Admin directory listing of user accounts."""

    users: List[UserProfileResponse]
    total: int
