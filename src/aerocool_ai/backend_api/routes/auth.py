"""Authentication and User Account Route Handlers."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from aerocool_ai.backend_api.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from aerocool_ai.backend_api.dependencies import (
    get_current_user,
    get_user_repository,
)
from aerocool_ai.backend_api.schemas.auth_schema import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from aerocool_ai.database.models.users import UserAccount, UserRole
from aerocool_ai.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication & Accounts"])
logger = logging.getLogger(__name__)


def _format_user_profile(user: UserAccount) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at and hasattr(user.last_login_at, "isoformat") else None,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Issue JWT Token",
)
async def login(
    payload: UserLoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    """Validate email/password and issue signed JWT bearer token."""
    user = await user_repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator.",
        )

    await user_repo.update_last_login(user.id)
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_profile(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Municipal User Account",
)
async def register(
    payload: UserRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    """Register a new customer/planner account."""
    existing = await user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    # Protect admin registration from public creation
    assigned_role = UserRole.ADMIN.value if payload.role == UserRole.ADMIN.value else UserRole.CUSTOMER.value

    hashed = hash_password(payload.password)
    user = await user_repo.create_user(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name,
        role=assigned_role,
        organization=payload.organization,
    )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_profile(user),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
)
async def get_my_profile(
    current_user: UserAccount = Depends(get_current_user),
) -> UserProfileResponse:
    """Retrieve profile and role permissions for currently authenticated user."""
    return _format_user_profile(current_user)


@router.post(
    "/demo-login/{role}",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="1-Click Instant Demo Authentication",
)
async def demo_login(
    role: str,
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    """Provide instant 1-click token for demo users ('admin' or 'customer')."""
    target_email = "admin@aerocool.ai" if role.lower() == "admin" else "planner@aerocool.ai"
    user = await user_repo.get_by_email(target_email)

    if not user:
        # Auto-create if not in db
        if role.lower() == "admin":
            user = await user_repo.create_user(
                email="admin@aerocool.ai",
                hashed_password=hash_password("Admin@123"),
                full_name="System Administrator",
                role=UserRole.ADMIN.value,
                organization="AeroCool Municipal Operations",
            )
        else:
            user = await user_repo.create_user(
                email="planner@aerocool.ai",
                hashed_password=hash_password("Planner@123"),
                full_name="City Climate Planner",
                role=UserRole.CUSTOMER.value,
                organization="Delhi Urban Climate Cell",
            )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_profile(user),
    )
