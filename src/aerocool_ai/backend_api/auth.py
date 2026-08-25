"""Authentication, Password Hashing, and JWT Utilities."""

from __future__ import annotations

import datetime
import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, Optional

import jwt

from aerocool_ai.config import get_settings

logger = logging.getLogger(__name__)

# Fallback Secret Key if not specified in config
DEFAULT_SECRET_KEY = "aerocool-ai-super-secret-jwt-signing-key-production-grade"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify raw password against stored salt$hash string."""
    try:
        if "$" not in hashed_password:
            return False
        salt, stored_hash = hashed_password.split("$", 1)
        computed_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000
        )
        return hmac.compare_digest(computed_key.hex(), stored_hash)
    except Exception as exc:
        logger.warning(f"Password verification error: {exc}")
        return False


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Generate signed JWT access token."""
    settings = get_settings()
    secret_key = settings.secret_key or DEFAULT_SECRET_KEY

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.datetime.now(datetime.timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token."""
    settings = get_settings()
    secret_key = settings.secret_key or DEFAULT_SECRET_KEY

    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Access token has expired.")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid access token: {exc}")
